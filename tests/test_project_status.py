import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('project_status', Path(__file__).resolve().parents[1]/'experiments/update_project_status.py')
status = importlib.util.module_from_spec(spec)
spec.loader.exec_module(status)


class ProjectStatusTests(unittest.TestCase):
    def test_manual_notes_and_history_survive_repeated_updates(self):
        text = f'manual preface\n{status.BEGIN}\nstale\n{status.END}\nmanual decision\n{status.HISTORY}\n\n| UTC | Record |\n|---|---|\n| old | preserved |\n'
        first = status.update_text(text, status.BEGIN+'fresh'+status.END, 'time1', 'checked')
        second = status.update_text(first, status.BEGIN+'newer'+status.END, 'time2', 'unchanged')
        self.assertIn('manual preface', second)
        self.assertIn('manual decision', second)
        self.assertIn('| old | preserved |', second)
        self.assertIn('| time1 | checked |', second)
        self.assertTrue(second.endswith('| time2 | unchanged |\n'))
        self.assertNotIn('stale', second)

    def test_missing_markers_refuse_overwrite(self):
        with self.assertRaises(ValueError):
            status.update_text('manual document', 'new', 'time', 'checked')
