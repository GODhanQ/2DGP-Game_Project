# game_logic/stages/stage_1.py

# This stage will use CatAssassin monsters
from ..monsters.cat_assassin import CatAssassin

# Stage data dictionary
stage_data = {
    'monsters': [
        # (CatAssassin, 200, 450),
        (CatAssassin, 600, 450),
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
        monster = monster_class(x, y)
        monster.world = world  # Allow monster to access the world (e.g., to spawn projectiles)
        world['entities'].append(monster)

    print("Stage 1 with CatAssassin loaded.")
