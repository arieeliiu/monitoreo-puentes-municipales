"""Regresiones de trazabilidad: HEAD no equivale a un worktree modificado."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.run_ev3_checks import code_revision, source_hashes


class EvidenceProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.git('init','-b','feature/ev3-cierre-tecnico')
        self.git('config','user.name','Evidence fixture')
        self.git('config','user.email','fixture@example.invalid')
        self.git('config','core.autocrlf','false')
        self.source=self.root/'source.py'
        self.source.write_bytes(b'VALUE = 1\n')
        self.git('add','source.py');self.git('commit','-m','fixture base')
        self.base=self.git('rev-parse','HEAD')
        self.git('update-ref','refs/remotes/origin/main',self.base)

    def git(self,*args):
        return subprocess.check_output(['git',*args],cwd=self.root,text=True,encoding='utf-8',stderr=subprocess.DEVNULL).strip()

    def test_clean_commit_differs_from_comparison_base(self):
        self.source.write_bytes(b'VALUE = 2\n')
        self.git('add','source.py');self.git('commit','-m','fixture correction')
        revision=code_revision(self.root,[self.source])
        self.assertNotEqual(revision['head_commit'],self.base)
        self.assertEqual(revision['comparison_base']['commit'],self.base)
        self.assertTrue(revision['worktree_clean'])
        self.assertTrue(revision['source_matches_head'])

    def test_modified_and_untracked_sources_are_not_attributed_to_head(self):
        before=source_hashes(self.root,[self.source])
        self.source.write_bytes(b'VALUE = 3\n')
        extra=self.root/'extra.py';extra.write_bytes(b'OTHER = 4\n')
        revision=code_revision(self.root,[self.source,extra])
        self.assertFalse(revision['worktree_clean'])
        self.assertFalse(revision['source_matches_head'])
        self.assertFalse(revision['source_git_blobs']['source.py']['matches_head'])
        self.assertIsNone(revision['source_git_blobs']['extra.py']['head_blob'])
        self.assertNotEqual(before,source_hashes(self.root,[self.source]))

    def test_line_endings_compare_git_content_and_preserve_raw_hash(self):
        self.git('config','core.autocrlf','true')
        initial=source_hashes(self.root,[self.source])
        self.source.write_bytes(b'VALUE = 1\r\n')
        revision=code_revision(self.root,[self.source])
        self.assertTrue(revision['source_matches_head'])
        self.assertNotEqual(initial,source_hashes(self.root,[self.source]))


if __name__=='__main__':unittest.main()
