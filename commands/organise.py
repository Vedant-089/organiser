import json
import os
import re
import time
import asyncio

import discord
from discord import ui
from discord.ext import commands

TARGET_CHANNEL_ID = 1489538138258014268
END_CHANNEL_ID = 1489538138258014268
PURCHASE_TRACKER_AUTHOR_ID = 716390085896962058
PURCHASE_TRACKER_MESSAGE = "You purchased an Incense for 50 shards!"
TRACKER_PAUSE_ROLE_ID = 1489529695572852871
RESERVE_ACCESS_ROLE_ID = 1490123523543400749
ORG_BUYER_ROLE_NAME = "Org Buyer"
CATEGORY_TRACKED_CHANNEL_NAMES = {
    "Rares": {f"incense-{index}" for index in range(1, 31)},
    "Regionals": {f"incense-{index}" for index in range(31, 51)},
    "Gigantamax": {f"incense-{index}" for index in range(51, 66)},
    "Eeveelutions": {f"incense-{index}" for index in range(66, 81)},
    "Reserve-1": {f"incense-{index}" for index in range(81, 86)},
    "Reserve-2": {f"incense-{index}" for index in range(86, 91)},
    "Reserve-3": {f"incense-{index}" for index in range(91, 96)},
    "Reserve-4": {f"incense-{index}" for index in range(96, 101)},
}
RESERVE_SLOTS_BY_CATEGORY = {
    "Rares": 1,
    "Regionals": 1,
    "Gigantamax": 1,
    "Eeveelutions": 1,
    "Reserve-1": 2,
    "Reserve-2": 2,
    "Reserve-3": 2,
    "Reserve-4": 2,
    "Pokopia Ditto": 0,
}
BUYER_ROLE_NAME_ALIASES = {
    "Rares": ["Rares Buyer", "Rare Buyer"],
    "Regionals": ["Regionals Buyer", "Regional Buyer"],
    "Gigantamax": ["Gigantamax Buyer"],
    "Eeveelutions": ["Eeveelutions Buyer"],
    "Reserve-1": ["Reserve-1 Buyer", "Reserve 1 Buyer", "Reserves Buyer", "Reserve Buyer"],
    "Reserve-2": ["Reserve-2 Buyer", "Reserve 2 Buyer", "Reserves Buyer", "Reserve Buyer"],
    "Reserve-3": ["Reserve-3 Buyer", "Reserve 3 Buyer", "Reserves Buyer", "Reserve Buyer"],
    "Reserve-4": ["Reserve-4 Buyer", "Reserve 4 Buyer", "Reserves Buyer", "Reserve Buyer"],
    "Pokopia Ditto": ["Pokopia Ditto Buyer", "Ditto Buyer"],
    "Event-1": ["Event-1 Buyer", "Event 1 Buyer", "Event Buyer"],
    "Event-2": ["Event-2 Buyer", "Event 2 Buyer", "Event Buyer"],
}
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUYER_FILE = os.path.join(BASE_DIR, "buyer.json")
INCENSE_FILE = os.path.join(BASE_DIR, "incense.json")
CLASS_FILE = os.path.join(BASE_DIR, "class.json")
FORMS_FILE = os.path.join(BASE_DIR, "forms.json")
RESERVE_RULES_FILE = os.path.join(BASE_DIR, "reserve.json")
RESERVE_RULES_SOURCE_FILE = os.path.join(BASE_DIR, "reserve.txt")
RARE_FILE = os.path.join(BASE_DIR, "rare.json")
REGIONAL_FILE = os.path.join(BASE_DIR, "regional.json")
EEVEELUTIONS_PARADOX_FILE = os.path.join(BASE_DIR, "eeveelutions_paradox.json")
GIGANTAMAX_FILE = os.path.join(BASE_DIR, "gigantamax.json")
TEMPLATES_FILE = os.path.join(BASE_DIR, "templates.json")
ROLE_CONFIG_FILE = os.path.join(BASE_DIR, "role_config.json")
ALIAS_FILE = os.path.join(BASE_DIR, "alias.json")


def default_buyer_state():
    return {
        "buyers": [],
        "completion_pinged": False,
        "ready_prompt_sent": False,
        "active_message_id": None,
        "paused_channel_ids": [],
        "buyer_role_name": ORG_BUYER_ROLE_NAME,
        "template_name": None,
        "start_role_id": None,
        "incense_completion_pinged": False,
        "bypassed_phases": [],
        "field_role_ids": {},
        "start_ping_role_id": None,
    }


def default_incense_state():
    return {
        "paused_channel_ids": [],
        "bought_channels": [],
    }


def default_buyer_entries():
    return [
        {
            "category": "Rares",
            "price": "300k",
            "claimed_user": None,
            "reserve": [],
            "tracked_purchase_channels": [],
            "max_channels": 30,
        },
        {
            "category": "Regionals",
            "price": "200k",
            "claimed_user": None,
            "reserve": [],
            "tracked_purchase_channels": [],
            "max_channels": 20,
        },
        {
            "category": "Gigantamax",
            "price": "150k",
            "claimed_user": None,
            "reserve": [],
            "tracked_purchase_channels": [],
            "max_channels": 15,
        },
        {
            "category": "Eeveelutions",
            "price": "150k",
            "claimed_user": None,
            "reserve": [],
            "tracked_purchase_channels": [],
            "max_channels": 15,
        },
        {
            "category": "Reserve-1",
            "price": "50k",
            "claimed_user": None,
            "reserve": [],
            "tracked_purchase_channels": [],
            "max_channels": 5,
        },
        {
            "category": "Reserve-2",
            "price": "50k",
            "claimed_user": None,
            "reserve": [],
            "tracked_purchase_channels": [],
            "max_channels": 5,
        },
        {
            "category": "Reserve-3",
            "price": "50k",
            "claimed_user": None,
            "reserve": [],
            "tracked_purchase_channels": [],
            "max_channels": 5,
        },
        {
            "category": "Reserve-4",
            "price": "50k",
            "claimed_user": None,
            "reserve": [],
            "tracked_purchase_channels": [],
            "max_channels": 5,
        },
        {
            "category": "Pokopia Ditto",
            "price": "500k",
            "claimed_user": None,
            "reserve": [],
            "tracked_purchase_channels": [],
            "max_channels": 0,
        },
    ]


def load_templates():
    if os.path.exists(TEMPLATES_FILE):
        with open(TEMPLATES_FILE, "r") as f:
            return json.load(f)
    return {}


