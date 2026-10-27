import unittest
from advisor import recommend, MISSION_ROLES

class AdvisorTests(unittest.TestCase):
    def test_survival_returns_ranked_recommendations(self):
        result = recommend("Survival", limit=5)
        self.assertEqual(len(result), 5)
        self.assertTrue(all("frame" in item and "matched_roles" in item for item in result))
    def test_mission_name_normalization(self):
        self.assertEqual(recommend("sanctuary_onslaught", limit=2), recommend("Sanctuary Onslaught", limit=2))
    def test_stealth_goal_includes_ivara(self):
        self.assertIn("Ivara", [item["frame"] for item in recommend("Spy", goal="stealth", limit=10)])
    def test_unknown_mission_is_explicit(self):
        with self.assertRaisesRegex(ValueError, "Unknown mission"):
            recommend("Moon mining")
    def test_mission_catalog_is_nonempty(self):
        self.assertIn("disruption", MISSION_ROLES)
        self.assertIn("void cascade", MISSION_ROLES)

if __name__ == "__main__":
    unittest.main()
