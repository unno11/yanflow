from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('workflow_init', ROOT/'scripts/init_project.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InitProjectTests(unittest.TestCase):
    def setUp(self):
        # Only this test-created subtree is cleaned up by TemporaryDirectory.
        test_parent = (ROOT/'.test-tmp').resolve()
        test_parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='research-workflow-', dir=test_parent)
        self.root = Path(self.temp.name).resolve()
        assert self.root.is_relative_to(test_parent)
        assert self.root.name.startswith('research-workflow-')
        self.addCleanup(self.temp.cleanup)
        self.library = self.root/'共享 文献库'
        self.project = self.root/'研究项目'

    def test_project_links_shared_library_and_keeps_separate_records(self):
        module.initialize(self.library, self.project, name='示例项目', goal='理解机制')
        self.assertTrue((self.library/'papers').is_dir())
        self.assertTrue((self.project/'复现').is_dir())
        self.assertTrue((self.project/'learning.md').is_file())
        self.assertIn((self.library/'index.md').as_posix(),
                      (self.project/'related_work/index.md').read_text(encoding='utf-8'))
        self.assertFalse((self.project/'papers').exists())
        self.assertFalse((self.project/'CLAUDE.md').exists())

    def test_rerun_preserves_user_instructions_data_and_tool_entries(self):
        module.initialize(self.library, self.project, entrypoints=('claude','gemini'))
        for name in ['AGENTS.md','CLAUDE.md','GEMINI.md','learning.md']:
            (self.project/name).write_text('使用者已有内容：'+name, encoding='utf-8')
        (self.project/'DataSet/raw.bin').write_bytes(b'keep-data')
        before = {p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        module.initialize(self.library, self.project, name='另一个名字', entrypoints=('claude','gemini'))
        for path, data in before.items():
            self.assertEqual(path.read_bytes(), data)

    def test_multiple_projects_reuse_library_without_overwriting_index(self):
        module.initialize(self.library, self.project)
        saved = (self.library/'index.md').read_bytes()
        other = self.root/'第二项目'
        module.initialize(self.library, other)
        self.assertEqual((self.library/'index.md').read_bytes(), saved)
        self.assertIn((self.library/'index.md').as_posix(),
                      (other/'related_work/index.md').read_text(encoding='utf-8'))

    def test_library_only_and_invalid_requests_have_no_project_side_effects(self):
        module.initialize(self.library)
        self.assertTrue((self.library/'index.md').is_file())
        self.assertFalse((self.library/'AGENTS.md').exists())
        for lib, project, entries in [
            (self.root/'same', self.root/'same', ()),
            (self.root/'invalid', None, ('claude',)),
            (self.root/'unknown', self.project, ('unknown',)),
        ]:
            with self.assertRaises(ValueError):
                module.initialize(lib, project, entrypoints=entries)
            self.assertFalse(lib.exists())

    def test_command_line_generates_requested_short_entries(self):
        proc = subprocess.run([
            sys.executable, '-X', 'utf8', '-B', str(ROOT/'scripts/init_project.py'),
            '--library-dir', str(self.library), '--project-dir', str(self.project),
            '--entrypoint', 'claude', '--entrypoint', 'gemini',
        ], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for name in ['CLAUDE.md','GEMINI.md']:
            text = (self.project/name).read_text(encoding='utf-8')
            self.assertIn('AGENTS.md', text)
            self.assertIn('handoff.md', text)


if __name__ == '__main__':
    unittest.main()
