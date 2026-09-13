"""Disposable installer checks: no proprietary game files required."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from installer import core
from tools import common


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.game = self.base / '日本語 Game (Copy)'
        self.game.mkdir()
        (self.game / 'asairo.exe').write_bytes(b'test executable')
        (self.game / 'Scenario.mpk').write_bytes(b'original archive')
        (self.game / 'save').mkdir()
        (self.game / 'save/slot.dat').write_bytes(b'original save')
        self.files = {name: ('fixture: ' + name).encode() for name in common.PAYLOAD_PATHS}
        self.rows = [{'path': name, 'sha256': hashlib.sha256(data).hexdigest()} for name, data in sorted(self.files.items())]
        for mock in [patch.object(common, 'EXPECTED_EXE', common.digest(self.game / 'asairo.exe')),
                     patch.object(core, 'manifest', return_value=self.rows),
                     patch.object(core, 'payload', return_value=self.files),
                     patch.object(core, 'require_closed')]:
            mock.start()
            self.addCleanup(mock.stop)

    def test_install_remove_and_save_backups(self):
        self.assertEqual(core.status(self.game), 'ADV')
        core.change(self.game, True)
        self.assertEqual(core.status(self.game), 'NVL')
        core.change(self.game, False)
        self.assertEqual(core.status(self.game), 'ADV')
        backups = list((self.game / '_nvl_backups').iterdir())
        self.assertEqual(len(backups), 2)
        for backup in backups:
            self.assertEqual((backup / 'save/slot.dat').read_bytes(), b'original save')
        removed = next(p for p in backups if p.name.startswith('mode_disable_'))
        for name, data in self.files.items():
            self.assertEqual((removed / name).read_bytes(), data)
        self.assertEqual((self.game / 'Scenario.mpk').read_bytes(), b'original archive')
        self.assertEqual((self.game / 'save/slot.dat').read_bytes(), b'original save')

    def test_idempotence(self):
        core.change(self.game, True)
        before = list((self.game / '_nvl_backups').iterdir())
        core.change(self.game, True)
        self.assertEqual(list((self.game / '_nvl_backups').iterdir()), before)

    def test_unknown_override_blocks_all_changes(self):
        (self.game / 'winmm.dll').write_bytes(b'another mod')
        for enable in (True, False):
            with self.assertRaisesRegex(RuntimeError, 'unknown file'):
                core.change(self.game, enable)
        self.assertFalse((self.game / '_nvl_backups').exists())
        self.assertEqual((self.game / 'winmm.dll').read_bytes(), b'another mod')

    def test_wrong_executable(self):
        (self.game / 'asairo.exe').write_bytes(b'unsupported')
        with self.assertRaisesRegex(RuntimeError, 'Unsupported'):
            core.change(self.game, True)

    def test_original_folder_refused(self):
        original = self.base / 'Original'
        self.game.rename(original)
        with self.assertRaisesRegex(RuntimeError, 'separate directory'):
            core.change(original, True)

    def test_running_game_refused(self):
        with patch.object(core, 'require_closed', side_effect=RuntimeError('Close every instance')):
            with self.assertRaisesRegex(RuntimeError, 'Close every instance'):
                core.change(self.game, True)
        self.assertFalse((self.game / '_nvl_backups').exists())

    def test_partial_install_repaired_and_removed(self):
        core.change(self.game, True)
        (self.game / 'winmm.dll').unlink()
        self.assertEqual(core.status(self.game), 'INCOMPLETE')
        core.change(self.game, True)
        self.assertEqual(core.status(self.game), 'NVL')
        (self.game / 'winmm.dll').unlink()
        core.change(self.game, False)
        self.assertEqual(core.status(self.game), 'ADV')

    def test_failed_install_rolls_back(self):
        real_replace = core.replace_bytes
        calls = 0
        def fail_second(destination, data):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('simulated disk failure')
            real_replace(destination, data)
        with patch.object(core, 'replace_bytes', side_effect=fail_second):
            with self.assertRaisesRegex(RuntimeError, 'rolled back'):
                core.change(self.game, True)
        self.assertEqual(core.status(self.game), 'ADV')

    def test_failed_removal_rolls_back(self):
        core.change(self.game, True)
        real_unlink = Path.unlink
        calls = 0
        def fail_second(path, *args, **kwargs):
            nonlocal calls
            if path.parent != self.game / '_nvl_backups' and path.name in {'NV00.mgr', '01game.msc'}:
                calls += 1
                if calls == 2:
                    raise OSError('simulated removal failure')
            return real_unlink(path, *args, **kwargs)
        with patch.object(Path, 'unlink', fail_second):
            with self.assertRaisesRegex(RuntimeError, 'rolled back'):
                core.change(self.game, False)
        self.assertEqual(core.status(self.game), 'NVL')

    def test_backup_failure_leaves_payload_untouched(self):
        with patch.object(core, 'snapshot_saves', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                core.change(self.game, True)
        self.assertEqual(core.status(self.game), 'ADV')

    def test_generation_failure_leaves_game_untouched(self):
        with patch.object(core, 'payload', side_effect=RuntimeError('mismatch')):
            with self.assertRaisesRegex(RuntimeError, 'mismatch'):
                core.change(self.game, True)
        self.assertFalse((self.game / '_nvl_backups').exists())

    def test_linked_directory_refused(self):
        outside = self.base / 'outside'
        outside.mkdir()
        try:
            (self.game / 'Scenario').symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('Symlink creation not available to this account')
        with self.assertRaises(RuntimeError):
            core.change(self.game, True)
        self.assertEqual(list(outside.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
