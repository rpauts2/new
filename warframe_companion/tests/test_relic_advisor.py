import io
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from relic_advisor import download_dataset, find_relics, load_dataset


class RelicAdvisorTests(unittest.TestCase):
    def setUp(self):
        self.relics = [
            {
                "tier": "Lith",
                "relicName": "A1",
                "rewards": [
                    {"itemName": "Forma Blueprint", "chance": 11, "rarity": "Common"},
                    {"itemName": "Example Prime Part", "chance": 2, "rarity": "Rare"},
                ],
            },
            {
                "tier": "Axi",
                "relicName": "B2",
                "rewards": {
                    "Intact": [{"itemName": "Example Prime Part", "chance": 6}],
                    "Radiant": [{"itemName": "Example Prime Part", "chance": 20}],
                },
            },
        ]

    def test_partial_search_sorts_by_recorded_chance(self):
        results = find_relics(self.relics, "example prime")
        self.assertEqual([row["chance"] for row in results], [20, 6, 2])
        self.assertEqual(results[0]["relic"], "B2")

    def test_tier_filter(self):
        results = find_relics(self.relics, "Forma", tier="lith")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["relic"], "A1")

    def test_state_filter(self):
        results = find_relics(self.relics, "Example Prime Part", state="Radiant")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["chance"], 20)

    def test_exact_name(self):
        self.assertEqual(find_relics(self.relics, "Forma", exact=True), [])
        self.assertEqual(len(find_relics(self.relics, "Forma Blueprint", exact=True)), 1)

    def test_loads_list_and_metadata_wrapped_dataset(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "relics.json"
            path.write_text(json.dumps({"timestamp": 123, "relics": self.relics}), encoding="utf-8")
            loaded, metadata = load_dataset(path)
            self.assertEqual(len(loaded), 2)
            self.assertEqual(metadata["timestamp"], 123)

    def test_rejects_invalid_dataset(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"not_relics": []}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Expected a relic list"):
                load_dataset(path)

    def test_rejects_empty_query(self):
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            find_relics(self.relics, "  ")


    def test_download_validates_and_writes_dataset(self):
        payload = json.dumps({"relics": self.relics, "timestamp": 456}).encode()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "cache" / "relics.json"
            with patch("relic_advisor.urllib.request.urlopen", return_value=io.BytesIO(payload)):
                result = download_dataset(target, url="https://example.test/relics.json")
            loaded, metadata = load_dataset(result)
            self.assertEqual(len(loaded), 2)
            self.assertEqual(metadata["timestamp"], 456)

    def test_download_does_not_overwrite_cache_with_invalid_data(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "relics.json"
            target.write_text('{"relics": [{"tier": "Lith", "relicName": "Old"}]}', encoding="utf-8")
            with patch("relic_advisor.urllib.request.urlopen", return_value=io.BytesIO(b'{"not_relics": []}')):
                with self.assertRaisesRegex(ValueError, "not a valid relic dataset"):
                    download_dataset(target, url="https://example.test/relics.json")
            self.assertIn("Old", target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
