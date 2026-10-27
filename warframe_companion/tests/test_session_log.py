import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from session_log import add_entry, backup_log, clear_log, export_csv, read_entries, summarize


class SessionLogTests(unittest.TestCase):
    def test_add_and_read_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "missions.jsonl"
            saved = add_entry(path, "Survival", 5, frame="Nekros", relic="Lith A1", reward="Forma Blueprint")
            loaded = read_entries(path)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["mission"], "Survival")
            self.assertEqual(loaded[0]["reward"], "Forma Blueprint")
            self.assertTrue(saved["completed"])

    def test_summary_counts_only_completed_time_and_rewards(self):
        entries = [
            {"mission": "Survival", "duration_minutes": 5, "reward": "Forma", "completed": True},
            {"mission": "Survival", "duration_minutes": 7, "reward": "Forma", "completed": True},
            {"mission": "Spy", "duration_minutes": 3, "reward": "Part", "completed": False},
        ]
        stats = summarize(entries)
        self.assertEqual(stats["sessions"], 3)
        self.assertEqual(stats["completed_sessions"], 2)
        self.assertEqual(stats["total_minutes"], 12)
        self.assertEqual(stats["average_minutes"], 6)
        self.assertEqual(stats["rewards"], {"Forma": 2})
        self.assertEqual(stats["reward_rates_per_hour"], {"Forma": 10.0})
        self.assertEqual(stats["missions"], {"Spy": 1, "Survival": 2})

    def test_rejects_invalid_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log.jsonl"
            with self.assertRaisesRegex(ValueError, "must not be empty"):
                add_entry(path, " ", 5)
            with self.assertRaisesRegex(ValueError, "greater than zero"):
                add_entry(path, "Survival", 0)

    def test_missing_log_is_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(read_entries(Path(directory) / "missing.jsonl"), [])

    def test_csv_export(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entry = add_entry(root / "missions.jsonl", "Capture", 2, reward="Neuroptics")
            output = root / "export.csv"
            export_csv([entry], output)
            content = output.read_text(encoding="utf-8-sig")
            self.assertIn("mission", content)
            self.assertIn("Capture", content)
            self.assertIn("Neuroptics", content)

    def test_backup_preserves_log_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "missions.jsonl"
            add_entry(source, "Survival", 5, reward="Forma")
            backup = backup_log(source, root / "manual-backup.jsonl")
            self.assertEqual(source.read_bytes(), backup.read_bytes())
            with self.assertRaises(FileExistsError):
                backup_log(source, backup)

    def test_clear_requires_confirmation_and_creates_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "missions.jsonl"
            add_entry(source, "Survival", 5, reward="Forma")
            original = source.read_bytes()
            with self.assertRaisesRegex(ValueError, "confirmation"):
                clear_log(source)
            backup = clear_log(source, confirm=True)
            self.assertEqual(source.read_text(encoding="utf-8"), "")
            self.assertEqual(backup.read_bytes(), original)
            self.assertEqual(read_entries(source), [])

    def test_malformed_log_is_not_backed_up_or_cleared(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "missions.jsonl"
            source.write_text("{broken json\n", encoding="utf-8")
            original = source.read_bytes()
            with self.assertRaisesRegex(ValueError, "Invalid JSON"):
                backup_log(source)
            with self.assertRaisesRegex(ValueError, "Invalid JSON"):
                clear_log(source, confirm=True)
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(list(Path(directory).glob("*.backup")), [])


if __name__ == "__main__":
    unittest.main()