def load_role_config():
    if os.path.exists(ROLE_CONFIG_FILE):
        with open(ROLE_CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    return {"field_role_ids": {}, "start_ping_role_id": None}


def save_role_config(data):
    with open(ROLE_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def save_templates(templates):
    with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
        json.dump(templates, f, indent=2)


def ensure_default_buyers(buyers_data, template_id=None):
    if not buyers_data.get("buyers"):
        templates = load_templates()
        template_data = templates.get(template_id)
        if template_data:
            new_buyers = []
            for b in template_data.get("buyers", []):
                allowed_channels = b.get("allowed_channels", [])
                channel_range = b.get("channel_range")
                if channel_range and len(channel_range) == 2:
                    start, end = channel_range[0], channel_range[1]
                    for i in range(start, end + 1):
                        allowed_channels.append(f"incense-{i}")

                new_buyers.append({
                    "category": b.get("category"),
                    "price": b.get("price"),
                    "claimed_user": None,
                    "reserve": [],
                    "tracked_purchase_channels": [],
                    "max_channels": b.get("max_channels", 0),
                    "max_reserves": b.get("max_reserves", 0),
                    "allowed_channels": allowed_channels,
                })
            buyers_data["buyers"] = new_buyers
            buyers_data["buyer_role_name"] = template_data.get("buyer_role_name", ORG_BUYER_ROLE_NAME)
            buyers_data["template_name"] = template_data.get("name", template_id)
        else:
            buyers_data["buyers"] = default_buyer_entries()
            buyers_data["buyer_role_name"] = ORG_BUYER_ROLE_NAME
            buyers_data["template_name"] = "Default"

        buyers_data["completion_pinged"] = False
        buyers_data["incense_completion_pinged"] = False
        buyers_data["bypassed_phases"] = []
        buyers_data["active_message_id"] = None
        buyers_data["paused_channel_ids"] = []
        role_config = load_role_config()
        buyers_data["field_role_ids"] = role_config.get("field_role_ids", {})
        buyers_data["start_ping_role_id"] = role_config.get("start_ping_role_id")
        return True
    return False


def ensure_tracker_state(buyers_data):
    if "buyers" not in buyers_data:
        buyers_data["buyers"] = []
    if "completion_pinged" not in buyers_data:
        buyers_data["completion_pinged"] = False
    if "ready_prompt_sent" not in buyers_data:
        buyers_data["ready_prompt_sent"] = False
    if "active_message_id" not in buyers_data:
        buyers_data["active_message_id"] = None
    if "paused_channel_ids" not in buyers_data or not isinstance(buyers_data.get("paused_channel_ids"), list):
        buyers_data["paused_channel_ids"] = []
    if "buyer_role_name" not in buyers_data:
        buyers_data["buyer_role_name"] = ORG_BUYER_ROLE_NAME
    if "template_name" not in buyers_data:
        buyers_data["template_name"] = "Default"
    if "start_role_id" not in buyers_data:
        buyers_data["start_role_id"] = None
    if "incense_completion_pinged" not in buyers_data:
        buyers_data["incense_completion_pinged"] = False
    if "bypassed_phases" not in buyers_data or not isinstance(buyers_data.get("bypassed_phases"), list):
        buyers_data["bypassed_phases"] = []
    if "field_role_ids" not in buyers_data or not isinstance(buyers_data.get("field_role_ids"), dict):
        buyers_data["field_role_ids"] = {}
    if "start_ping_role_id" not in buyers_data:
        buyers_data["start_ping_role_id"] = None


def ensure_incense_state(incense_data):
    if "paused_channel_ids" not in incense_data or not isinstance(incense_data.get("paused_channel_ids"), list):
        incense_data["paused_channel_ids"] = []
    if "bought_channels" not in incense_data or not isinstance(incense_data.get("bought_channels"), list):
        incense_data["bought_channels"] = []


def add_paused_channel_id(buyers_data, channel_id):
    paused_channel_ids = buyers_data.get("paused_channel_ids", [])
    if not isinstance(paused_channel_ids, list):
        paused_channel_ids = []

    if channel_id not in paused_channel_ids:
        paused_channel_ids.append(channel_id)
    buyers_data["paused_channel_ids"] = paused_channel_ids


def remove_paused_channel_id(buyers_data, channel_id):
    paused_channel_ids = buyers_data.get("paused_channel_ids", [])
    if not isinstance(paused_channel_ids, list):
        paused_channel_ids = []

    buyers_data["paused_channel_ids"] = [
        paused_channel_id for paused_channel_id in paused_channel_ids if paused_channel_id != channel_id
    ]


def add_incense_channel_id(incense_data, channel_id):
    paused_channel_ids = incense_data.get("paused_channel_ids", [])
    if not isinstance(paused_channel_ids, list):
        paused_channel_ids = []

    if channel_id not in paused_channel_ids:
        paused_channel_ids.append(channel_id)
    incense_data["paused_channel_ids"] = paused_channel_ids


def remove_incense_channel_id(incense_data, channel_id):
    paused_channel_ids = incense_data.get("paused_channel_ids", [])
    if not isinstance(paused_channel_ids, list):
        paused_channel_ids = []

    incense_data["paused_channel_ids"] = [
        paused_channel_id for paused_channel_id in paused_channel_ids if paused_channel_id != channel_id
    ]


def add_bought_channel_name(incense_data, channel_name):
    bought_channels = incense_data.get("bought_channels", [])
    if not isinstance(bought_channels, list):
        bought_channels = []

    normalized_name = normalize_incense_channel_name(channel_name)
    if normalized_name is None:
        return

    if normalized_name not in bought_channels:
        bought_channels.append(normalized_name)
    incense_data["bought_channels"] = sorted(
        bought_channels,
        key=lambda name: int(name.split("-")[1]),
    )


def normalize_incense_channel_name(channel_name):
    name = (channel_name or "").strip().lower()
    if not name.startswith("incense-"):
        return None

    number_part = name.replace("incense-", "", 1)
    if not number_part.isdigit():
        return None

    channel_number = int(number_part)
    if channel_number < 1 or channel_number > 500:
        return None

    return f"incense-{channel_number}"


def normalize_pokemon_name(name):
    normalized = (name or "").strip().lower().replace("-", " ")
    return " ".join(normalized.split())


def build_forms_indexes(forms_data):
    base_to_forms = {}
    form_to_base = {}

    for base_name, form_list in forms_data.items():
        normalized_base = normalize_pokemon_name(base_name)
        if not normalized_base:
            continue

        normalized_forms = set()
        if isinstance(form_list, list):
            for form_name in form_list:
                normalized_form = normalize_pokemon_name(form_name)
                if not normalized_form:
                    continue
                normalized_forms.add(normalized_form)
                form_to_base[normalized_form] = normalized_base

        base_to_forms[normalized_base] = normalized_forms

    return base_to_forms, form_to_base


def parse_reserve_rules_text(text):
    parsed_rules = {}

    for raw_line in (text or "").splitlines():
        if ":" not in raw_line:
            continue

        category, raw_values = raw_line.split(":", 1)
        normalized_category = normalize_pokemon_name(category)
        if not normalized_category:
            continue

        values = []
        for value in raw_values.split(","):
            normalized_value = normalize_pokemon_name(value)
            if normalized_value:
                values.append(normalized_value)

        parsed_rules[normalized_category] = values

    return parsed_rules


def build_bought_embed(page_index, bought_channels, guild):
    channels_per_page = 25
    all_channels = [f"incense-{idx}" for idx in range(1, 501)]
    total_pages = (len(all_channels) + channels_per_page - 1) // channels_per_page

    page_index = max(0, min(page_index, total_pages - 1))
    start_idx = page_index * channels_per_page
    end_idx = min(start_idx + channels_per_page, len(all_channels))
    page_channels = all_channels[start_idx:end_idx]

    bought_set = {
        normalize_incense_channel_name(name)
        for name in bought_channels
        if isinstance(name, str)
    }
    bought_set.discard(None)

    lines = []
    for channel_name in page_channels:
        status_icon = "🟢" if channel_name in bought_set else "🔴"
        resolved_channel = discord.utils.get(guild.text_channels, name=channel_name) if guild else None
        channel_ref = resolved_channel.mention if resolved_channel else f"#{channel_name}"
        lines.append(f"{status_icon} {channel_ref}")

    embed = discord.Embed(
        title="Incense Bought Tracker",
        description="\n".join(lines),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text=f"Page {page_index + 1}/{total_pages} • Green = Bought • Red = Not bought")
    return embed, total_pages


class BoughtPaginationView(ui.View):
    def __init__(self, cog, bought_channels, author_id, guild):
        super().__init__(timeout=180)
        self.cog = cog
        self.bought_channels = bought_channels
        self.author_id = author_id
        self.guild = guild
        self.page_index = 0
        self.total_pages = 1
        self._sync_buttons()

    def _sync_buttons(self):
        self.prev_button.disabled = self.page_index <= 0
        self.next_button.disabled = self.page_index >= self.total_pages - 1

    async def _refresh(self, interaction):
        embed, total_pages = build_bought_embed(self.page_index, self.bought_channels, self.guild)
        self.total_pages = total_pages
        self._sync_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    async def interaction_check(self, interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ You can only control your own bought tracker view.", ephemeral=True)
            return False
        return True

    @ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction, button):
        if self.page_index > 0:
            self.page_index -= 1
        await self._refresh(interaction)

    @ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction, button):
        if self.page_index < self.total_pages - 1:
            self.page_index += 1
        await self._refresh(interaction)


def get_reserve_slots(category, buyer=None):
    if buyer is not None:
        configured_slots = buyer.get("max_reserves")
        if isinstance(configured_slots, int) and configured_slots >= 0:
            return configured_slots
    return max(1, RESERVE_SLOTS_BY_CATEGORY.get(category, 1))


def get_reserve_list(buyer):
    reserve_value = buyer.get("reserve", [])
    if isinstance(reserve_value, list):
        return [name.strip() for name in reserve_value if isinstance(name, str) and name.strip()]
    if isinstance(reserve_value, str) and reserve_value.strip():
        return [reserve_value.strip()]
    return []


def format_pokemon_display_name(normalized_or_raw_name):
    """Return a title-cased display name from a normalized or raw name."""
    if not normalized_or_raw_name:
        return ""
    name = (normalized_or_raw_name or "").strip()
    # strip any leading 'all ' prefix for base name formatting
    if name.lower().startswith("all "):
        name = name[4:].strip()

    # Title-case each word (e.g., 'mr mime' -> 'Mr Mime')
    parts = [part.capitalize() for part in name.split()]
    return " ".join(parts)


def format_reserve_display(reserve_value):
    """Format stored reserve value for display.

    - If value starts with 'all ', show 'All <Pokemon>' with title-casing.
    - Otherwise title-case the value.
    """
    if not reserve_value or not isinstance(reserve_value, str):
        return ""
    val = reserve_value.strip()
    if val.lower().startswith("all "):
        name = val[4:].strip()
        display_name = format_pokemon_display_name(name)
        return f"All {display_name}"
    return format_pokemon_display_name(val)


def buyer_has_reserve(buyer):
    return bool(get_reserve_list(buyer))


def get_claimed_spots_for_user(buyers_data, user_id):
    return [buyer for buyer in buyers_data.get("buyers", []) if buyer.get("claimed_user") == user_id]


def get_open_reserve_spots_for_user(buyers_data, user_id):
    return [buyer for buyer in get_claimed_spots_for_user(buyers_data, user_id) if not buyer_has_reserve(buyer)]


def get_locked_reserve_spots_for_user(buyers_data, user_id):
    return [buyer for buyer in get_claimed_spots_for_user(buyers_data, user_id) if buyer_has_reserve(buyer)]


def get_purchase_channel_count(buyer):
    tracked_channels = buyer.get("tracked_purchase_channels", [])
    if isinstance(tracked_channels, list):
        return len({channel_name for channel_name in tracked_channels if isinstance(channel_name, str) and channel_name.strip()})
    return 0


def get_purchase_channel_limit(buyer):
    return buyer.get("max_channels", 0)


def get_buyer_role_name_candidates(category):
    base = (category or "").strip()
    if not base:
        return []

    candidates = []
    candidates.extend(BUYER_ROLE_NAME_ALIASES.get(base, []))
    candidates.append(f"{base} Buyer")
    if base.endswith("s"):
        candidates.append(f"{base[:-1]} Buyer")
    else:
        candidates.append(f"{base}s Buyer")
    candidates.append(f"{base.replace('&', 'and').strip()} Buyer")

    deduped = []
    seen = set()
    for candidate in candidates:
        normalized = candidate.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped.append(candidate.strip())
    return deduped


def find_role_by_names(guild, candidate_names):
    role_by_name = {role.name.lower(): role for role in guild.roles}
    for candidate_name in candidate_names:
        role = role_by_name.get(candidate_name.lower())
        if role is not None:
            return role
    return None


def get_buyer_role_mentions(guild, buyers_data):
    role_mentions = []
    seen_role_ids = set()
    missing_role_names = []
    blocked_role_names = []
    me = guild.me
    can_force_role_ping = bool(me and me.guild_permissions.mention_everyone)

    for buyer in buyers_data.get("buyers", []):
        category = buyer.get("category", "")
        role_id = buyers_data.get("field_role_ids", {}).get(category)
        role = guild.get_role(role_id) if role_id else None
        candidate_names = get_buyer_role_name_candidates(category)
        if role is None and candidate_names:
            role = find_role_by_names(guild, candidate_names)
        if role is None:
            missing_role_names.append(category)
            continue
        if not role.mentionable and not can_force_role_ping:
            blocked_role_names.append(role.name)
            continue
        if role.id not in seen_role_ids:
            seen_role_ids.add(role.id)
            role_mentions.append(role.mention)

    return " ".join(role_mentions), missing_role_names, blocked_role_names


def get_buyer_by_category(buyers_data, category):
    for buyer in buyers_data["buyers"]:
        if buyer["category"] == category:
            return buyer
    return None


def get_category_for_purchase_channel(buyers_data, channel_name):
    normalized = (channel_name or "").strip().lower()
    for buyer in buyers_data.get("buyers", []):
        category = buyer.get("category")
        allowed_channels = buyer.get("allowed_channels", [])
        if normalized in allowed_channels:
            return category
    # Fallback to the old hardcoded CATEGORY_TRACKED_CHANNEL_NAMES
    for category, channel_names in CATEGORY_TRACKED_CHANNEL_NAMES.items():
        if normalized in channel_names:
            return category
    return None


def get_tracked_channel_names(buyers_data):
    tracked_channels = set()
    has_template_channels = False

    for buyer in buyers_data.get("buyers", []):
        allowed_channels = buyer.get("allowed_channels", [])
        if not isinstance(allowed_channels, list):
            continue

        normalized_channels = {
            normalized
            for channel in allowed_channels
            if isinstance(channel, str)
            for normalized in [normalize_incense_channel_name(channel)]
            if normalized is not None
        }
        if normalized_channels:
            has_template_channels = True
            tracked_channels.update(normalized_channels)

    if has_template_channels:
        return tracked_channels

    for channel_names in CATEGORY_TRACKED_CHANNEL_NAMES.values():
        tracked_channels.update(channel_names)
    return {
        normalized
        for channel in tracked_channels
        for normalized in [normalize_incense_channel_name(channel)]
        if normalized is not None
    }


TEMPLATE_LINE_PATTERN = re.compile(
    r"^\s*(?P<category>.+?)\s*-\s*(?P<incense>\d+)\s+incense\s*-\s*"
    r"(?P<price>\S+)\s*-\s*(?P<max_reserves>\d+)\s*$",
    re.IGNORECASE,
)


def parse_template_message(content):
    buyers = []
    channel_start = 1
    total_incense = 0

    for line_number, raw_line in enumerate((content or "").splitlines(), start=1):
        if not raw_line.strip():
            continue

        match = TEMPLATE_LINE_PATTERN.match(raw_line)
        if match is None:
            raise ValueError(
                f"Line {line_number} is invalid. Use: Category - number incense - price - max reserves"
            )

        category = match.group("category").strip()
        incense = int(match.group("incense"))
        price = match.group("price").strip()
        max_reserves = int(match.group("max_reserves"))
        if not category or incense <= 0 or max_reserves < 0:
            raise ValueError(
                f"Line {line_number} must have a category, positive incense count, "
                "and non-negative max reserves."
            )

        channel_end = channel_start + incense - 1
        allowed_channels = [
            f"incense-{channel_number}"
            for channel_number in range(channel_start, channel_end + 1)
        ]
        buyers.append({
            "category": category,
            "price": price,
            "channel_range": [channel_start, channel_end],
            "max_channels": incense,
            "max_reserves": max_reserves,
            "allowed_channels": allowed_channels,
        })
        total_incense += incense
        channel_start = channel_end + 1

    if not buyers:
        raise ValueError("The replied message does not contain any template lines.")

    return {
        "name": f"{total_incense} Incense Template",
        "buyer_role_name": ORG_BUYER_ROLE_NAME,
        "buyers": buyers,
        "total_incense": total_incense,
    }


def all_spots_claimed(buyers_data):
    buyers = buyers_data.get("buyers", [])
    return bool(buyers) and all(buyer.get("claimed_user") for buyer in buyers)


def is_phase_bypassed(buyers_data, phase):
    return phase in buyers_data.get("bypassed_phases", [])


def assign_missing_spots_to_user(buyers_data, user_id):
    for buyer in buyers_data.get("buyers", []):
        if not buyer.get("claimed_user"):
            buyer["claimed_user"] = user_id
            buyer["reserve"] = []


def mark_tracked_channels_bought(buyers_data, incense_data):
    for channel_name in get_tracked_channel_names(buyers_data):
        add_bought_channel_name(incense_data, channel_name)


def all_tracked_channels_bought(buyers_data, incense_data):
    tracked_channels = get_tracked_channel_names(buyers_data)
    bought_channels = {
        normalized
        for channel in incense_data.get("bought_channels", [])
        for normalized in [normalize_incense_channel_name(channel)]
        if normalized is not None
    }
    return tracked_channels.issubset(bought_channels)


def build_reserve_start_messages(buyers_data):
    messages = []
    for buyer in buyers_data.get("buyers", []):
        user_id = buyer.get("claimed_user")
        category = str(buyer.get("category") or "").strip().lower()
        if not user_id or not category:
            continue

        reserves = get_reserve_list(buyer)
        if category.lower().startswith(("reserve", "reserves")):
            messages.extend(
                f"m!r a {reserve} <@{user_id}>"
                for reserve in reserves
            )
            continue

        if not reserves:
            messages.append(f"m!r a {category} <@{user_id}>")
            continue

        for reserve in reserves:
            messages.append(f"m!r a {category}, {reserve} <@{user_id}>")

    return messages


def get_round_buyer_role(guild, buyers_data):
    role_name = buyers_data.get("buyer_role_name", ORG_BUYER_ROLE_NAME)
    return discord.utils.find(
        lambda role: role.name.lower() == role_name.lower(),
        guild.roles,
    )


def build_completion_ping_text(buyers_data):
    unique_user_ids = []
    seen = set()

    for buyer in buyers_data.get("buyers", []):
        user_id = buyer.get("claimed_user")
        if user_id and user_id not in seen:
            seen.add(user_id)
            unique_user_ids.append(user_id)

    return " ".join(f"<@{user_id}>" for user_id in unique_user_ids)


def track_purchase_channel(buyers_data, category, channel_name):
    buyer = get_buyer_by_category(buyers_data, category)
    if not buyer:
        return False

    normalized_channel_name = (channel_name or "").strip().lower()
    if not normalized_channel_name:
        return False

    tracked_channels = buyer.get("tracked_purchase_channels")
    if not isinstance(tracked_channels, list):
        tracked_channels = []

    normalized_channels = {
        name.strip().lower()
        for name in tracked_channels
        if isinstance(name, str) and name.strip()
    }
    if normalized_channel_name in normalized_channels:
        buyer["tracked_purchase_channels"] = sorted(normalized_channels)
        return False

    normalized_channels.add(normalized_channel_name)
    buyer["tracked_purchase_channels"] = sorted(normalized_channels)
    return True


class ReserveModal(ui.Modal):
    def __init__(self, cog, category, source_message_id):
        super().__init__(title=f"{category} Reserve Setup")
        self.cog = cog
        self.category = category
        self.source_message_id = source_message_id
        self.reserve_inputs = []

        buyers_data = cog.load_buyers()
        buyer = get_buyer_by_category(buyers_data, category)
        reserve_slots = get_reserve_slots(category, buyer)
        for idx in range(reserve_slots):
            reserve_input = ui.TextInput(
                label=f"Reserve {idx + 1}",
                placeholder="Pokemon name (leave empty if none)",
                required=False,
                max_length=60,
            )
            self.reserve_inputs.append(reserve_input)
            self.add_item(reserve_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        buyers_data = self.cog.load_buyers()
        buyer = get_buyer_by_category(buyers_data, self.category)

        if not buyer:
            await interaction.followup.send("Category not found!", ephemeral=True)
            return

        if buyer["claimed_user"] and buyer["claimed_user"] != interaction.user.id:
            await interaction.followup.send(
                f"This spot is already claimed by <@{buyer['claimed_user']}>!",
                ephemeral=True,
            )
            return

        reserve_list = []
        for reserve_input in self.reserve_inputs:
            value = (reserve_input.value or "").strip()
            if value:
                reserve_list.append(value)

        buyer["claimed_user"] = interaction.user.id
        buyer["reserve"] = reserve_list
        self.cog.save_buyers(buyers_data)
        if interaction.guild is not None:
            await self.cog.add_round_buyer_role(
                interaction.guild,
                interaction.user.id,
                buyers_data,
            )

        source_message = await interaction.channel.fetch_message(self.source_message_id)
        organiser_mention = source_message.embeds[0].description.split("Organiser:- ")[1].strip()
        organiser_id = int(organiser_mention.replace("<@", "").replace("!", "").replace(">", ""))
        organiser_user = await self.cog.bot.fetch_user(organiser_id)

        new_embed = self.cog.create_organiser_embed(organiser_user, buyers_data)
        await source_message.edit(embed=new_embed, view=await self.cog.create_button_view(buyers_data))

        await self.cog.maybe_send_completion_ping(buyers_data)
        await self.cog.maybe_send_incense_completion_ping(
            buyers_data,
            self.cog.load_incense_state(),
        )
        await self.cog.maybe_send_ready_prompt(buyers_data)

        await interaction.followup.send(
            f"✅ You've claimed the {self.category} spot. Use o!r <pokemon_name> to add your reserve.",
            ephemeral=True,
        )


class ReserveSpotSelect(ui.Select):
    def __init__(self, view, options):
        super().__init__(
            placeholder="Choose the spot to set this reserve on",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        await self.view_ref.handle_selection(interaction, self.values[0])


class ReserveSpotSelectView(ui.View):
    def __init__(self, cog, requester_id, reserve_value, open_spots, locked_spots, form_to_base, base_to_forms):
        super().__init__(timeout=120)
        self.cog = cog
        self.requester_id = requester_id
        self.reserve_value = reserve_value
        self.form_to_base = form_to_base
        self.base_to_forms = base_to_forms
        self.open_spots = {buyer["category"]: buyer for buyer in open_spots}
        self.locked_spots = locked_spots

        options = [
            discord.SelectOption(label=buyer["category"], description=f"Set reserve for {buyer['category']}")
            for buyer in open_spots
        ]
        self.add_item(ReserveSpotSelect(self, options))

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message(
                "❌ You can only use this reserve selector for your own spots.",
                ephemeral=True,
            )
            return False
        return True

    async def handle_selection(self, interaction: discord.Interaction, category):
        buyers_data = self.cog.load_buyers()
        buyer = get_buyer_by_category(buyers_data, category)

        if not buyer or buyer.get("claimed_user") != self.requester_id:
            await interaction.response.send_message("❌ That spot is no longer available.", ephemeral=True)
            return

        if buyer_has_reserve(buyer):
            await interaction.response.send_message(
                "❌ This spot already has a reserve set and can't be changed again.",
                ephemeral=True,
            )
            return

        reserve_rules = self.cog.load_reserve_rules()

        # Determine normalized name to check against blocked lists
        rv_norm = normalize_pokemon_name(self.reserve_value)
        rv_check_name = rv_norm[4:].strip() if rv_norm.startswith("all ") else rv_norm
        if self.cog.is_blocked_reserve_name(rv_check_name, reserve_rules, self.form_to_base):
            await interaction.response.send_message("🚫 You cant add this pokemon as reserve.", ephemeral=True)
            return

        result_message = await self.cog.apply_reserve_to_buyer(
            buyers_data, buyer, self.form_to_base.get(rv_check_name, rv_check_name), self.form_to_base, self.base_to_forms, reserve_value_override=self.reserve_value
        )
        if result_message is None:
            await interaction.response.send_message("❌ Failed to set reserve for that spot.", ephemeral=True)
            return

        await interaction.response.edit_message(content=result_message, view=None)


class ClaimButton(ui.Button):
    def __init__(self, cog, category, row, claimed=False):
        style = discord.ButtonStyle.secondary if claimed else discord.ButtonStyle.blurple
        super().__init__(label=category, style=style, custom_id=f"claim_{category}", row=row, disabled=claimed)
        self.cog = cog
        self.category = category

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        buyers_data = self.cog.load_buyers()
        buyer = get_buyer_by_category(buyers_data, self.category)

        if not buyer:
            await interaction.followup.send("Category not found!", ephemeral=True)
            return

        if buyer["claimed_user"]:
            await interaction.followup.send(
                f"This spot is already claimed by <@{buyer['claimed_user']}>!",
                ephemeral=True,
            )
            return

        now = time.time()
        cooldown_until = self.cog.claim_cooldowns.get(interaction.user.id, 0)
        if cooldown_until > now:
            seconds_left = max(1, int(cooldown_until - now))
            await interaction.followup.send(
                f"⏳ Please wait {seconds_left}s before claiming another spot.",
                ephemeral=True,
            )
            return

        buyer["claimed_user"] = interaction.user.id
        buyer["reserve"] = []
        self.cog.save_buyers(buyers_data)
        self.cog.claim_cooldowns[interaction.user.id] = now + 15

        role_message = ""
        if interaction.guild is not None:
            role_name = buyers_data.get("buyer_role_name", ORG_BUYER_ROLE_NAME)
            if not await self.cog.add_round_buyer_role(
                interaction.guild,
                interaction.user.id,
                buyers_data,
            ):
                role_message = f"\n⚠️ Claimed spot, but failed to assign {role_name} role."

        source_message = interaction.message
        if source_message and source_message.embeds:
            description = source_message.embeds[0].description or ""
            if "Organiser:- " in description:
                organiser_mention = description.split("Organiser:- ")[1].strip()
                organiser_id = int(organiser_mention.replace("<@", "").replace("!", "").replace(">", ""))
                organiser_user = await self.cog.bot.fetch_user(organiser_id)
                new_embed = self.cog.create_organiser_embed(organiser_user, buyers_data)
                await source_message.edit(embed=new_embed, view=await self.cog.create_button_view(buyers_data))

        await self.cog.maybe_send_completion_ping(buyers_data)
        await self.cog.maybe_send_incense_completion_ping(
            buyers_data,
            self.cog.load_incense_state(),
        )
        await self.cog.maybe_send_ready_prompt(buyers_data)

        dm_message = None
        try:
            release_view = ReleaseClaimView(self.cog, self.category, interaction.user.id)
            dm_message = await interaction.user.send(
                content=(
                    f"You have claimed {self.category} in Sadellite Sphagetti.\n\n"
                    "Click the Button Below if you wanna release the spot."
                ),
                view=release_view,
            )
            release_view.message = dm_message
        except discord.Forbidden:
            role_message += "\n⚠️ I couldn\'t DM you the release button."
        except discord.HTTPException:
            role_message += "\n⚠️ I couldn\'t send the release DM right now."

        await interaction.followup.send(
            f"✅ You've claimed the {self.category} spot.{role_message}. **Use o!r <name> to reserve a pokemon.**",
            ephemeral=True,
        )


class ReleaseClaimButton(ui.Button):
    def __init__(self, view):
        custom_id = f"release_claim_{view.category.lower().replace(' ', '_')}_{view.requester_id}"
        super().__init__(label="Release", style=discord.ButtonStyle.danger, custom_id=custom_id)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        await self.view_ref.handle_release(interaction)


class ReleaseClaimView(ui.View):
    def __init__(self, cog, category, requester_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.category = category
        self.requester_id = requester_id
        self.message = None
        self.add_item(ReleaseClaimButton(self))

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message(
                "❌ Only the buyer who claimed this spot can release it.",
                ephemeral=True,
            )
            return False
        return True

    async def handle_release(self, interaction: discord.Interaction):
        buyers_data = self.cog.load_buyers()
        buyer = get_buyer_by_category(buyers_data, self.category)

        if not buyer or buyer.get("claimed_user") != self.requester_id:
            await interaction.response.send_message("❌ This spot is no longer claimed by you.", ephemeral=True)
            return

        buyer["claimed_user"] = None
        buyer["reserve"] = []
        buyers_data["ready_prompt_sent"] = False
        self.cog.save_buyers(buyers_data)

        if not get_claimed_spots_for_user(buyers_data, self.requester_id):
            await self.cog.remove_round_buyer_role(
                self.requester_id,
                buyers_data,
                interaction.guild,
            )

        await self.cog.refresh_active_organiser_message(buyers_data)

        if self.message is not None:
            try:
                await self.message.edit(content=f"✅ You released {self.category} in Sadellite Sphagetti.", view=None)
            except Exception:
                pass

        await interaction.response.send_message("✅ Spot released.", ephemeral=True)


def get_template_categories():
    categories = []
    seen = set()
    for template in load_templates().values():
        for buyer in template.get("buyers", []):
            category = str(buyer.get("category") or "").strip()
            normalized = category.casefold()
            if category and normalized not in seen:
                seen.add(normalized)
                categories.append(category)
    return categories


class RoleFieldSelect(ui.Select):
    def __init__(self, view, categories):
        options = [
            discord.SelectOption(
                label=category[:100],
                description=f"Choose the role for {category}"[:100],
            )
            for category in categories
        ]
        super().__init__(
            placeholder="Select a buyer field to configure",
            options=options,
            min_values=1,
            max_values=1,
            row=0,
        )
        self.view_ref = view

    async def callback(self, interaction):
        self.view_ref.selected_category = self.values[0]
        await interaction.response.send_message(
            f"✅ Selected `{self.values[0]}`. Now choose its role below.",
            ephemeral=True,
        )


class RoleValueSelect(ui.RoleSelect):
    def __init__(self, view):
        super().__init__(
            placeholder="Choose the role for the selected field",
            min_values=1,
            max_values=1,
            row=1,
        )
        self.view_ref = view

    async def callback(self, interaction):
        category = self.view_ref.selected_category
        if not category:
            await interaction.response.send_message(
                "❌ Select a buyer field first.",
                ephemeral=True,
            )
            return

        role = self.values[0]
        config = load_role_config()
        field_role_ids = config.setdefault("field_role_ids", {})
        field_role_ids[category] = role.id
        save_role_config(config)
        await interaction.response.send_message(
            f"✅ `{category}` will use {role.mention} for buyer pings.",
            ephemeral=True,
        )
        await self.view_ref.refresh_message(interaction)


class StartPingRoleSelect(ui.RoleSelect):
    def __init__(self, view):
        super().__init__(
            placeholder="Choose the Organise Start Ping role",
            min_values=1,
            max_values=1,
            row=2,
        )
        self.view_ref = view

    async def callback(self, interaction):
        role = self.values[0]
        config = load_role_config()
        config["start_ping_role_id"] = role.id
        save_role_config(config)
        await interaction.response.send_message(
            f"✅ Organise Start Ping role set to {role.mention}.",
            ephemeral=True,
        )
        await self.view_ref.refresh_message(interaction)


class RoleAssignmentView(ui.View):
    def __init__(self, cog, categories):
        super().__init__(timeout=900)
        self.cog = cog
        self.selected_category = None
        self.message = None
        self.add_item(RoleFieldSelect(self, categories))
        self.add_item(RoleValueSelect(self))
        self.add_item(StartPingRoleSelect(self))

    async def refresh_message(self, interaction):
        if self.message is None:
            return
        await self.message.edit(embed=self.cog.build_role_assignment_embed(), view=self)


class OrganiseBaseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.claim_cooldowns = {}

    async def add_round_buyer_role(self, guild, user_id, buyers_data):
        role = get_round_buyer_role(guild, buyers_data)
        member = guild.get_member(user_id)
        if role is None or member is None:
            return False
        if role in member.roles:
            return True

        try:
            await member.add_roles(role, reason="Claimed organiser buyer spot")
            return True
        except (discord.Forbidden, discord.HTTPException):
            return False

    async def remove_round_buyer_role(self, user_id, buyers_data, preferred_guild=None):
        guilds = []
        if preferred_guild is not None:
            guilds.append(preferred_guild)
        guilds.extend(guild for guild in self.bot.guilds if guild not in guilds)

        removed = False
        for guild in guilds:
            role = get_round_buyer_role(guild, buyers_data)
            member = guild.get_member(user_id)
            if role is None or member is None or role not in member.roles:
                continue
            try:
                await member.remove_roles(role, reason="Released organiser buyer spot")
                removed = True
            except (discord.Forbidden, discord.HTTPException):
                continue
        return removed

    def can_use_reserve_command(self, user):
        if user.guild_permissions.administrator:
            return True

        buyers_data = self.load_buyers()
        buyer_role_name = buyers_data.get("buyer_role_name", ORG_BUYER_ROLE_NAME)

        for role in user.roles:
            if role.id == RESERVE_ACCESS_ROLE_ID:
                return True
            if role.name.lower() == buyer_role_name.lower():
                return True

        return False

    def load_buyers(self):
        if os.path.exists(BUYER_FILE):
            with open(BUYER_FILE, "r") as f:
                data = json.load(f)
                ensure_tracker_state(data)
                return data
        return default_buyer_state()

    def save_buyers(self, data):
        with open(BUYER_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def load_incense_state(self):
        if os.path.exists(INCENSE_FILE):
            with open(INCENSE_FILE, "r") as f:
                data = json.load(f)
                ensure_incense_state(data)
                return data
        return default_incense_state()

    def save_incense_state(self, data):
        with open(INCENSE_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def load_class_names(self):
        if not os.path.exists(CLASS_FILE):
            return set()

        with open(CLASS_FILE, "r") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return set()

        return {normalize_pokemon_name(name) for name in data.keys() if isinstance(name, str)}

    def load_aliases(self):
        if not os.path.exists(ALIAS_FILE):
            return {}
        with open(ALIAS_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return {}
        
        reverse_aliases = {}
        for primary, aliases in data.items():
            primary_norm = normalize_pokemon_name(primary)
            if primary_norm:
                for alias in aliases:
                    alias_norm = normalize_pokemon_name(alias)
                    if alias_norm:
                        reverse_aliases[alias_norm] = primary_norm
                reverse_aliases[primary_norm] = primary_norm
        return reverse_aliases

    def load_forms_data(self):
        if not os.path.exists(FORMS_FILE):
            return {}

        with open(FORMS_FILE, "r") as f:
            data = json.load(f)

        return data if isinstance(data, dict) else {}

    def load_reserve_rules(self):
        parsed_rules = {}

        if os.path.exists(RESERVE_RULES_SOURCE_FILE):
            with open(RESERVE_RULES_SOURCE_FILE, "r", encoding="utf-8") as f:
                parsed_rules = parse_reserve_rules_text(f.read())

            with open(RESERVE_RULES_FILE, "w", encoding="utf-8") as f:
                json.dump(parsed_rules, f, indent=2)
        elif os.path.exists(RESERVE_RULES_FILE):
            with open(RESERVE_RULES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    parsed_rules = data

        return parsed_rules

    def load_special_category_names(self):
        category_files = {
            "rare": (RARE_FILE, "rares"),
            "regional": (REGIONAL_FILE, "regionals"),
            "eeveelutions": (EEVEELUTIONS_PARADOX_FILE, "eeveelutions_paradox"),
            "paradox": (EEVEELUTIONS_PARADOX_FILE, "paradox"),
            "gigantamax": (GIGANTAMAX_FILE, "gigantamax"),
        }
        category_names = set()

        for file_path, category_key in category_files.values():
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            values = data.get(category_key, []) if isinstance(data, dict) else []
            if not isinstance(values, list):
                raise ValueError(f"{file_path} must contain a list under '{category_key}'")

            category_names.update(
                normalize_pokemon_name(value)
                for value in values
                if isinstance(value, str) and normalize_pokemon_name(value)
            )

        return category_names

    def is_blocked_reserve_name(self, normalized_name, reserve_rules, form_to_base):
        blocked_names = self.load_special_category_names()

        if normalized_name in blocked_names:
            return True
            
        request_base = form_to_base.get(normalized_name, normalized_name)
        if request_base != normalized_name and request_base in blocked_names:
            return True
            
        return False

    async def apply_reserve_to_buyer(self, buyers_data, buyer, target_base, form_to_base, base_to_forms=None, reserve_value_override=None):
        if buyer_has_reserve(buyer):
            return None

        rv_norm = normalize_pokemon_name(reserve_value_override) if reserve_value_override else ""
        rv_is_all = rv_norm.startswith("all ") if rv_norm else False
        rv_is_normal = rv_norm.startswith("normal ") if rv_norm else False
        
        if rv_norm:
            if rv_is_all:
                rv_target = rv_norm[4:].strip()
            elif rv_is_normal:
                rv_target = rv_norm[7:].strip()
            else:
                rv_target = rv_norm
        else:
            rv_target = target_base
            
        reserve_base = form_to_base.get(rv_target, rv_target)

        if base_to_forms is None:
            forms_data = self.load_forms_data()
            base_to_forms, _ = build_forms_indexes(forms_data)

        forms_for_base = base_to_forms.get(reserve_base, set())
        has_multiple_forms = bool(forms_for_base)

        if rv_is_all or (not reserve_value_override and has_multiple_forms):
            forms_to_check = [reserve_base] + list(forms_for_base)
        else:
            forms_to_check = [rv_target]

        reserve_rules = self.load_reserve_rules()

        taken_forms = set()
        for other_buyer in buyers_data.get("buyers", []):
            if other_buyer is buyer:
                continue
            for res in get_reserve_list(other_buyer):
                res_norm = normalize_pokemon_name(res)
                if res_norm:
                    taken_forms.add(res_norm)
                    if res_norm.startswith("all "):
                        res_base = res_norm[4:].strip()
                        taken_forms.add(res_base)
                        for f in base_to_forms.get(res_base, set()):
                            taken_forms.add(f)

        final_reserves = []
        for form in forms_to_check:
            if self.is_blocked_reserve_name(form, reserve_rules, form_to_base):
                continue
            if form in taken_forms:
                continue
            final_reserves.append(form)

        if not final_reserves:
            return "🚫 All requested forms are either blocked or already reserved by others."

        buyer["reserve"] = final_reserves
        self.save_buyers(buyers_data)

        await self.refresh_active_organiser_message(buyers_data)
        await self.maybe_send_ready_prompt(buyers_data)
        
        display_items = [format_reserve_display(r) for r in final_reserves]
        if len(display_items) > 4:
            display = ", ".join(display_items[:4]) + f" +{len(display_items)-4}....."
        else:
            display = ", ".join(display_items)
            
        return f"***✅ Reserve set for {buyer['category']}: {display}***. Use **o!r remove <name>** to remove reserve."

    async def resolve_channel(self, channel_id):
        channel = self.bot.get_channel(channel_id)
        if channel is not None:
            return channel

        try:
            return await self.bot.fetch_channel(channel_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    async def get_active_organiser_message(self, buyers_data):
        active_message_id = buyers_data.get("active_message_id")
        if not active_message_id:
            return None

        channel = await self.resolve_channel(TARGET_CHANNEL_ID)
        if channel is None:
            return None

        try:
            return await channel.fetch_message(active_message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    def has_permission(self, user, guild):
        if user.guild_permissions.administrator:
            return True

        buyers_data = self.load_buyers()
        start_role_id = buyers_data.get("start_role_id")
        for role in user.roles:
            if (
                role.name == "Organiser"
                or role.permissions.administrator
                or (start_role_id and role.id == start_role_id)
            ):
                return True

        return False

    def create_organiser_embed(self, organiser_user, buyers_data):
        title = buyers_data.get("template_name", "100 Incense Org")
        embed = discord.Embed(
            title=title,
            description=f"Click button below to claim a spot in the incense round\n\nOrganiser:- {organiser_user.mention}",
            color=discord.Color.green(),
        )

        for buyer in buyers_data["buyers"]:
            claimed = buyer["claimed_user"]
            claimed_text = f"<@{claimed}>" if claimed else "Available"
            reserve_list = get_reserve_list(buyer)
            reserve_items = [format_reserve_display(rv) for rv in reserve_list]
            
            if len(reserve_items) > 4:
                reserve_text = ", ".join(reserve_items[:4]) + f" +{len(reserve_items)-4}....."
            else:
                reserve_text = ", ".join(reserve_items) if reserve_items else "None"
            
            channel_count = get_purchase_channel_count(buyer)
            channel_limit = get_purchase_channel_limit(buyer)

            field_name = f"➤ **{buyer['category']} • {buyer['price']}**"
            field_value = (
                f"{claimed_text}\n"
                f"Reserve :- {reserve_text}\n"
                f"Channels :- {channel_count}/{channel_limit}"
            )

            embed.add_field(name=field_name, value=field_value, inline=False)

        embed.set_footer(
            text="For any external requests regarding reserves, please inform the organiser."
        )
        return embed

    def build_role_assignment_embed(self):
        config = load_role_config()
        embed = discord.Embed(
            title="Organiser Role Configuration",
            description=(
                "Select a buyer field, then choose its role. "
                "The configured roles are pinged when all spots are claimed.\n\n"
                "**Organise Start Ping role** is used when a new organisation starts."
            ),
            color=discord.Color.blurple(),
        )
        start_role_id = config.get("start_ping_role_id")
        start_role_text = f"<@&{start_role_id}>" if start_role_id else "Not set"
        embed.add_field(name="Organise Start Ping", value=start_role_text, inline=False)

        field_role_ids = config.get("field_role_ids", {})
        for category in get_template_categories():
            role_id = field_role_ids.get(category)
            role_text = f"<@&{role_id}>" if role_id else "Not set"
            embed.add_field(name=category, value=role_text, inline=True)

        embed.set_footer(text="Only administrators can change these roles.")
        return embed

    async def create_button_view(self, buyers_data):
        view = ui.View(timeout=3600)

        for i, buyer in enumerate(buyers_data["buyers"]):
            row = i // 5
            button = ClaimButton(self, buyer["category"], row, claimed=bool(buyer.get("claimed_user")))
            view.add_item(button)

        return view


    async def schedule_post_organise_checks(self, buyers_data):
        # Wait 5 minutes then ping buyer roles for remaining spots
        try:
            while True:
                await asyncio.sleep(300)
                buyers_data = self.load_buyers()
                
                if not buyers_data.get("active_message_id") or all_spots_claimed(buyers_data):
                    break

                channel = await self.resolve_channel(TARGET_CHANNEL_ID)
                if channel is None or channel.guild is None:
                    return

                remaining = [b["category"] for b in buyers_data.get("buyers", []) if not b.get("claimed_user")]
                if remaining:
                    # collect role mentions for remaining categories
                    mentions = []
                    seen_mentions = set()
                    for cat in remaining:
                        candidate_names = get_buyer_role_name_candidates(cat)
                        role = find_role_by_names(channel.guild, candidate_names)
                        if role is not None and role.mention not in seen_mentions:
                            seen_mentions.add(role.mention)
                            mentions.append(role.mention)

                    spots_text = " & ".join(remaining) if len(remaining) <= 2 else ", ".join(remaining[:-1]) + " & " + remaining[-1]
                    mention_text = " ".join(mentions) if mentions else ""
                    if len(remaining) == 1:
                        message_text = f"Hurry Up! {spots_text} is left. GRAB IT!"
                    else:
                        message_text = f"Hurry Up! {spots_text} are left. GRAB IT!"

                    await channel.send(f"{mention_text}\n{message_text}" if mention_text else message_text)

        except Exception:
            return


    async def maybe_send_ready_prompt(self, buyers_data):
        # Send a ready prompt when all spots claimed AND all tracked channels are bought
        try:
            if not all_spots_claimed(buyers_data):
                return

            incense_data = self.load_incense_state()
            bought = set(incense_data.get("bought_channels", []))
            # build set of tracked channels from mapping
            tracked_normalized = get_tracked_channel_names(buyers_data)

            if not tracked_normalized.issubset(bought):
                return

            # guard against duplicate ready prompts
            if buyers_data.get("ready_prompt_sent"):
                return

            # prepare allowed buyers
            buyer_ids = [b.get("claimed_user") for b in buyers_data.get("buyers", []) if b.get("claimed_user")]
            allowed = [uid for uid in buyer_ids if uid]

            # resolve target channel for ready prompt
            try:
                ready_channel = await self.resolve_channel(1489692846091927562)
            except Exception:
                ready_channel = None

            if ready_channel is None:
                return

            mention_text = " ".join(f"<@{uid}>" for uid in allowed)
            content = f"{mention_text}\nAre you ready? Click the Ready button below to confirm."

            view = ReadyView(self, allowed)
            sent = await ready_channel.send(content, view=view)
            # keep reference for timeout edit
            view.message = sent

            buyers_data["ready_prompt_sent"] = True
            self.save_buyers(buyers_data)

        except Exception:
            return


class ReadyButton(ui.Button):
    def __init__(self, view):
        super().__init__(label="Ready", style=discord.ButtonStyle.success)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id in self.view_ref.ready_users:
            await interaction.response.send_message("You already marked ready.", ephemeral=True)
            return
        self.view_ref.ready_users.add(interaction.user.id)
        await interaction.response.send_message("✅ Marked ready!", ephemeral=True)
        # update message to show ready users
        try:
            msg = interaction.message
            mentions = " ".join(f"<@{uid}>" for uid in sorted(self.view_ref.ready_users))
            await msg.edit(content=f"Ready list: {mentions}", view=self.view_ref)
        except Exception:
            pass


class ReadyView(ui.View):
    def __init__(self, cog, allowed_user_ids):
        super().__init__(timeout=900)
        self.cog = cog
        self.allowed = set(allowed_user_ids)
        self.ready_users = set()
        self.message = None
        self.add_item(ReadyButton(self))

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id not in self.allowed:
            await interaction.response.send_message("❌ Only buyers can mark ready.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        try:
            if self.message:
                mentions = " ".join(f"<@{uid}>" for uid in sorted(self.ready_users)) or "No one"
                await self.message.edit(content=f"Ready window closed. Ready list: {mentions}", view=None)
        except Exception:
            pass


class OrganiseCog(OrganiseBaseCog):
    def can_start(self, user, buyers_data):
        if user.guild_permissions.administrator:
            return True

        start_role_id = buyers_data.get("start_role_id")
        return bool(
            start_role_id
            and any(role.id == start_role_id for role in user.roles)
        )

    async def refresh_active_organiser_message(self, buyers_data):
        active_message_id = buyers_data.get("active_message_id")
        if not active_message_id:
            return

        channel = await self.resolve_channel(TARGET_CHANNEL_ID)
        if channel is None:
            return

        try:
            message = await channel.fetch_message(active_message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return

        if not message.embeds:
            return

        description = message.embeds[0].description or ""
        if "Organiser:- " not in description:
            return

        organiser_mention = description.split("Organiser:- ")[1].strip()
        organiser_id = int(organiser_mention.replace("<@", "").replace("!", "").replace(">", ""))
        organiser_user = await self.bot.fetch_user(organiser_id)

        await message.edit(embed=self.create_organiser_embed(organiser_user, buyers_data), view=await self.create_button_view(buyers_data))

    async def maybe_send_completion_ping(self, buyers_data, force=False):
        if buyers_data.get("completion_pinged"):
            return

        if not force and not all_spots_claimed(buyers_data):
            return

        target_channel = await self.resolve_channel(TARGET_CHANNEL_ID)
        if target_channel is None:
            return

        role_mentions, _, _ = get_buyer_role_mentions(target_channel.guild, buyers_data)
        message_text = (
            f"{role_mentions}\nAll spots are bought. Kindly buy your incense in your respective channels."
            if role_mentions
            else "All spots are bought. Kindly buy your incense in your respective channels."
        )

        await target_channel.send(
            message_text,
            allowed_mentions=discord.AllowedMentions(roles=bool(role_mentions)),
        )
        buyers_data["completion_pinged"] = True
        self.save_buyers(buyers_data)

    async def maybe_send_incense_completion_ping(self, buyers_data, incense_data, force=False):
        if buyers_data.get("incense_completion_pinged"):
            return
        if not force and not all_spots_claimed(buyers_data):
            return
        if not force and not all_tracked_channels_bought(buyers_data, incense_data):
            return

        active_message = await self.get_active_organiser_message(buyers_data)
        target_channel = await self.resolve_channel(TARGET_CHANNEL_ID)
        if active_message is None or target_channel is None or not active_message.embeds:
            return

        description = active_message.embeds[0].description or ""
        if "Organiser:- " not in description:
            return

        organiser_mention = description.split("Organiser:- ", 1)[1].strip()
        await target_channel.send(
            f"{organiser_mention}\nAll incense channels are bought. Start with reserves and the announcement, then continue the round with the incense.",
            allowed_mentions=discord.AllowedMentions(users=True),
        )
        buyers_data["incense_completion_pinged"] = True
        self.save_buyers(buyers_data)

    async def pause_channel_for_tracker(self, channel, incense_data, target_member):
        if not isinstance(channel, discord.abc.GuildChannel):
            return False

        if target_member is None:
            return False

        overwrite = channel.overwrites_for(target_member)
        overwrite.send_messages = False

        try:
            await channel.set_permissions(
                target_member,
                overwrite=overwrite,
                reason="Tracker auto-pause after incense purchase",
            )
        except (discord.Forbidden, discord.HTTPException):
            return False

        add_incense_channel_id(incense_data, channel.id)
        self.save_incense_state(incense_data)

        try:
            await channel.send("Incense Paused")
        except (discord.Forbidden, discord.HTTPException):
            pass

        return True

    async def set_tracker_send_permissions(self, channel, guild, enabled):
        tracker_member = await self.get_tracker_member(guild)
        if tracker_member is None:
            return False

        overwrite = channel.overwrites_for(tracker_member)
        overwrite.send_messages = enabled

        try:
            await channel.set_permissions(
                tracker_member,
                overwrite=overwrite,
                reason="Manual tracker pause/resume command",
            )
            return True
        except (discord.Forbidden, discord.HTTPException):
            return False

    async def pause_tracked_channels(self, ctx, incense_data):
        tracker_member = await self.get_tracker_member(ctx.guild)
        if tracker_member is None:
            await ctx.send("❌ Tracker member not found in this server.")
            return

        channel_ids = incense_data.get("paused_channel_ids", [])
        if not channel_ids:
            await ctx.send("ℹ️ No tracked incense channels are stored yet.")
            return

        paused_count = 0
        failed_count = 0

        for channel_id in list(dict.fromkeys(channel_ids)):
            channel = ctx.guild.get_channel(channel_id)
            if channel is None:
                try:
                    fetched = await self.bot.fetch_channel(channel_id)
                    channel = fetched if isinstance(fetched, discord.abc.GuildChannel) else None
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    channel = None

            if channel is None:
                failed_count += 1
                continue

            if await self.set_tracker_send_permissions(channel, ctx.guild, False):
                paused_count += 1
            else:
                failed_count += 1

        await ctx.send(
            f"✅ Paused {paused_count} tracked incense channel(s)." + (
                f" ⚠️ Failed in {failed_count} channel(s)." if failed_count else ""
            )
        )

    async def resume_tracked_channels(self, ctx, incense_data):
        tracker_member = await self.get_tracker_member(ctx.guild)
        if tracker_member is None:
            await ctx.send("❌ Tracker member not found in this server.")
            return

        channel_ids = incense_data.get("paused_channel_ids", [])
        if not channel_ids:
            await ctx.send("ℹ️ No tracked incense channels are paused.")
            return

        resumed_count = 0
        failed_count = 0
        remaining_channel_ids = []

        for channel_id in list(dict.fromkeys(channel_ids)):
            channel = ctx.guild.get_channel(channel_id)
            if channel is None:
                try:
                    fetched = await self.bot.fetch_channel(channel_id)
                    channel = fetched if isinstance(fetched, discord.abc.GuildChannel) else None
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    channel = None

            if channel is None:
                failed_count += 1
                remaining_channel_ids.append(channel_id)
                continue

            if await self.set_tracker_send_permissions(channel, ctx.guild, True):
                resumed_count += 1
            else:
                failed_count += 1
                remaining_channel_ids.append(channel_id)

        incense_data["paused_channel_ids"] = remaining_channel_ids
        self.save_incense_state(incense_data)

        await ctx.send(
            f"✅ Resumed {resumed_count} tracked incense channel(s)." + (
                f" ⚠️ Failed in {failed_count} channel(s)." if failed_count else ""
            )
        )

    async def get_tracker_member(self, guild):
        member = guild.get_member(PURCHASE_TRACKER_AUTHOR_ID)
        if member is not None:
            return member

        try:
            return await guild.fetch_member(PURCHASE_TRACKER_AUTHOR_ID)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot and message.author.id != PURCHASE_TRACKER_AUTHOR_ID:
            return

        if (
            message.guild is not None
            and message.author.id == PURCHASE_TRACKER_AUTHOR_ID
            and message.content.strip() == PURCHASE_TRACKER_MESSAGE
        ):
            channel_name = getattr(message.channel, "name", "")
            normalized_channel_name = normalize_incense_channel_name(channel_name)
            if normalized_channel_name is None:
                return

            incense_data = self.load_incense_state()
            add_incense_channel_id(incense_data, message.channel.id)
            add_bought_channel_name(incense_data, normalized_channel_name)
            self.save_incense_state(incense_data)

            tracker_member = await self.get_tracker_member(message.guild)
            if tracker_member is not None:
                await self.pause_channel_for_tracker(message.channel, incense_data, tracker_member)

            buyers_data = self.load_buyers()
            tracked_category = get_category_for_purchase_channel(buyers_data, channel_name)
            if tracked_category:
                if track_purchase_channel(buyers_data, tracked_category, channel_name):
                    self.save_buyers(buyers_data)
                    await self.refresh_active_organiser_message(buyers_data)
                    await self.maybe_send_incense_completion_ping(buyers_data, incense_data)
                    await self.maybe_send_ready_prompt(buyers_data)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"✅ Bot is online as {self.bot.user}")

    @commands.command(name="template")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def template(self, ctx, template_id: str = None):
        """Create a template from the message this command replies to."""
        if not template_id or not template_id.strip():
            await ctx.send("❌ Provide a template name, for example: `o!template hw26`.")
            return

        reference = ctx.message.reference
        if reference is None or reference.message_id is None:
            await ctx.send("❌ Reply to the template message when using this command.")
            return

        source_message = reference.resolved
        if not isinstance(source_message, discord.Message):
            try:
                source_message = await ctx.channel.fetch_message(reference.message_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                await ctx.send("❌ I couldn't fetch the replied message.")
                return

        try:
            template_data = parse_template_message(source_message.content)
        except ValueError as exc:
            await ctx.send(f"❌ Invalid template: {exc}")
            return

        template_key = template_id.strip()

        templates = load_templates()
        templates[template_key] = template_data
        save_templates(templates)
        await ctx.send(
            f"✅ Saved template `{template_key}` with {template_data['total_incense']} incense "
            f"across {len(template_data['buyers'])} categories."
        )

    @template.error
    async def template_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Only server administrators can create templates.")
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("❌ This command can only be used in a server.")
        else:
            raise error

    @commands.group(name="organise", invoke_without_command=True, aliases=["organize", "o"])
    async def organise(self, ctx, template_id: str = None):
        try:
            if not template_id or not template_id.strip():
                await ctx.send(
                    "❌ Provide a saved template name, for example: `o!organise hwD`."
                )
                return

            template_id = template_id.strip()
            templates = load_templates()
            if template_id not in templates:
                available_templates = ", ".join(sorted(templates)) or "none"
                await ctx.send(
                    f"❌ Template `{template_id}` was not found. "
                    f"Available templates: `{available_templates}`."
                )
                return

            channel = await self.resolve_channel(TARGET_CHANNEL_ID)
            if not channel:
                await ctx.send("❌ Target channel not found!")
                return

            buyers_data = self.load_buyers()
            active_message = await self.get_active_organiser_message(buyers_data)
            if active_message is not None:
                await ctx.send(f"An org is already going on here: {active_message.jump_url}")
                return

            if not self.has_permission(ctx.author, ctx.guild):
                await ctx.send("❌ You can't organise a round, as you lack permissions.")
                return

            buyers_data = default_buyer_state()

            if ensure_default_buyers(buyers_data, template_id):
                self.save_buyers(buyers_data)

            embed = self.create_organiser_embed(ctx.author, buyers_data)
            view = await self.create_button_view(buyers_data)
            role_mentions, missing_roles, blocked_roles = get_buyer_role_mentions(ctx.guild, buyers_data)
            start_ping_role_id = buyers_data.get("start_ping_role_id")
            send_content = f"<@&{start_ping_role_id}>" if start_ping_role_id else None
            sent_message = await channel.send(
                content=send_content,
                embed=embed,
                view=view,
                allowed_mentions=discord.AllowedMentions(roles=bool(start_ping_role_id)),
            )
            buyers_data["active_message_id"] = sent_message.id
            self.save_buyers(buyers_data)
            # schedule a 5-minute reminder to buyers for remaining spots
            try:
                asyncio.create_task(self.schedule_post_organise_checks(buyers_data))
            except Exception:
                pass
            await ctx.send("✅ Organiser message sent!")

            if missing_roles:
                missing_text = ", ".join(missing_roles)
                await ctx.send(f"⚠️ These buyer roles were not found: {missing_text}")
            if blocked_roles:
                blocked_text = ", ".join(blocked_roles)
                await ctx.send(
                    "⚠️ These roles exist but could not be pinged because they are not mentionable and the bot lacks Mention Everyone permission: "
                    f"{blocked_text}"
                )

        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")
            print(f"Error in organise command: {e}")

    async def end_organise_session(self, ctx):
        source_channel = await self.resolve_channel(TARGET_CHANNEL_ID)
        end_channel = await self.resolve_channel(END_CHANNEL_ID)

        if not source_channel:
            await ctx.send("❌ Target channel not found!")
            return

        if not end_channel:
            await ctx.send("❌ End channel not found!")
            return

        buyers_data = self.load_buyers()
        archive_embed = self.create_organiser_embed(ctx.author, buyers_data)
        await end_channel.send(embed=archive_embed)

        claimed_user_ids = {
            buyer.get("claimed_user")
            for buyer in buyers_data.get("buyers", [])
            if buyer.get("claimed_user")
        }
        for user_id in claimed_user_ids:
            await self.remove_round_buyer_role(user_id, buyers_data, ctx.guild)

        self.save_buyers(default_buyer_state())
        await ctx.send("✅ Organiser data archived and buyer.json cleared.")

    @organise.command(name="end")
    async def organise_end(self, ctx):
        if not self.has_permission(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to use this command. You need the Organiser role or Administrator permissions.")
            return

        try:
            await self.end_organise_session(ctx)

        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")
            print(f"Error in organise end command: {e}")

    @commands.command(name="end")
    async def end(self, ctx):
        if not self.has_permission(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to use this command. You need the Organiser role or Administrator permissions.")
            return

        try:
            await self.end_organise_session(ctx)

        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")
            print(f"Error in end command: {e}")

    @commands.command(name="allow")
    async def allow(self, ctx, role: discord.Role = None):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Only server administrators can allow a role to use o!start.")
            return

        if role is None:
            await ctx.send("❌ Usage: o!allow @role")
            return

        buyers_data = self.load_buyers()
        buyers_data["start_role_id"] = role.id
        self.save_buyers(buyers_data)
        await ctx.send(f"✅ {role.mention} can now use o!start.")

    @commands.command(name="setroles", aliases=["sr"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def set_roles(self, ctx):
        categories = get_template_categories()
        if not categories:
            await ctx.send("❌ No template fields exist yet. Save a template first.")
            return

        view = RoleAssignmentView(self, categories)
        view.message = await ctx.send(embed=self.build_role_assignment_embed(), view=view)

    @set_roles.error
    async def set_roles_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Only server administrators can set organiser roles.")
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("❌ This command can only be used in a server.")
        else:
            raise error

    @commands.command(name="start")
    async def start(self, ctx):
        buyers_data = self.load_buyers()
        if not self.can_start(ctx.author, buyers_data):
            await ctx.send("❌ You don't have permission to use this command.")
            return

        active_message = await self.get_active_organiser_message(buyers_data)
        if active_message is None:
            await ctx.send("❌ No organiser is currently running.")
            return

        incense_data = self.load_incense_state()
        if (
            not is_phase_bypassed(buyers_data, 2)
            and not all_tracked_channels_bought(buyers_data, incense_data)
        ):
            await ctx.send("❌ Not all spots have been bought yet.")
            return

        if not is_phase_bypassed(buyers_data, 1) and not all_spots_claimed(buyers_data):
            await ctx.send("❌ Not all spots have been claimed yet.")
            return

        messages = build_reserve_start_messages(buyers_data)
        if not messages:
            await ctx.send("✅ All spots have been bought, but no reserves are set.")
            return

        for message in messages:
            await ctx.send(
                message,
                allowed_mentions=discord.AllowedMentions(users=True),
            )

    @commands.command(name="bp")
    async def bypass_phase(self, ctx, phase: str = ""):
        buyers_data = self.load_buyers()
        if not self.can_start(ctx.author, buyers_data):
            await ctx.send("❌ You don't have permission to use this command.")
            return

        active_message = await self.get_active_organiser_message(buyers_data)
        if active_message is None:
            await ctx.send("❌ No organiser is currently running.")
            return

        if phase not in {"1", "2"}:
            await ctx.send("❌ Usage: o!bp 1 or o!bp 2")
            return

        phase_number = int(phase)
        bypassed_phases = buyers_data.setdefault("bypassed_phases", [])
        if phase_number not in bypassed_phases:
            bypassed_phases.append(phase_number)

        if phase_number == 1:
            if not active_message.embeds:
                await ctx.send("❌ The organiser message does not identify the organiser.")
                return

            description = active_message.embeds[0].description or ""
            organiser_match = re.search(
                r"Organiser:-\s*<@!?(\d+)>",
                description,
            )
            if organiser_match is None:
                await ctx.send("❌ The organiser message does not identify the organiser.")
                return

            assign_missing_spots_to_user(buyers_data, int(organiser_match.group(1)))
            self.save_buyers(buyers_data)
            await self.refresh_active_organiser_message(buyers_data)
            await self.maybe_send_completion_ping(buyers_data, force=True)
            message = "✅ Phase 1 bypassed. The round-buyer role was notified."
        else:
            incense_data = self.load_incense_state()
            mark_tracked_channels_bought(buyers_data, incense_data)
            self.save_incense_state(incense_data)
            await self.maybe_send_incense_completion_ping(
                buyers_data,
                incense_data,
                force=True,
            )
            message = "✅ Phase 2 bypassed. The organiser was notified to start."

        self.save_buyers(buyers_data)
        await ctx.send(message)

    @commands.command(name="bought")
    async def bought(self, ctx):
        incense_data = self.load_incense_state()
        bought_channels = incense_data.get("bought_channels", [])

        embed, total_pages = build_bought_embed(0, bought_channels, ctx.guild)
        if total_pages <= 1:
            await ctx.send(embed=embed)
            return

        view = BoughtPaginationView(self, bought_channels, ctx.author.id, ctx.guild)
        view.total_pages = total_pages
        view._sync_buttons()
        await ctx.send(embed=embed, view=view)

    @commands.command(name="reserve", aliases=["r"])
    async def reserve(self, ctx, *, pokemon_name: str = ""):
        if not isinstance(ctx.channel, discord.abc.GuildChannel):
            await ctx.send("❌ This command can only be used in a server channel.")
            return

        if not self.can_use_reserve_command(ctx.author):
            await ctx.send(
                "❌ You don't have permission to use this command. Requires Administrator, Org Buyer role, or role 1490123523543400749."
            )
            return

        request_text = (pokemon_name or "").strip()
        if not request_text:
            await ctx.send("❌ Usage: o!r add <pokemon>, o!r add all <pokemon>, o!r remove <pokemon>")
            return

        normalized_request = normalize_pokemon_name(request_text)
        is_add_all = False
        is_remove = False
        target_name = ""

        if normalized_request.startswith("remove all "):
            is_remove = True
            target_name = normalized_request[11:].strip()
        elif normalized_request.startswith("remove "):
            is_remove = True
            target_name = normalized_request[7:].strip()
        elif normalized_request == "remove":
            is_remove = True
            target_name = ""
        elif normalized_request.startswith("add all "):
            is_add_all = True
            target_name = normalized_request[8:].strip()
        elif normalized_request.startswith("add "):
            target_name = normalized_request[4:].strip()
        else:
            await ctx.send("❌ Usage: o!r add <pokemon>, o!r add all <pokemon>, o!r remove <pokemon>")
            return

        is_explicit_normal = False
        if not is_remove and target_name.startswith("normal "):
            is_explicit_normal = True
            target_name = target_name[7:].strip()

        if not target_name and not is_remove:
            await ctx.send("❌ Usage: o!r add <pokemon>, o!r add all <pokemon>, o!r remove <pokemon>")
            return

        class_names = self.load_class_names()
        forms_data = self.load_forms_data()
        base_to_forms, form_to_base = build_forms_indexes(forms_data)

        if target_name:
            aliases_map = self.load_aliases()
            if target_name in aliases_map:
                target_name = aliases_map[target_name]

        if is_remove:
            buyers_data = self.load_buyers()
            claimed_spots = get_claimed_spots_for_user(buyers_data, ctx.author.id)
            locked_spots = [b for b in claimed_spots if buyer_has_reserve(b)]
            
            if not locked_spots:
                await ctx.send("❌ You don't have any reserves set.")
                return

            spot_to_clear = None
            if not target_name:
                if len(locked_spots) == 1:
                    spot_to_clear = locked_spots[0]
                else:
                    await ctx.send("❌ You have multiple reserves. Please specify which one to remove: `o!r remove <name>`")
                    return
            else:
                target_base = form_to_base.get(target_name, target_name)
                for spot in locked_spots:
                    for res in get_reserve_list(spot):
                        res_norm = normalize_pokemon_name(res)
                        res_target = res_norm[4:].strip() if res_norm.startswith("all ") else (res_norm[7:].strip() if res_norm.startswith("normal ") else res_norm)
                        res_base = form_to_base.get(res_target, res_target)
                        if res_base == target_base or res_norm == target_name:
                            spot_to_clear = spot
                            break
                    if spot_to_clear:
                        break
                
                if not spot_to_clear:
                    await ctx.send("❌ No matching reserve found.")
                    return

            spot_to_clear["reserve"] = []
            buyers_data["ready_prompt_sent"] = False
            self.save_buyers(buyers_data)
            await self.refresh_active_organiser_message(buyers_data)
            await ctx.send(f"✅ Reserve removed for {spot_to_clear['category']}.")
            return

        valid_names = set(class_names)
        valid_names.update(base_to_forms.keys())
        valid_names.update(form_to_base.keys())

        if target_name not in valid_names:
            await ctx.send(
                "❌ That Pokemon Doestn exist.\n\n⚠️ Please Note: The bot doesnt support alias for the mean time, pls prefer using original english names."
            )
            return

        reserve_rules = self.load_reserve_rules()
        if self.is_blocked_reserve_name(target_name, reserve_rules, form_to_base):
            await ctx.send("🚫 You cant add this pokemon as reserve.")
            return

        buyers_data = self.load_buyers()
        claimed_spots = get_claimed_spots_for_user(buyers_data, ctx.author.id)

        if not claimed_spots:
            await ctx.send("❌ You have no claimed spot to set reserve for.")
            return

        target_base = form_to_base.get(target_name, target_name)

        # Determine the intended reserve value based on user input:
        # - If user explicitly requested 'all', use all <base>
        # - If user prefixed with 'normal ', force only the base form
        # - If user input matched a specific form, reserve that form only
        # - If user input matched a base and base has multiple forms, reserve 'all <base>'
        # - Otherwise reserve the base name
        reserve_value = None

        # If the user explicitly asked for 'all', honor it (resolve form->base first)
        if is_add_all:
            reserve_value = f"all {target_base}"
        else:
            # If user typed 'normal <name>', treat as base-only
            if is_explicit_normal:
                # strip the 'normal ' prefix from original normalized_request (target_name already stripped)
                maybe_name = target_name
                base_name = form_to_base.get(maybe_name, maybe_name)
                reserve_value = f"normal {base_name}"
            else:
                # If they typed a specific form name, reserve that form only
                if target_name in form_to_base:
                    # target_name is a form
                    reserve_value = target_name
                else:
                    # target_name is (or resolved to) a base
                    forms_for_base = base_to_forms.get(target_base, set()) if 'base_to_forms' in locals() else set()
                    if forms_for_base and len(forms_for_base) > 0:
                        reserve_value = f"all {target_base}"
                    else:
                        reserve_value = target_base

        open_spots = [buyer for buyer in claimed_spots if not buyer_has_reserve(buyer)]
        locked_spots = [buyer for buyer in claimed_spots if buyer_has_reserve(buyer)]

        if not open_spots:
            locked_categories = ", ".join(buyer["category"] for buyer in locked_spots) if locked_spots else "none"
            await ctx.send(
                f"❌ You already set reserves for every claimed spot. Locked spots: {locked_categories}. "
                "A reserve can't be changed again once it is set."
            )
            return

        if len(open_spots) > 1:
            open_categories = ", ".join(buyer["category"] for buyer in open_spots)
            locked_categories = ", ".join(buyer["category"] for buyer in locked_spots) if locked_spots else "none"
            display_reserve = format_reserve_display(reserve_value)
            view = ReserveSpotSelectView(self, ctx.author.id, reserve_value, open_spots, locked_spots, form_to_base, base_to_forms)
            await ctx.send(
                f"You have multiple claimed spots that can still be edited.\n"
                f"Open spots: {open_categories}\n"
                f"Already locked: {locked_categories}\n"
                f"Choose where to set: {display_reserve}",
                view=view,
            )
            return

        chosen_spot = open_spots[0]
        result_message = await self.apply_reserve_to_buyer(buyers_data, chosen_spot, target_base, form_to_base, base_to_forms, reserve_value_override=reserve_value)
        if result_message is None:
            await ctx.send("❌ This spot already has a reserve set and can't be changed again.")
            return

        await ctx.send(result_message)

    @commands.group(name="pause", invoke_without_command=True)
    async def pause(self, ctx):
        if not self.has_permission(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to use this command. You need the Organiser role or Administrator permissions.")
            return

        if not isinstance(ctx.channel, discord.abc.GuildChannel):
            await ctx.send("❌ This command can only be used in a server channel.")
            return

        incense_data = self.load_incense_state()
        if await self.set_tracker_send_permissions(ctx.channel, ctx.guild, False):
            add_incense_channel_id(incense_data, ctx.channel.id)
            self.save_incense_state(incense_data)
            await ctx.send("✅ Send message permission removed in this channel.")
        else:
            await ctx.send("❌ Failed to remove send message permission in this channel.")

    @pause.command(name="all")
    async def pause_all(self, ctx):
        if not self.has_permission(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to use this command. You need the Organiser role or Administrator permissions.")
            return

        if not isinstance(ctx.channel, discord.abc.GuildChannel):
            await ctx.send("❌ This command can only be used in a server channel.")
            return

        incense_data = self.load_incense_state()
        await self.pause_tracked_channels(ctx, incense_data)

    @commands.group(name="resume", invoke_without_command=True)
    async def resume(self, ctx):
        if not self.has_permission(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to use this command. You need the Organiser role or Administrator permissions.")
            return

        if not isinstance(ctx.channel, discord.abc.GuildChannel):
            await ctx.send("❌ This command can only be used in a server channel.")
            return

        incense_data = self.load_incense_state()
        if await self.set_tracker_send_permissions(ctx.channel, ctx.guild, True):
            remove_incense_channel_id(incense_data, ctx.channel.id)
            self.save_incense_state(incense_data)
            await ctx.send("✅ Send message permission restored in this channel.")
        else:
            await ctx.send("❌ Failed to restore send message permission in this channel.")

    @resume.command(name="all")
    async def resume_all(self, ctx):
        if not self.has_permission(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to use this command. You need the Organiser role or Administrator permissions.")
            return

        if not isinstance(ctx.channel, discord.abc.GuildChannel):
            await ctx.send("❌ This command can only be used in a server channel.")
            return

        incense_data = self.load_incense_state()
        await self.resume_tracked_channels(ctx, incense_data)

    @commands.command(name="access")
    async def access(self, ctx):
        """Grant view permissions on incense categories to specified roles."""
        target_categories = ["・ incense-1", "・ incense-2"]
        access_role_id = 1490641491750813736

        access_role = ctx.guild.get_role(access_role_id)
        if access_role is None:
            await ctx.send(f"❌ Role with ID {access_role_id} not found in this server.")
            return

        admin_roles = [role for role in ctx.guild.roles if role.permissions.administrator]

        if not admin_roles:
            await ctx.send("❌ No admin roles found in this server.")
            return

        target_permission_roles = [access_role] + admin_roles
        unique_target_roles = list({r.id: r for r in target_permission_roles}.values())

        found_categories = []
        for category in ctx.guild.categories:
            if category.name in target_categories:
                found_categories.append(category)

        if not found_categories:
            await ctx.send(f"❌ Categories {' or '.join(target_categories)} not found in this server.")
            return

        updated_count = 0
        failed_count = 0

        for category in found_categories:
            for target_role in unique_target_roles:
                overwrite = category.overwrites_for(target_role)
                overwrite.view_channel = True
                try:
                    await category.set_permissions(
                        target_role,
                        overwrite=overwrite,
                        reason=f"access command: granted view for {category.name}",
                    )
                    updated_count += 1
                except (discord.Forbidden, discord.HTTPException):
                    failed_count += 1

            for channel in category.channels:
                try:
                    await channel.edit(sync_permissions=True, reason="access command: synced permissions with category")
                    updated_count += 1
                except (discord.Forbidden, discord.HTTPException):
                    failed_count += 1

        if failed_count:
            await ctx.send(
                f"✅ Synced {updated_count} channel(s) and updated category permissions. "
                f"⚠️ Failed for {failed_count} operation(s)."
            )
        else:
            await ctx.send(f"✅ Synced {updated_count} channel(s) with category permissions.")

    @commands.command(name="createincense")
    async def createincense(self, ctx):
        """Create incense categories/channels from incense-101 to incense-300 in 50-channel blocks."""
        if not self.has_permission(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to use this command. You need the Organiser role or Administrator permissions.")
            return

        start_channel = 101
        end_channel = 300
        channels_per_category = 50

        created_categories = 0
        created_channels = 0
        skipped_channels = 0
        failed_ops = 0

        for block_start in range(start_channel, end_channel + 1, channels_per_category):
            block_end = min(block_start + channels_per_category - 1, end_channel)
            category_number = 3 + ((block_start - start_channel) // channels_per_category)
            category_name = f"・ incense-{category_number}"

            category = discord.utils.get(ctx.guild.categories, name=category_name)
            if category is None:
                try:
                    category = await ctx.guild.create_category(
                        name=category_name,
                        reason="createincense command: create incense category block",
                    )
                    created_categories += 1
                except (discord.Forbidden, discord.HTTPException):
                    failed_ops += 1
                    continue

            existing_channel_names = {channel.name for channel in category.channels}

            for channel_number in range(block_start, block_end + 1):
                channel_name = f"incense-{channel_number}"
                if channel_name in existing_channel_names:
                    skipped_channels += 1
                    continue

                try:
                    await ctx.guild.create_text_channel(
                        name=channel_name,
                        category=category,
                        reason="createincense command: create incense channels 101-300",
                    )
                    created_channels += 1
                    existing_channel_names.add(channel_name)
                except (discord.Forbidden, discord.HTTPException):
                    failed_ops += 1

        await ctx.send(
            f"✅ Created {created_categories} category(s), {created_channels} channel(s), skipped {skipped_channels} existing channel(s). "
            f"⚠️ Failed operations: {failed_ops}."
        )


async def setup(bot):
    await bot.add_cog(OrganiseCog(bot))
