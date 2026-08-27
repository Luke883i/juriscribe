"""Portable fail-closed scientific recovery bundles for Juriscribe 1.0.

Recovery is MATERIALIZATION_ONLY. The ZIP proves snapshot integrity/replayability,
not legal/scientific truth or authenticity against a fully rewriting adversary.
"""
from __future__ import annotations

import copy, hashlib, io, json, os, posixpath, stat, zipfile, zlib
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from . import __version__ as RUNTIME_VERSION
from .continuity import canonical_digest, checkpoint_id, material_index, project_iteration, validate_iteration_projection, validate_material_archive

SCHEMA="juriscribe-recovery-bundle/v1"
AUTHORITY="MATERIALIZATION_ONLY"
CLAIM_SCOPE="SNAPSHOT_INTEGRITY_AND_REPLAYABILITY_NOT_AUTHENTICITY_OR_LEGAL_OR_SCIENTIFIC_TRUTH"
MANIFEST_PATH="manifest.json"; STATE_PATH="snapshot/state.json"; ITERATION_PATH="snapshot/iteration.json"; MATERIAL_INDEX_PATH="snapshot/material-index.json"; README_PATH="README.md"
MAX_FILES=4096; MAX_SINGLE_FILE_BYTES=256*1024*1024; MAX_UNCOMPRESSED_BYTES=1024*1024*1024; MAX_COMPRESSION_RATIO=250.0


