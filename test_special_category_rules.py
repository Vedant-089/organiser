import unittest

from commands.organise import OrganiseBaseCog


class SpecialCategoryRuleTests(unittest.TestCase):
    def setUp(self):
        self.cog = object.__new__(OrganiseBaseCog)

    def test_loads_names_from_specific_category_files(self):
        names = self.cog.load_special_category_names()

        self.assertIn("galarian articuno", names)
        self.assertIn("vaporeon", names)
        self.assertIn("iron valiant", names)
        self.assertIn("charizard", names)

    def test_specific_category_names_are_blocked(self):
        self.assertTrue(
            self.cog.is_blocked_reserve_name(
                "galarian articuno",
                {},
                {},
            )
        )
        self.assertTrue(
            self.cog.is_blocked_reserve_name(
                "iron valiant",
                {},
                {},
            )
        )


if __name__ == "__main__":
    unittest.main()
