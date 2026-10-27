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
            {"mission": "Survival", "duration_minutes": 5, "frame": "Nekros", "reward": "Forma", "completed": True},
            {"mission": "Survival", "duration_minutes": 7, "frame": "Nekros", "reward": "Forma", "completed": True},
            {"mission": "Spy", "duration_minutes": 3, "frame": "Loki", "reward": "Part", "completed": False},
        ]
        stats = summarize(entries)
        self.assertEqual(stats["sessions"], 3)
        self.assertEqual(stats["completed_sessions"], 2)
        self.assertEqual(stats["total_minutes"], 12)
        self.assertEqual(stats["average_minutes"], 6)
        self.assertEqual(stats["rewards"], {"Forma": 2})
        self.assertEqual(stats["reward_rates_per_hour"], {"Forma": 10.0})
        self.assertEqual(stats["missions"], {"Spy": 1, "Survival": 2})
        self.assertEqual(stats["by_mission"]["Survival"], {
            "sessions": 2, "completed_sessions": 2, "completed_minutes": 12.0, "average_completed_minutes": 6.0,
        })
        self.assertEqual(stats["by_mission"]["Spy"]["completed_sessions"], 0)
        self.assertEqual(stats["by_frame"]["Nekros"]["completed_minutes"], 12.0)
        self.assertEqual(stats["by_frame"]["Loki"]["completed_minutes"], 0.0)
        self.assertEqual(stats["reward_rates_per_hour_by_mission"]["Survival"], {"Forma": 10.0})
        self.assertEqual(stats["reward_rates_per_hour_by_mission"]["Spy"], {})
        self.assertEqual(stats["reward_rates_per_hour_by_frame"]["Nekros"], {"Forma": 10.0})
        self.assertEqual(stats["reward_rates_per_hour_by_frame"]["Loki"], {})

    def test_reward_rates_do_not_mix_time_between_missions_or_frames(self):
        stats = summarize([
            {"mission": "Survival", "duration_minutes": 10, "frame": "Nekros", "reward": "Forma", "completed": True},
            {"mission": "Capture", "duration_minutes": 30, "frame": "Loki", "reward": "Forma", "completed": True},
            {"mission": "Survival", "duration_minutes": 10, "frame": "Nekros", "reward": "Forma", "completed": True},
        ])
        self.assertEqual(stats["reward_rates_per_hour"]["Forma"], 3.6)
        self.assertEqual(stats["reward_rates_per_hour_by_mission"]["Survival"]["Forma"], 6.0)
        self.assertEqual(stats["reward_rates_per_hour_by_mission"]["Capture"]["Forma"], 2.0)
        self.assertEqual(stats["reward_rates_per_hour_by_frame"]["Nekros"]["Forma"], 6.0)
        self.assertEqual(stats["reward_rates_per_hour_by_frame"]["Loki"]["Forma"], 2.0)

    def test_rejects_invalid_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log.jsonl"
            with self.assertRaisesRegex(ValueError, "must not be empty"):
                add_entry(path, " ", 5)
            for duration in (0, -1, float("nan"), float("inf"), "not a number"):
                with self.subTest(duration=duration):
                    with self.assertRaisesRegex(ValueError, "finite number greater than zero"):
                        add_entry(path, "Survival", duration)

    def test_summary_rejects_corrupt_duration_and_completion_flag(self):
        with self.assertRaisesRegex(ValueError, "session entry 1"):
            summarize([{"mission": "Survival", "duration_minutes": "invalid"}])
        with self.assertRaisesRegex(ValueError, "completed must be true or false"):
            summarize([{"mission": "Survival", "duration_minutes": 5, "completed": "yes"}])

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

    def test_automatic_backups_do_not_overwrite_same_second(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "missions.jsonl"
            add_entry(source, "Survival", 5, reward="Forma")
            first = backup_log(source)
            second = backup_log(source)
            self.assertNotEqual(first, second)
            self.assertTrue(first.exists())
            self.assertTrue(second.exists())

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
