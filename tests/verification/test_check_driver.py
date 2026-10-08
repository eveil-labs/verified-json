import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import check
from process_runner import ProcessResult

class CheckDriverTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=os.environ['VERIFIED_JSON_TEST_WORK'])
        self.addCleanup(self.tmp.cleanup);self.work=Path(self.tmp.name)
    def test_raw_diagnostics_match_receipt_hash(self):
        result=check.run([sys.executable,'-B','-S','-c','import os; os.write(1, bytes([255]))'],
                         cwd=self.work,env={'PATH':'/usr/bin:/bin'},work=self.work,name='bytes',timeout=2)
        raw=(self.work/'bytes.log').read_bytes()
        self.assertEqual(raw,b'\xff');self.assertEqual(result['log_sha256'],hashlib.sha256(raw).hexdigest())
    def test_missing_exit_or_reaping_never_succeeds(self):
        for code,reaped in [(None,False),(0,False)]:
            observed=ProcessResult(code,b'',b'',False,False,None,0.0,'not_attempted',reaped)
            with patch('check.run_bounded',return_value=observed):
                with self.assertRaisesRegex(RuntimeError,'infrastructure'):
                    check.run(['unused'],cwd=self.work,env={},work=self.work,name=f'absent-{code}',timeout=1)
    def test_timeout_keeps_partial_diagnostics_and_metadata(self):
        observed=ProcessResult(-9,b'partial\xff',b'',True,False,'pipe uncertain',0.1,'uncertain',True)
        with patch('check.run_bounded',return_value=observed):
            with self.assertRaisesRegex(RuntimeError,'infrastructure'):
                check.run(['unused'],cwd=self.work,env={},work=self.work,name='timeout',timeout=1)
        self.assertEqual((self.work/'timeout.log').read_bytes(),b'partial\xff')
        self.assertTrue(json.loads((self.work/'timeout.json').read_text())['timed_out'])

if __name__=='__main__':unittest.main()
