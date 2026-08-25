from __future__ import annotations
import json
import unittest
from pathlib import Path
from juriscribe import __version__
from juriscribe.admission import CONTRACT_VERSION, contract_digest
from juriscribe.modes import MODES, COMPRESSION_CONSOLIDATION

ROOT=Path(__file__).resolve().parents[1]

class ModeContractV11Tests(unittest.TestCase):
    def test_admission_contract_manifest_and_runtime_are_coherent(self):
        admission=json.loads((ROOT/'ADMISSION.json').read_text(encoding='utf-8'))
        manifest=json.loads((ROOT/'MANIFEST.json').read_text(encoding='utf-8'))
        contract=(ROOT/'ISENECA_ACCESS_CONTRACT.md').read_text(encoding='utf-8')
        self.assertEqual(admission['canonical_modes'],list(MODES))
        self.assertEqual(manifest['modes']['canonical'],list(MODES))
        self.assertEqual(admission['contract_version'],CONTRACT_VERSION)
        self.assertEqual(manifest['contract_version'],CONTRACT_VERSION)
        self.assertEqual(manifest['runtime_version'],__version__)
        self.assertEqual(admission['contract_sha256'],contract_digest(contract))
        self.assertIn(COMPRESSION_CONSOLIDATION,contract)
        self.assertTrue(admission['dynamic_mode_discovery_required'])
        self.assertEqual(manifest['compression_consolidation']['mutation_cases_min'],10_000_000)
        self.assertEqual(manifest['compression_consolidation']['no_novelty_tail_min'],1000)
        self.assertEqual(manifest['compression_consolidation']['no_better_compression_tail_min'],1000)

if __name__=='__main__': unittest.main()
