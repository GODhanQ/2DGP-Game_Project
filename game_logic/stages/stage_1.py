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

# 플레이어 시작 위치 (맵 중심 기준)
PLAYER_START_POSITION = {
    'x': 0,
    'y': -700
}

# Stage data dictionary
stage_data = {
    'monsters': [
        (CatAssassin, 300, 0),  # 몬스터를 플레이어 우측에 배치
    ],
    'background': {
        'image': 'resources/Texture_organize/Map/Stage4_Bad_Lands/badlandBG.png',
        'width': window_width,
        'height': window_height,
        'scale': 10.0
    },
    'stage_map': {
        'image': 'resources/Texture_organize/Map/Stage4_Bad_Lands/Map_Askard/AskardMap.png',
        'width': 512,
        'height': 385,
        'scale': 5.0
    }
}

def load(world):
    """
    스테이지 데이터를 월드에 로드합니다.
    Args:
        world: 게임 월드 딕셔너리 (레이어별로 객체 리스트 포함)
    """
    print("[Stage 1] 스테이지 1 로드 시작...")

    # 배경 이미지 로드 (선택적 - 맵 뒤에 표시될 단색 또는 고정 배경)
    bg_info = stage_data.get('background')
    if bg_info:
        background = FixedBackground(
            bg_info['image'],
            bg_info['width'],
            bg_info['height']
        )
        try:
            background.scale = bg_info.get('scale')
        except Exception as ex:
            print(f"\033[91m[Stage 1] 배경 스케일 설정 오류: {ex}\033[0m")
            background.scale = 1.0
        world['bg'].append(background)
        print(f"[Stage 1] 배경 이미지 추가됨: {bg_info['image']}")

    # 스테이지 맵 로드 (실제 플레이 맵)
    stageMap_info = stage_data.get('stage_map')
    if stageMap_info:
        # 맵 스케일 적용
        map_scale = stageMap_info.get('scale', 1.0)
        scaled_width = int(stageMap_info['width'] * map_scale)
        scaled_height = int(stageMap_info['height'] * map_scale)

        stage_map = StageMap(
            stageMap_info['image'],
            scaled_width,
            scaled_height
        )
        stage_map.scale = map_scale

        # 맵을 ground 레이어에 추가 (리스트에 append)
        world['ground'].append(stage_map)
        print(f"[Stage 1] 스테이지 맵 추가됨: {stageMap_info['image']}")
        print(f"[Stage 1]   - 원본 크기: {stageMap_info['width']}x{stageMap_info['height']}")
        print(f"[Stage 1]   - 스케일: {map_scale}")
        print(f"[Stage 1]   - 최종 크기: {scaled_width}x{scaled_height}")

    # 몬스터 로드
    for monster_class, x, y in stage_data['monsters']:
        monster = monster_class(x, y)
        monster.world = world  # 몬스터가 월드에 접근할 수 있도록 (투사체 생성 등)
        world['entities'].append(monster)
        print(f"[Stage 1] 몬스터 추가됨: {monster_class.__name__} at ({x}, {y})")

    print("[Stage 1] 스테이지 1 로드 완료!")
