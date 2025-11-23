# game_logic/stages/stage_1.py

# This stage will use CatAssassin monsters
from ..monsters.cat_assassin import CatAssassin
from ..background import FixedBackground, StageMap

# 창 크기 설정 (main.py와 동일하게 유지)
window_scale = 8
window_width, window_height = 160 * window_scale, 90 * window_scale

# 로딩 화면 정보
LOADING_SCREEN_INFO = {
    'stage_number': 1,
    'bg_image': 'resources/Texture_organize/UI/Stage_1/St1Loading_BG.png',
    'animation_prefix': 'resources/Texture_organize/UI/Stage_Loading/Stage_1/St1Loading_',
    'animation_count': 12  # 0~11
}

# 플레이어 시작 위치
PLAYER_START_POSITION = {
    'x': 0,
    'y': 0
}

# Stage data dictionary
stage_data = {
    'monsters': [
        (CatAssassin, 0, 0),
    ],
    'background': {
        'image': 'resources/Texture_organize/Map/Stage4_Bad_Lands/badlandBG.png',
        'width': window_width,
        'height': window_height
    },
    'stage_map': {
        'image': 'resources/Texture_organize/Map/Stage4_Bad_Lands/Map_Askard/AskardMap.png',
        'width': 512,
        'height': 368
    }
}

def load(world):
    """Loads stage data into the world."""

    # Load background
    bg_info = stage_data.get('background')
    if bg_info:
        background = FixedBackground(bg_info['image'], bg_info['width'], bg_info['height'])
        world['bg'].append(background)
        print(f"[Stage 1] 배경 이미지 추가됨: {bg_info['image']}")

    # Load monsters
    for monster_class, x, y in stage_data['monsters']:
        monster = monster_class(x, y)
        monster.world = world  # Allow monster to access the world (e.g., to spawn projectiles)
        world['entities'].append(monster)

    # TODO : Load and set up the stage map
    # 1. create StageMap instance
    # 2. assign to world['ground']
    # 3. print confirmation message

    stageMap_info = stage_data.get('stage_map')
    if stageMap_info:
        stage_map = StageMap(stageMap_info['image'], stageMap_info['width'], stageMap_info['height'])
        world['ground'] = stage_map
        print(f"[Stage 1] 스테이지 맵 추가됨: {stageMap_info['image']}")

    print("Stage 1 with CatAssassin loaded.")
