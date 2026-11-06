import unittest

from commands.organise import (
    assign_missing_spots_to_user,
    all_tracked_channels_bought,
    build_reserve_start_messages,
    is_phase_bypassed,
    mark_tracked_channels_bought,
    get_role_mentions_for_categories,
)


class StartLogicTests(unittest.TestCase):
    def test_shared_role_is_mentioned_once_for_empty_fields(self):
        class Role:
            def __init__(self, role_id):
                self.id = role_id
                self.mention = f"<@&{role_id}>"

        class Guild:
            def __init__(self, role):
                self.role = role

            def get_role(self, role_id):
                return self.role if role_id == self.role.id else None

        shared_role = Role(99)
        buyers_data = {
            "field_role_ids": {"Reserve 1": 99, "Reserve 2": 99},
            "buyers": [
                {"category": "Reserve 1", "claimed_user": None},
                {"category": "Reserve 2", "claimed_user": None},
            ],
        }

        self.assertEqual(
            get_role_mentions_for_categories(
                Guild(shared_role),
                buyers_data,
                ["Reserve 1", "Reserve 2"],
            ),
            ["<@&99>"],
        )

    def test_builds_exact_reserve_commands(self):
        buyers_data = {
            "buyers": [
                {
                    "category": "Rares",
                    "claimed_user": 123,
                    "reserve": ["vulpix"],
                },
                {
                    "category": "Regionals",
                    "claimed_user": 456,
                    "reserve": [],
                },
            ]
        }

        self.assertEqual(
            build_reserve_start_messages(buyers_data),
            [
                "m!r a rares, vulpix <@123>",
                "m!r a regionals <@456>",
            ],
        )

    def test_start_messages_use_field_names_for_event_categories(self):
        buyers_data = {
            "buyers": [
                {
                    "category": "Event Meowscarada",
                    "claimed_user": 123,
                    "reserve": ["oracle meowscarada"],
                },
            ]
        }

        self.assertEqual(
            build_reserve_start_messages(buyers_data),
            ["m!r a event meowscarada, oracle meowscarada <@123>"],
        )

    def test_reserve_fields_send_only_their_pokemon_names(self):
        buyers_data = {
            "buyers": [
                {
                    "category": "Reserve 1",
                    "claimed_user": 123,
                    "reserve": ["oracle meowscarada", "vulpix"],
                },
            ]
        }

        self.assertEqual(
            build_reserve_start_messages(buyers_data),
            [
                "m!r a oracle meowscarada <@123>",
                "m!r a vulpix <@123>",
            ],
        )

    def test_requires_all_tracked_channels_to_be_bought(self):
        buyers_data = {
            "buyers": [
                {
                    "allowed_channels": ["incense-1", "incense-2"],
                }
            ]
        }

        self.assertFalse(
            all_tracked_channels_bought(
                buyers_data,
                {"bought_channels": ["incense-1"]},
            )
        )
        self.assertTrue(
            all_tracked_channels_bought(
                buyers_data,
                {"bought_channels": ["incense-1", "incense-2"]},
            )
        )

    def test_phase_bypass_state_is_explicit(self):
        buyers_data = {"bypassed_phases": [1]}

        self.assertTrue(is_phase_bypassed(buyers_data, 1))
        self.assertFalse(is_phase_bypassed(buyers_data, 2))

    def test_phase_one_bypass_assigns_only_missing_spots_without_reserves(self):
        buyers_data = {
            "buyers": [
                {"claimed_user": None, "reserve": ["pikachu"]},
                {"claimed_user": 456, "reserve": ["eevee"]},
            ]
        }

        assign_missing_spots_to_user(buyers_data, 123)

        self.assertEqual(
            buyers_data["buyers"],
            [
                {"claimed_user": 123, "reserve": []},
                {"claimed_user": 456, "reserve": ["eevee"]},
            ],
        )

    def test_phase_two_bypass_marks_all_tracked_channels_bought(self):
        buyers_data = {
            "buyers": [
                {"allowed_channels": ["incense-1", "incense-2"]},
            ]
        }
        incense_data = {"bought_channels": ["incense-2"]}

        mark_tracked_channels_bought(buyers_data, incense_data)

        self.assertTrue(all_tracked_channels_bought(buyers_data, incense_data))
        self.assertEqual(incense_data["bought_channels"], ["incense-1", "incense-2"])


if __name__ == "__main__":
    unittest.main()
