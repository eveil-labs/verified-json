import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/verification'))
from source_envelope import load_root_set, snapshot_source, source_files, files_digest

class SourceEnvelopeTests(unittest.TestCase):
    def setUp(self):
        scratch=Path(os.environ['VERIFIED_JSON_TEST_WORK'])
        self.tmp=tempfile.TemporaryDirectory(dir=scratch);self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'source';self.root.mkdir()
        (self.root/'proofs').mkdir();(self.root/'lean/VerifiedJson').mkdir(parents=True)
        for name in ['Spec','Grammar','DocumentSpec']:
            (self.root/f'lean/VerifiedJson/{name}.lean').write_text('namespace Test\nend Test\n')
        bindings=[{'path':f'lean/VerifiedJson/{n}.lean','sha256':hashlib.sha256((self.root/f'lean/VerifiedJson/{n}.lean').read_bytes()).hexdigest()} for n in ['DocumentSpec','Spec','Grammar']]
        for filename,decl in [('roots.json','Test.helper'),('document-spec-roots.json','Test.witness')]:
            record={'declarations':[decl],'meaning_roots':['Test.Type'],
                    'allowed_axioms':['propext','Quot.sound','Classical.choice'],'source_bindings':bindings}
            if filename.startswith('document'):record['source_sha256']=bindings[0]['sha256']
            (self.root/'proofs'/filename).write_text(json.dumps(record))
    def mutate(self,name,key,value):
        p=self.root/'proofs'/name;d=json.loads(p.read_text());d[key]=value;p.write_text(json.dumps(d))
    def test_both_manifests_are_required(self):
        (self.root/'proofs/document-spec-roots.json').unlink()
        with self.assertRaises(FileNotFoundError):load_root_set(self.root)
    def test_stale_claimed_source_digest_fails(self):
        self.mutate('document-spec-roots.json','source_sha256','0'*64)
        with self.assertRaisesRegex(ValueError,'source_sha256'):load_root_set(self.root)
    def test_changed_source_or_dependency_fails(self):
        for name in ['DocumentSpec','Spec','Grammar']:
            p=self.root/f'lean/VerifiedJson/{name}.lean';old=p.read_bytes();p.write_bytes(old+b'-- changed\n')
            with self.assertRaisesRegex(ValueError,'stale source'):load_root_set(self.root)
            p.write_bytes(old)
    def test_zero_roots_and_widened_basis_fail(self):
        self.mutate('roots.json','declarations',[])
        with self.assertRaises(ValueError):load_root_set(self.root)
        self.mutate('roots.json','declarations',['Test.helper'])
        self.mutate('roots.json','allowed_axioms',['sorryAx'])
        with self.assertRaises(ValueError):load_root_set(self.root)
    def test_duplicate_and_injected_roots_fail(self):
        self.mutate('roots.json','declarations',['Test.witness'])
        with self.assertRaisesRegex(ValueError,'duplicate'):load_root_set(self.root)
        self.mutate('roots.json','declarations',['Test.helper'])
        self.mutate('roots.json','meaning_roots',['Test.Type\n#eval bad'])
        with self.assertRaises(ValueError):load_root_set(self.root)
    def test_contract_dependency_census_required(self):
        self.mutate('document-spec-roots.json','source_bindings',[])
        with self.assertRaises(ValueError):load_root_set(self.root)
    def test_snapshot_matches_bytes_and_does_not_follow_symlinks(self):
        dest=Path(self.tmp.name)/'snapshot';files=snapshot_source(self.root,dest)
        self.assertEqual(files,source_files(dest));self.assertEqual(files_digest(files),files_digest(source_files(self.root)))
        (self.root/'link').symlink_to(self.root/'lean/VerifiedJson/Spec.lean')
        with self.assertRaisesRegex(ValueError,'symlink'):source_files(self.root)
    def test_binding_cannot_traverse(self):
        self.mutate('roots.json','source_bindings',[{'path':'../outside','sha256':'0'*64}])
        with self.assertRaises(ValueError):load_root_set(self.root)

if __name__=='__main__':unittest.main()
