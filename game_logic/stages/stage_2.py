# game_logic/stages/stage_2.py

from ..monsters.goblin import Goblin

stage_data = {
    'monsters': [
        (Goblin, 200, 200),
        (Goblin, 600, 600),
    ],
}

def load(world):
    """Loads stage data into the world."""
    for monster_class, x, y in stage_data['monsters']:
        world['entities'].append(monster_class(x, y))
    print("Stage 2 loaded.")
# empty

