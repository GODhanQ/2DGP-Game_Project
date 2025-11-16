# game_logic/stages/stage_2.py

from ..monsters.cat_assassin import CatAssassin

stage_data = {
    'monsters': [
        (CatAssassin, 200, 200),
        (CatAssassin, 600, 600),
        (CatAssassin, 200, 600),
        (CatAssassin, 600, 200),
    ],
}

def load(world):
    """Loads stage data into the world."""
    for monster_class, x, y in stage_data['monsters']:
        monster = monster_class(x, y)
        monster.world = world # Allow monster to access the world
        world['entities'].append(monster)
    print("Stage 2 with CatAssassin loaded.")
