import json
import shutil

FILE = "alias.json"
BACKUP = "alias_final_backup.json"

# Conflicting aliases and the Pokémon that currently share them
conflicts = {
    "Alola-Form": [
        "alolan diglett", "alolan dugtrio", "alolan exeggutor",
        "alolan geodude", "alolan golem", "alolan graveler",
        "alolan grimer", "alolan marowak", "alolan meowth",
        "alolan muk", "alolan ninetales", "alolan persian",
        "alolan raichu", "alolan raticate", "alolan rattata",
        "alolan sandshrew", "alolan sandslash", "alolan vulpix"
    ],

    "Aroranosugata": [
        "alolan diglett", "alolan dugtrio", "alolan exeggutor",
        "alolan geodude", "alolan golem", "alolan graveler",
        "alolan grimer", "alolan marowak", "alolan meowth",
        "alolan muk", "alolan ninetales", "alolan persian",
        "alolan raichu", "alolan raticate", "alolan rattata",
        "alolan sandshrew", "alolan sandslash", "alolan vulpix"
    ],

    "Arōranosugata": [
        "alolan diglett", "alolan dugtrio", "alolan exeggutor",
        "alolan geodude", "alolan golem", "alolan graveler",
        "alolan grimer", "alolan marowak", "alolan meowth",
        "alolan muk", "alolan ninetales", "alolan persian",
        "alolan raichu", "alolan raticate", "alolan rattata",
        "alolan sandshrew", "alolan sandslash", "alolan vulpix"
    ],

    "Forme d'Alola": [
        "alolan diglett", "alolan dugtrio", "alolan exeggutor",
        "alolan geodude", "alolan golem", "alolan graveler",
        "alolan grimer", "alolan marowak", "alolan meowth",
        "alolan muk", "alolan ninetales", "alolan persian",
        "alolan raichu", "alolan raticate", "alolan rattata",
        "alolan sandshrew", "alolan sandslash", "alolan vulpix"
    ],

    "Forme dAlola": [
        "alolan diglett", "alolan dugtrio", "alolan exeggutor",
        "alolan geodude", "alolan golem", "alolan graveler",
        "alolan grimer", "alolan marowak", "alolan meowth",
        "alolan muk", "alolan ninetales", "alolan persian",
        "alolan raichu", "alolan raticate", "alolan rattata",
        "alolan sandshrew", "alolan sandslash", "alolan vulpix"
    ],

    "Otachi": [
        "furret",
        "sentret"
    ],

    "アローラのすかた": [
        "alolan diglett", "alolan dugtrio", "alolan exeggutor",
        "alolan geodude", "alolan golem", "alolan graveler",
        "alolan grimer", "alolan marowak", "alolan meowth",
        "alolan muk", "alolan ninetales", "alolan persian",
        "alolan raichu", "alolan raticate", "alolan rattata",
        "alolan sandshrew", "alolan sandslash", "alolan vulpix"
    ],

    "アローラのすがた": [
        "alolan diglett", "alolan dugtrio", "alolan exeggutor",
        "alolan geodude", "alolan golem", "alolan graveler",
        "alolan grimer", "alolan marowak", "alolan meowth",
        "alolan muk", "alolan ninetales", "alolan persian",
        "alolan raichu", "alolan raticate", "alolan rattata",
        "alolan sandshrew", "alolan sandslash", "alolan vulpix"
    ],

    "カラカラ": [
        "cubone",
        "marowak"
    ]
}


# --------------------------------------------------
# Backup
# --------------------------------------------------

shutil.copy2(FILE, BACKUP)
print(f"Backup created: {BACKUP}")


# --------------------------------------------------
# Load
# --------------------------------------------------

with open(FILE, "r", encoding="utf-8") as f:
    data = json.load(f)


# --------------------------------------------------
# Remove conflicts
# --------------------------------------------------

removed = 0

for alias, pokemon_list in conflicts.items():

    for pokemon in pokemon_list:

        if pokemon not in data:
            print(f"[WARNING] Pokémon not found: {pokemon}")
            continue

        old_aliases = data[pokemon]

        if alias in old_aliases:
            data[pokemon] = [
                a for a in old_aliases
                if a != alias
            ]

            removed += 1
            print(f"[REMOVED] {alias} -> {pokemon}")


# --------------------------------------------------
# Save
# --------------------------------------------------

with open(FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print()
print("=" * 60)
print(f"Removed {removed} conflicting aliases")
print(f"Updated: {FILE}")
print(f"Backup:  {BACKUP}")
print("=" * 60)