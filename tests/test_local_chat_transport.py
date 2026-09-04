from __future__ import annotations

import hashlib
import unittest

from juriscribe import host_bootstrap as mod


class LocalChatTransportTests(unittest.TestCase):
    def test_h0_does_not_include_session_activation_modules(self):
        self.assertEqual(
            mod.H0_HANDSHAKE_SOURCE_PATHS,
            (
                'juriscribe/__init__.py',
                'juriscribe/admission.py',
                'juriscribe/bootstrap.py',
                'juriscribe/host_bootstrap.py',
            ),
        )
        self.assertNotIn('juriscribe/portable_session.py', mod.H0_HANDSHAKE_SOURCE_PATHS)

    def test_git_blob_binding_accepts_exact_bytes(self):
        data = b'canonical bytes\n'
        expected = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        self.assertEqual(mod.validate_source_transport_binding(data, expected), expected)

    def test_git_blob_binding_rejects_mutation(self):
        data = b'canonical bytes\n'
        expected = mod.git_blob_sha1(data)
        with self.assertRaises(PermissionError):
            mod.validate_source_transport_binding(data + b'x', expected)

    def test_transport_witness_has_no_runtime_authority(self):
        data = b'x'
        sha = mod.git_blob_sha1(data)
        witness = mod.source_transport_witness(
            path='x',
            data=data,
            expected_git_blob_sha=sha,
            resolved_revision='a' * 40,
        )
        self.assertEqual(witness['authority'], 'HOST_TRANSPORT_EVIDENCE_ONLY')
        self.assertFalse(witness['runtime_receipt'])


if __name__ == '__main__':
    unittest.main()
