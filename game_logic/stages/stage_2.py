# game_logic/stages/stage_2.py

from ..monsters.cat_assassin import CatAssassin
from ..background import FixedBackground

# 로딩 화면 정보
LOADING_SCREEN_INFO = {
    'stage_number': 2,
    'bg_image': 'resources/Texture_organize/UI/Stage_Loading/Stage_2/St2Loading_BG.png',
    'animation_prefix': 'resources/Texture_organize/UI/Stage_Loading/Stage_2/St2Loading_',
    'animation_count': 12,  # 0~11
    # 추가 애니메이션 (카트)
    'extra_animation': {
        'prefix': 'resources/Texture_organize/UI/Stage_Loading/Stage_2/St2Loading_Cart_',
        'count': 12,  # 0~11
        'position': 'Cart',  # 위치 지정
        'scale': 5.0
    }
}

# 플레이어 시작 위치
PLAYER_START_POSITION = {
    'x': 0,
    'y': 0
}

stage_data = {
    'monsters': [
        (CatAssassin, 0, 0),
        # (CatAssassin, 600, 600),
        # (CatAssassin, 200, 600),
        # (CatAssassin, 600, 200),
    ],
    'background': {
        # 'image': 'resources/Texture_organize/UI/Stage_Loading/Stage_2/St2Loading_BG.png',
        # 'width': 1600,
        # 'height': 900
    }
}

def load(world):
    """Loads stage data into the world."""

    # Load background
    bg_info = stage_data.get('background')
    if bg_info:
        background = FixedBackground(bg_info['image'], bg_info['width'], bg_info['height'])
        world['bg'].append(background)
        print(f"[Stage 2] 배경 이미지 추가됨: {bg_info['image']}")

    # Load monsters
    for monster_class, x, y in stage_data['monsters']:
        monster = monster_class(x, y)
        monster.world = world # Allow monster to access the world
        world['entities'].append(monster)
    print("Stage 2 with CatAssassin loaded.")
