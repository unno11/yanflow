from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import shutil

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('workflow_init', ROOT/'scripts/init_project.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InitProjectTests(unittest.TestCase):
    def setUp(self):
        # Test data lives outside the installed skill; TMPDIR/TEMP may select a writable root.
        test_parent = Path(tempfile.gettempdir()).resolve()
        self.temp = tempfile.TemporaryDirectory(prefix='yanflow-test-')
        self.root = Path(self.temp.name).resolve()
        assert self.root.is_relative_to(test_parent)
        assert self.root.name.startswith('yanflow-test-')
        self.addCleanup(self.temp.cleanup)
        self.library = self.root/'共享 文献库'
        self.project = self.root/'研究项目'

    def test_project_links_shared_library_and_keeps_separate_records(self):
        actions = module.initialize(self.library, self.project, name='示例项目', goal='理解机制')
        for item in actions:
            self.assertNotIn('{{', Path(item['path']).read_text(encoding='utf-8'))
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
            self.assertIn('现行交接', text)

    def test_project_only_does_not_create_or_require_library(self):
        actions = module.initialize(project_dir=self.project)
        self.assertTrue((self.project/'AGENTS.md').is_file())
        self.assertFalse(self.library.exists())
        self.assertEqual(len(actions), len(module.PROJECT_FILES))
        for name in ['AGENTS.md', 'related_work/index.md']:
            text = (self.project/name).read_text(encoding='utf-8')
            self.assertIn('可选，未建立', text)
            self.assertNotIn('{{', text)

    def test_entrypoints_only_preserves_external_records_and_existing_layout(self):
        main = self.root/'笔记主纲.md'
        handoff = self.root/'现行交接.md'
        main.write_text('主线与完整约束', encoding='utf-8')
        handoff.write_text('已有进度与编排', encoding='utf-8')
        (self.project/'experiments').mkdir(parents=True)
        actions = module.initialize(project_dir=self.project, entrypoints=('claude',),
                                    entrypoints_only=True, main_record=main,
                                    handoff_record=handoff, maintainer='会话甲',
                                    constraints=('不推送、不改服务器',))
        self.assertEqual({p.name for p in self.project.iterdir()},
                         {'AGENTS.md', 'CLAUDE.md', 'experiments'})
        entry = (self.project/'AGENTS.md').read_text(encoding='utf-8')
        self.assertIn(main.as_posix(), entry)
        self.assertIn(handoff.as_posix(), entry)
        self.assertIn('不推送、不改服务器', entry)
        self.assertIn('会话甲', entry)
        self.assertFalse(self.library.exists())
        self.assertEqual(main.read_text(encoding='utf-8'), '主线与完整约束')
        self.assertEqual(handoff.read_text(encoding='utf-8'), '已有进度与编排')
        self.assertEqual(len(actions), 2)

    def test_similar_directory_requires_choice_before_any_writes(self):
        (self.project/'experiments').mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, '等价目录'):
            module.initialize(self.library, self.project)
        self.assertFalse(self.library.exists())
        self.assertEqual(list(self.project.iterdir()), [self.project/'experiments'])

    @unittest.skipUnless(shutil.which('git'), 'Git is needed to verify ignore reporting')
    def test_ignored_entrypoint_is_local_only_without_changing_ignore_rules(self):
        self.project.mkdir()
        subprocess.run(['git','init','--quiet',str(self.project)], check=True)
        ignore = self.project/'.gitignore'
        ignore.write_text('CLAUDE.md\n', encoding='utf-8')
        before = ignore.read_bytes()
        actions = module.initialize(project_dir=self.project, entrypoints=('claude',),
                                    entrypoints_only=True)
        claude = next(item for item in actions if Path(item['path']).name == 'CLAUDE.md')
        self.assertEqual(claude['tracking'], 'ignored-local-only')
        self.assertEqual(ignore.read_bytes(), before)
        tracked = subprocess.check_output(['git','-C',str(self.project),'ls-files'])
        self.assertEqual(tracked, b'')

    def test_no_target_and_invalid_external_records_have_no_side_effects(self):
        for kwargs in [{}, {'project_dir':self.project, 'main_record':self.root/'missing',
                            'entrypoints_only':True},
                       {'project_dir':self.project, 'library_dir':self.library,
                        'entrypoints_only':True}]:
            with self.assertRaises(ValueError):
                module.initialize(**kwargs)
            self.assertFalse(self.project.exists())
            self.assertFalse(self.library.exists())

    def test_cli_project_only_entrypoints_without_library(self):
        proc = subprocess.run([
            sys.executable, '-X','utf8','-B',str(ROOT/'scripts/init_project.py'),
            '--project-dir',str(self.project),'--entrypoints-only','--entrypoint','claude',
        ], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual({p.name for p in self.project.iterdir()}, {'AGENTS.md','CLAUDE.md'})


if __name__ == '__main__':
    unittest.main()
