# game_logic/stages/stage_1.py

# This stage will use Slime and Goblin monsters
from ..monsters.slime import Slime
from ..monsters.goblin import Goblin

# Stage data dictionary
stage_data = {
    'monsters': [
        (Slime, 200, 150),
        (Slime, 600, 150),
        (Goblin, 400, 400)
    ],
    'background': {
        # 'image': 'resources/background_stage1.png', # Placeholder
        # 'width': 1024,
        # 'height': 768
    }
}

def load(world):
    """Loads stage data into the world."""

    # Load background (if any)
    # bg_info = stage_data.get('background')
    # if bg_info:
    #     world['background'] = FixedBackground(bg_info['image'], bg_info['width'], bg_info['height'])

    # Load monsters
    for monster_class, x, y in stage_data['monsters']:
        world['entities'].append(monster_class(x, y))

    print("Stage 1 loaded.")

