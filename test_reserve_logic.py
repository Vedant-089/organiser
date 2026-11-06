import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FORMS_FILE = os.path.join(BASE_DIR, "forms.json")
RESERVE_FILE = os.path.join(BASE_DIR, "reserve.json")


def normalize_pokemon_name(name):
    normalized = (name or "").strip().lower().replace("-", " ")
    return " ".join(normalized.split())


with open(FORMS_FILE, "r", encoding="utf-8") as f:
    forms = json.load(f)

with open(RESERVE_FILE, "r", encoding="utf-8") as f:
    reserve_rules = json.load(f)

# build form_to_base
form_to_base = {}
for base, forms_list in forms.items():
    base_n = normalize_pokemon_name(base)
    if isinstance(forms_list, list):
        for fm in forms_list:
            fn = normalize_pokemon_name(fm)
            form_to_base[fn] = base_n

# blocked names per categories
blocked_categories = {"rare", "regional", "gigantamax", "eeveelutions", "paradox"}
blocked_names = set()
for cat in blocked_categories:
    vals = reserve_rules.get(cat, [])
    if isinstance(vals, list):
        for v in vals:
            nv = normalize_pokemon_name(v)
            if nv:
                blocked_names.add(nv)


def is_blocked_local(name):
    return normalize_pokemon_name(name) in blocked_names

# special forms list
special = ["Prof Tangrowth", "Chef Dente", "DJ Rotom", "Smearguru", "Peakychu", "Mosslax"]
special_norm = {normalize_pokemon_name(s) for s in special}


def can_reserve(request_name, claimed_categories):
    # normalize and determine target base
    req = normalize_pokemon_name(request_name)
    target_base = form_to_base.get(req, req)

    # blocked by reserve.json only if exact match
    if is_blocked_local(req):
        return False, f"Blocked by reserve.json for exact name: {req}"

    # special-case: only allowed if requester has Reserve-1..4 when requesting exact special form
    if req in special_norm:
        has_reserve = any(cat in ("Reserve-1","Reserve-2","Reserve-3","Reserve-4") for cat in claimed_categories)
        if not has_reserve:
            return False, f"Special form {req} requires Reserve-1..4 ownership"

    # otherwise allowed
    return True, f"Allowed: req={req}, base={target_base}"


tests = [
    ("hisuian growlithe", []),
    ("growlithe", []),
    ("dj rotom", []),
    ("dj rotom", ["Reserve-1"]),
    ("Prof Tangrowth", ["Reserve-2"]),
    ("prof tangrowth", []),
]

for t, cats in tests:
    ok, msg = can_reserve(t, cats)
    print(f"Test '{t}' with claimed {cats}: -> {'OK' if ok else 'BLOCKED'} ({msg})")
