"""Pilot onboarding and privacy checks; only isolated fixtures are mutated."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
import workflow as w
import improvement
import doctor
import server


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / '项目记录').mkdir()
        (self.root / 'AGENTS.md').write_text('Isolated test only', encoding='utf-8')
        w.atomic(self.root / '项目记录/state.json', w.seed())
        w.atomic(self.root / '项目记录/工作流改进.json', improvement.seed())

    def test_transient_windows_file_lock_recovers_without_reset(self):
        path = self.root / '项目记录/state.json'
        state = w.read_json(path); state['title'] = 'Updated after transient lock'
        original = w.os.replace
        denied = PermissionError('simulated Windows sharing conflict'); denied.winerror = 32
        attempts = []
        def replace(source, target):
            attempts.append(target)
            if len(attempts) < 3: raise denied
            return original(source, target)
        with mock.patch.object(w.os, 'replace', side_effect=replace), mock.patch.object(w.time, 'sleep'):
            w.atomic(path, state)
        self.assertEqual(w.read_json(path), state)
        self.assertEqual(len(attempts), 3)

    def test_persistent_file_lock_preserves_original_and_stops_retrying(self):
        path = self.root / '项目记录/state.json'
        before = w.read_json(path)
        denied = PermissionError('simulated persistent lock'); denied.winerror = 5
        with mock.patch.object(w.os, 'replace', side_effect=denied) as replace, mock.patch.object(w.time, 'sleep'):
            with self.assertRaises(PermissionError): w.atomic(path, {'not': 'saved'})
        self.assertEqual(replace.call_count, 5)
        self.assertEqual(w.read_json(path), before)
        self.assertEqual(list(path.parent.glob('state-*.tmp')), [])

    def test_missing_game_engine_does_not_fail_workflow_preflight(self):
        report = doctor.inspect(self.root)
        self.assertTrue(report['ok'])
        self.assertFalse(report['game_root_structure'])
        self.assertEqual(report['game_markers'], [])

    def test_second_workspace_cannot_bind_the_running_server_port(self):
        first = server.LocalHTTPServer(('127.0.0.1', 0), server.Handler)
        self.addCleanup(first.server_close)
        with self.assertRaises(OSError):
            second = server.LocalHTTPServer(first.server_address, server.Handler)
            second.server_close()

    def test_godot_and_unreal_are_detected_without_claiming_runtime(self):
        game = self.root / 'Game'; game.mkdir()
        (game / 'project.godot').write_text('[application]')
        self.assertIn('Godot', doctor.inspect(self.root)['game_markers'])
        (game / 'sample.uproject').write_text('{}')
        report = doctor.inspect(self.root)
        self.assertIn('Unreal', report['game_markers'])
        self.assertTrue(all(v.startswith('待 AI') for v in report['capabilities'].values()))

    def test_document_catalog_excludes_private_backup_markdown(self):
        previous = server.ROOT
        server.ROOT = self.root
        self.addCleanup(setattr, server, 'ROOT', previous)
        for ref in ('项目记录/当前操作/step.md', '项目记录/backups/secret.md',
                    '项目记录/工作流改进证据/变更备份/secret.md', 'docs/.private/secret.md'):
            p = self.root / ref; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('fixture')
        self.assertEqual(server.documents(), ['项目记录/当前操作/step.md'])

    def test_clean_initialization_has_first_action_card_and_preserves_existing_records(self):
        # Use the actual CLI from a separate root, not monkeypatched production state.
        target = self.root / '新项目 中文 path'
        shutil.copytree(APP, target / '04_本地进度网页', ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(APP.parent / '05_项目模板', target / '05_项目模板')
        command = [sys.executable, '-B', str(target / '04_本地进度网页/init_project.py')]
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stderr)
        path = target / '项目记录/state.json'
        state = w.read_json(path)
        self.assertTrue((target / state['tasks'][0]['instructions']).is_file())
        self.assertTrue(all(t['status'] == 'pending' and not t['evidence'] for t in state['tasks']))
        concept = target / '项目记录/项目概念.md'
        concept.write_text('客户已有的解谜设计', encoding='utf-8')
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(concept.read_text(encoding='utf-8'), '客户已有的解谜设计')
        self.assertEqual(w.read_json(path), state)


if __name__ == '__main__':
    unittest.main()
