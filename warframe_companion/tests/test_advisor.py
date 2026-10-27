import json
import subprocess
import sys
import unittest
from pathlib import Path

# Make the sibling advisor.py importable when tests are launched from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from advisor import recommend, MISSION_ROLES


class AdvisorTests(unittest.TestCase):
    def test_survival_returns_ranked_recommendations(self):
        result = recommend("Survival", limit=5)
        self.assertEqual(len(result), 5)
        self.assertTrue(all("frame" in item and "matched_roles" in item for item in result))

    def test_mission_name_normalization(self):
        self.assertEqual(
            recommend("sanctuary_onslaught", limit=2),
            recommend("Sanctuary Onslaught", limit=2),
        )

    def test_stealth_goal_includes_ivara(self):
        self.assertIn(
            "Ivara",
            [item["frame"] for item in recommend("Spy", goal="stealth", limit=10)],
        )

    def test_unknown_mission_is_explicit(self):
        with self.assertRaisesRegex(ValueError, "Unknown mission"):
            recommend("Moon mining")

    def test_mission_catalog_is_nonempty(self):
        self.assertIn("disruption", MISSION_ROLES)
        self.assertIn("void cascade", MISSION_ROLES)


    def test_excluded_frames_are_removed(self):
        results = recommend("Survival", limit=10, exclude=("Nekros", "Nova"))
        names = [item["frame"] for item in results]
        self.assertNotIn("Nekros", names)
        self.assertNotIn("Nova", names)

    def test_exclusion_is_case_and_spacing_insensitive(self):
        results = recommend("Survival", limit=10, exclude=("  nEkRoS  ",))
        self.assertNotIn("Nekros", [item["frame"] for item in results])

    def test_cli_json_output_is_valid(self):
        script = Path(__file__).resolve().parents[1] / "advisor.py"
        completed = subprocess.run(
            [sys.executable, str(script), "--mission", "Survival", "--format", "json", "--limit", "2"],
            check=True, capture_output=True, text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["mission"], "Survival")
        self.assertEqual(len(payload["recommendations"]), 2)


if __name__ == "__main__":
    unittest.main()
