import unittest

from commands.organise import get_tracked_channel_names, parse_template_message


TEMPLATE = """\
Rare - 35 incense - 350k - 1
Regional - 20 incense - 200k - 1
Gmax - 23 incense - 230k - 1
Eevos - 10 incense - 100k - 1
Paradox - 8 incense - 80k - 1
Reserves (2 res) - 6 incense - 60k - 2
Event Meowscarada - 50 incense - 500k - 1
Event Reuniclus - 49 incense - 490k - 1
Event Simipour - 48 incense - 480k - 1
Event Applin - 45 incense - 450k - 1
"""


class TemplateParserTests(unittest.TestCase):
    def test_builds_cumulative_ranges_and_prices(self):
        template = parse_template_message(TEMPLATE)

        self.assertEqual(template["total_incense"], 294)
        self.assertEqual(template["buyers"][0]["price"], "350k")
        self.assertEqual(template["buyers"][0]["channel_range"], [1, 35])
        self.assertEqual(template["buyers"][1]["channel_range"], [36, 55])
        self.assertEqual(template["buyers"][5]["max_reserves"], 2)

    def test_requires_max_reserves_field(self):
        with self.assertRaisesRegex(ValueError, "Line 1 is invalid"):
            parse_template_message("Rare - 35 incense - 350k")

    def test_tracks_template_channels(self):
        content = "\n".join(
            [
                "Rare - 35 incense - 350k - 1",
                "Regional - 65 incense - 650k - 1",
            ]
        )
        template = parse_template_message(content)
        buyers_data = {"buyers": template["buyers"]}

        self.assertEqual(template["total_incense"], 100)
        self.assertEqual(
            get_tracked_channel_names(buyers_data),
            {f"incense-{index}" for index in range(1, 101)},
        )


if __name__ == "__main__":
    unittest.main()