def _utc_now(): return datetime.now(timezone.utc).isoformat()
def _sha(data:bytes): return hashlib.sha256(data).hexdigest()
def _json(value): return (json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode()
def _state(state):
    if isinstance(state,dict): return copy.deepcopy(state)
    if is_dataclass(state): return asdict(state)
    return copy.deepcopy(dict(getattr(state,"__dict__",{})))
def _semver(value):
    core=str(value or "").split("+",1)[0].split("-",1)[0]; parts=core.split(".")
    if len(parts)!=3 or any(not p.isdigit() for p in parts): raise ValueError("invalid Juriscribe runtime version")
    return tuple(map(int,parts))
def _runtime_compatible(source,current=RUNTIME_VERSION):
    a,b=_semver(source),_semver(current); return a[0]==b[0] and a<=b


def _safe(name:str)->bool:
    if not name or "\\" in name or name.startswith("/"): return False
    p=PurePosixPath(name)
    return not p.is_absolute() and all(x not in {"",".",".."} for x in p.parts) and posixpath.normpath(name)==name


def _write(z:zipfile.ZipFile,name:str,data:bytes):
    if not _safe(name) or len(data)>MAX_SINGLE_FILE_BYTES: raise ValueError("unsafe or oversized recovery member")
    method=zipfile.ZIP_DEFLATED
    if len(data)>=256*1024:
        probe=zlib.compress(data,1)
        if probe and len(data)/len(probe)>MAX_COMPRESSION_RATIO*.40: method=zipfile.ZIP_STORED
    i=zipfile.ZipInfo(name,(1980,1,1,0,0,0)); i.compress_type=method; i.external_attr=(0o100600&0xffff)<<16; z.writestr(i,data)


def _workspace_files(root:Path|None):
    if not root or not root.exists(): return []
    root=root.resolve(); out=[]
    candidates=[]
    if (root/"session.integrity.json").exists(): candidates.append(root/"session.integrity.json")
    for d in ("artifacts","ledger"):
        base=root/d
        if base.exists(): candidates.extend(p for p in sorted(base.rglob("*")) if p.is_file() or p.is_symlink())
    for p in candidates:
        if p.is_symlink(): raise ValueError(f"recovery export rejects symlink: {p}")
        resolved=p.resolve(); rel=resolved.relative_to(root); out.append(("workspace/"+rel.as_posix(),resolved))
    return out


def _readme(iteration,session_id):
    w=iteration.get("where") or {}; n=iteration.get("next") or {}; d=iteration.get("done") or {}
    return f"""# Juriscribe recovery bundle\n\nScientific session snapshot; not a legal correctness certificate.\n\nSession: {session_id}\nCheckpoint: {iteration.get('checkpoint_id','')}\nMode: {w.get('mode') or '-'}\nPhase: {w.get('phase') or '-'}\nStage: {w.get('stage') or '-'}\n\nDone: {d.get('summary') or '-'}\nNext: {n.get('summary') or '-'}\nHow: {n.get('how') or '-'}\n\nResume: validate manifest and hashes; validate runtime-input archive; validate human admission; perform a fresh host probe; restore state; rebind host paths only; regenerate host-bound materialization; continue from the projected next gate. Never reuse the old probe as current authority.\n\nThis bundle can contain confidential user material.\n"""


def _payloads(state,workspace_base=None,require_resumable=True):
    s=_state(state)
    if not s.get("session_id"): raise ValueError("recovery snapshot requires session_id")
    ok,errors=validate_material_archive(s)
    if require_resumable and s.get("corpus") and not ok: raise ValueError("recovery snapshot is not losslessly resumable: "+"; ".join(errors))
    iteration=project_iteration(s)
    if require_resumable and not (iteration.get("recovery") or {}).get("resume_ready"): raise ValueError("recovery snapshot is not resume-ready")
    payload={STATE_PATH:_json(s),ITERATION_PATH:_json(iteration),MATERIAL_INDEX_PATH:_json(material_index(s)),README_PATH:_readme(iteration,str(s["session_id"])).encode()}
    raw=str(workspace_base if workspace_base is not None else (s.get("runtime") or {}).get("workspace_base") or "").strip(); root=Path(raw).resolve() if raw and Path(raw).exists() else None
    workspace=[]; total=sum(map(len,payload.values()))
    for name,path in _workspace_files(root):
        data=path.read_bytes(); total+=len(data)
        if total>MAX_UNCOMPRESSED_BYTES: raise ValueError("recovery bundle exceeds total uncompressed size limit")
        payload[name]=data; workspace.append({"bundle_path":name,"workspace_relative_path":name.removeprefix("workspace/"),"sha256":_sha(data),"size":len(data)})
    entries=[{"path":n,"sha256":_sha(v),"size":len(v)} for n,v in sorted(payload.items())]
    manifest={"schema":SCHEMA,"authority":AUTHORITY,"bundle_id":"JRB-"+iteration["checkpoint_id"][3:19],"created_at":_utc_now(),"source_session_id":str(s["session_id"]),"checkpoint_id":iteration["checkpoint_id"],"runtime_version":RUNTIME_VERSION,"runtime_compatibility":{"major":_semver(RUNTIME_VERSION)[0],"resume_direction":"SOURCE_LE_CURRENT_SAME_MAJOR"},"state_sha256":_sha(payload[STATE_PATH]),"state_canonical_digest":canonical_digest(s),"iteration_digest":iteration.get("digest"),"material_archive_status":"PASS" if ok else "PARTIAL","material_archive_errors":errors,"material_count":len(material_index(s)),"fresh_host_probe_required_on_resume":True,"contract_sha256":str((s.get("runtime") or {}).get("contract_sha256") or (s.get("admission") or {}).get("receipt",{}).get("contract_sha256") or ""),"source_revision":str((s.get("runtime") or {}).get("source_revision") or ""),"workspace_members":workspace,"entries":entries,"entry_count":len(entries),"confidentiality":"CONTAINS_SESSION_AND_USER_MATERIAL","claim_scope":CLAIM_SCOPE}
    manifest["manifest_digest"]=canonical_digest({k:v for k,v in manifest.items() if k!="manifest_digest"})
    return payload,manifest


def create_recovery_bundle_bytes(state,*,workspace_base=None,require_resumable=True):
    payload,manifest=_payloads(state,workspace_base,require_resumable); out=io.BytesIO()
    with zipfile.ZipFile(out,"w") as z:
        _write(z,MANIFEST_PATH,_json(manifest))
        for name,data in sorted(payload.items()): _write(z,name,data)
    data=out.getvalue(); report=inspect_recovery_bundle(data)
    if report["status"]!="PASS": raise ValueError("generated recovery bundle failed readback: "+"; ".join(report["errors"]))
    return data


def create_recovery_bundle(state,path,*,workspace_base=None,require_resumable=True):
    out=Path(path); out.parent.mkdir(parents=True,exist_ok=True); data=create_recovery_bundle_bytes(state,workspace_base=workspace_base,require_resumable=require_resumable); tmp=out.with_name("."+out.name+".tmp"); tmp.write_bytes(data); os.replace(tmp,out); return out


def _open(bundle): return zipfile.ZipFile(io.BytesIO(bundle) if isinstance(bundle,bytes) else bundle)


def inspect_recovery_bundle(bundle):
    errors=[]; manifest={}; state={}; iteration={}
    try:
        with _open(bundle) as z:
            infos=z.infolist(); names=[i.filename for i in infos]
            if len(infos)>MAX_FILES: errors.append("recovery bundle file count exceeds limit")
            if len(names)!=len(set(names)): errors.append("recovery bundle contains duplicate member names")
            total=0
            for i in infos:
                total+=i.file_size
                if not _safe(i.filename): errors.append(f"unsafe recovery bundle member: {i.filename}")
                mode=(i.external_attr>>16)&0xffff
                if stat.S_ISLNK(mode): errors.append(f"recovery bundle symlink forbidden: {i.filename}")
                if i.file_size>MAX_SINGLE_FILE_BYTES: errors.append(f"recovery bundle member too large: {i.filename}")
                if i.compress_size and i.file_size/max(1,i.compress_size)>MAX_COMPRESSION_RATIO: errors.append(f"recovery compression ratio unsafe: {i.filename}")
            if total>MAX_UNCOMPRESSED_BYTES: errors.append("recovery bundle uncompressed size exceeds limit")
            if MANIFEST_PATH not in names: errors.append("recovery manifest missing"); return {"status":"FAIL","errors":errors,"manifest":{},"state":{},"iteration":{}}
            manifest=json.loads(z.read(MANIFEST_PATH).decode())
            if manifest.get("schema")!=SCHEMA or manifest.get("authority")!=AUTHORITY: errors.append("recovery manifest schema/authority mismatch")
            if manifest.get("manifest_digest")!=canonical_digest({k:v for k,v in manifest.items() if k!="manifest_digest"}): errors.append("recovery manifest digest mismatch")
            if manifest.get("fresh_host_probe_required_on_resume") is not True: errors.append("fresh host probe policy missing")
            if not _runtime_compatible(str(manifest.get("runtime_version") or "")): errors.append("recovery runtime version incompatible")
            compat=manifest.get("runtime_compatibility") or {}
            if compat.get("major")!=_semver(RUNTIME_VERSION)[0] or compat.get("resume_direction")!="SOURCE_LE_CURRENT_SAME_MAJOR": errors.append("recovery runtime compatibility policy mismatch")
            entries=manifest.get("entries") or []; paths=[str(x.get("path") or "") for x in entries]
            if len(paths)!=len(set(paths)) or int(manifest.get("entry_count",-1))!=len(entries): errors.append("recovery manifest entry identity/count mismatch")
            expected={MANIFEST_PATH,*paths}; actual=set(names)
            if actual!=expected: errors.append("recovery bundle members differ from manifest")
            for e in entries:
                name=str(e.get("path") or "")
                if name not in actual: continue
                data=z.read(name)
                if len(data)!=int(e.get("size",-1)) or _sha(data)!=e.get("sha256"): errors.append(f"recovery member digest/size mismatch: {name}")
            if STATE_PATH in actual:
                raw=z.read(STATE_PATH); state=json.loads(raw.decode())
                if manifest.get("state_sha256")!=_sha(raw) or manifest.get("state_canonical_digest")!=canonical_digest(state): errors.append("recovery state binding mismatch")
                if checkpoint_id(state)!=manifest.get("checkpoint_id"): errors.append("recovery manifest checkpoint does not match state")
            if MATERIAL_INDEX_PATH in actual and state:
                stored=json.loads(z.read(MATERIAL_INDEX_PATH).decode()); expected_index=material_index(state)
                if stored!=expected_index: errors.append("recovery material index is stale or inconsistent")
                ok,archive_errors=validate_material_archive(state)
                if manifest.get("material_archive_status")!=("PASS" if ok else "PARTIAL") or int(manifest.get("material_count",-1))!=len(expected_index): errors.append("recovery material archive manifest mismatch")
                errors.extend([] if ok else archive_errors)
            if ITERATION_PATH in actual and state:
                iteration=json.loads(z.read(ITERATION_PATH).decode()); ok,projection_errors=validate_iteration_projection(state,iteration)
                if not ok: errors.extend(projection_errors)
                if manifest.get("iteration_digest")!=iteration.get("digest") or manifest.get("checkpoint_id")!=iteration.get("checkpoint_id"): errors.append("recovery iteration/checkpoint binding mismatch")
    except (OSError,zipfile.BadZipFile,KeyError,ValueError,TypeError,UnicodeError,json.JSONDecodeError,OverflowError) as exc: errors.append(f"recovery bundle read failed: {type(exc).__name__}: {exc}")
    return {"status":"PASS" if not errors else "FAIL","errors":list(dict.fromkeys(errors)),"manifest":manifest,"state":state,"iteration":iteration}


def validate_recovery_bundle(bundle):
    r=inspect_recovery_bundle(bundle); return r["status"]=="PASS",list(r["errors"])


def extract_recovery_workspace(bundle,target):
    r=inspect_recovery_bundle(bundle)
    if r["status"]!="PASS": raise ValueError("invalid recovery bundle: "+"; ".join(r["errors"]))
    target=Path(target).resolve(); target.mkdir(parents=True,exist_ok=True)
    with _open(bundle) as z:
        for item in r["manifest"].get("workspace_members") or []:
            name,rel=str(item.get("bundle_path") or ""),str(item.get("workspace_relative_path") or "")
            if not _safe(name) or not _safe(rel): raise ValueError("unsafe workspace path in recovery manifest")
            dest=(target/rel).resolve(); dest.relative_to(target); dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists(): raise FileExistsError(f"recovery extraction refuses to overwrite existing file: {dest}")
            dest.write_bytes(z.read(name))
    return target


def resume_recovery_bundle(bundle,root,*,host_capabilities,host,contract_text=None,runtime_revision=None):
    r=inspect_recovery_bundle(bundle)
    if r["status"]!="PASS": raise ValueError("invalid recovery bundle: "+"; ".join(r["errors"]))
    from .admission import load_contract_text,require_receipt
    from .bootstrap import claim_probe_receipt,issue_probe_receipt,require_probe_receipt
    from .dashboard_persistence import persist_dashboard_generation
    from .session import SessionState,Workspace
    data=copy.deepcopy(r["state"]); cp=str(r["manifest"].get("checkpoint_id") or ""); contract_text=contract_text or load_contract_text(); admission=data.get("admission") or {}; receipt=require_receipt(admission.get("receipt"),contract_text); probe=issue_probe_receipt(receipt,contract_text,dict(host_capabilities),host=str(host)); require_probe_receipt(probe,receipt,contract_text)
    session_id=str(data.get("session_id") or "").strip(); ws=Workspace(Path(root),session_id); ws.assert_initializable(); claim_probe_receipt(root,probe,session_id); extract_recovery_workspace(bundle,ws.base)
    old=str((data.get("runtime") or {}).get("workspace_base") or ""); old_root=Path(old).resolve(strict=False) if old else None; restored={str(x.get("workspace_relative_path") or "") for x in r["manifest"].get("workspace_members") or []}; stale=False
    for a in data.get("artifacts") or []:
        raw=str(a.get("path") or "")
        if not raw or not old_root: a["readback"]="STALE_RECOVERY"; a["materialization_stale"]=True; stale=True; continue
        p=Path(raw); candidate=p if p.is_absolute() else old_root/p
        try: rel=candidate.resolve(strict=False).relative_to(old_root)
        except ValueError: a["readback"]="STALE_RECOVERY"; a["materialization_stale"]=True; stale=True; continue
        a["path"]=str((ws.base/rel).resolve(strict=False))
        if rel.as_posix() not in restored: a["readback"]="STALE_RECOVERY"; a["materialization_stale"]=True; stale=True
    runtime=dict(data.get("runtime") or {}); source_rev=str(r["manifest"].get("source_revision") or "")
    if runtime_revision is not None and source_rev and str(runtime_revision)!=source_rev: raise PermissionError("recovery runtime revision mismatch")
    runtime.pop("source_revision",None); runtime.update({"host":str(host),"capabilities":dict(host_capabilities),"workspace_base":str(ws.base.resolve()),"storage_backend":"FILESYSTEM","recovered_from_checkpoint":cp,"recovery_source_revision":source_rev}); data["runtime"]=runtime; admission["probe_receipt"]=probe; data["admission"]=admission
    continuity=data.setdefault("strategy",{}).setdefault("continuity",{}); continuity.setdefault("recovery_lineage",[]).append({"source_session_id":str(r["manifest"].get("source_session_id") or ""),"source_checkpoint_id":cp,"resumed_at":_utc_now(),"fresh_probe_receipt_id":str(probe.get("receipt_id") or "")})
    if stale: data["completion"]={**(data.get("completion") or {}),"eligible":False,"reason":"host-bound materialization must be regenerated after recovery"}; data["phase"]="VALIDATING"
    state=SessionState(**data)
    if checkpoint_id(state)!=cp: raise PermissionError("recovery host/path rebinding changed scientific checkpoint")
    ws.save(state)
    try: persist_dashboard_generation(ws,state,trigger="recovery-resume")
    except Exception: ws.save(state)
    return ws.base
