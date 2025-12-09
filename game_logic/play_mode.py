# game_logic.play_mode: play mode state that creates Player, InventoryOverlay, Cursor
# minimal, compatible with existing game_logic modules
import pico2d as p2
from sdl2 import SDL_QUIT, SDL_KEYDOWN, SDLK_ESCAPE
from PIL import Image

import game_framework
from .player import Player
from .ui_overlay import InventoryOverlay, HealthBar, ManaBar, DashBar, BuffIndicatorUI
from .cursor import Cursor
from .loading_screen import LoadingScreen
from . import defeat_mode, victory_mode
# 사용할 스테이지 모듈들을 import 합니다.
from .stages import stage_1, stage_2, stage_3

# world layers: keep same keys as original main.py
world = {
    'ground': [],
    'upper_ground': [],
    'walls': [],
    'effects_back': [],
    'entities': [],
    'effects_front': [],
    'ui': [],
    'extra_bg': [],
    'extras': [],
    'cursor': []
}
world['bg'] = world['ground']

# 스테이지 관리
stages = [stage_1, stage_2, stage_3]
# stages = [stage_1]
# stages = [stage_2]
# stages = [stage_3]
current_stage_index = 0
is_stage_cleared = False

# 로딩 화면 관리
loading_screen = None
is_loading = False
next_stage_to_load = None

# 경과 시간 추적 (play_mode 진입 후 경과 시간)
elapsed_time = 0.0

# 승리 페이드인 효과 관련 변수
is_fading_to_victory = False  # 승리 페이드인 진행 중 플래그
victory_fade_elapsed = 0.0    # 페이드인 경과 시간
victory_fade_duration = 3.0   # 페이드인 지속 시간 (3초)
victory_fade_image = None     # 페이드인 이미지


class Camera:
    """
    플레이어를 부드럽게 따라가는 카메라 클래스
    맵의 경계를 넘지 않도록 제한하며, 화면 중앙을 (0,0)으로 하는 좌표계 사용
    """
    def __init__(self, target, map_width, map_height, screen_width, screen_height):
        """
        카메라 초기화
        Args:
            target: 카메라가 따라갈 대상 (일반적으로 플레이어)
            map_width: 맵의 전체 너비
            map_height: 맵의 전체 높이
            screen_width: 화면 너비
            screen_height: 화면 높이
        """
        self.target = target
        self.x = target.x
        self.y = target.y
        self.map_width = map_width
        self.map_height = map_height
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.smooth = 0.1  # 부드러운 이동 정도 (0~1, 낮을수록 부드럽고 느림)

        # 맵 오프셋 (배경의 중심점, calculate_background_bounds에서 설정)
        self.map_offset_x = 0
        self.map_offset_y = 0

    def update(self):
        """
        카메라 위치 업데이트 - 타겟을 부드럽게 따라가며 맵 경계 내로 제한
        """
        # 플레이어 위치를 부드럽게 따라감 (LERP - Linear Interpolation)
        target_x = self.target.x
        target_y = self.target.y
        self.x += (target_x - self.x) * self.smooth
        self.y += (target_y - self.y) * self.smooth

        # 화면의 중앙이 (0,0)이 되도록 카메라 위치 보정
        half_w = self.screen_width // 2
        half_h = self.screen_height // 2

        # 맵의 중심이 (0,0) 기준이므로, 카메라의 x, y가 -map_width/2 ~ map_width/2 범위로 제한
        min_x = -self.map_width/2
        max_x = self.map_width/2
        min_y = -self.map_height/2
        max_y = self.map_height/2

        self.x = max(min_x, min(self.x, max_x))
        self.y = max(min_y, min(self.y, max_y))

        # 만약 맵이 화면보다 작으면 중앙에 고정
        if self.map_width <= self.screen_width:
            self.x = 0
        if self.map_height <= self.screen_height:
            self.y = 0

    def apply(self, obj_x, obj_y):
        """
        카메라 위치에 따라 오브젝트의 화면 좌표 계산
        Args:
            obj_x: 오브젝트의 월드 x 좌표 (맵 중심 기준)
            obj_y: 오브젝트의 월드 y 좌표 (맵 중심 기준)
        Returns:
            tuple: (draw_x, draw_y) - 화면에 그릴 좌표
        """
        half_w = self.screen_width // 2
        half_h = self.screen_height // 2
        return obj_x - self.x + half_w, obj_y - self.y + half_h


# Camera 객체를 전역으로 선언
camera = None


def calculate_background_bounds():
    """
    ground 레이어의 모든 배경 객체들의 실제 범위를 계산합니다.
    모든 배경 이미지를 고려하여 최소/최대 x, y 좌표를 반환합니다.

    Returns:
        tuple: (min_x, max_x, min_y, max_y) - 배경이 존재하는 실제 영역의 경계
    """
    min_x = float('inf')
    max_x = float('-inf')
    min_y = float('inf')
    max_y = float('-inf')

    # ground 레이어의 모든 객체를 순회
    for obj in world['ground']:
        # 객체가 x, y, image 속성을 가지고 있는지 확인
        if hasattr(obj, 'x') and hasattr(obj, 'y') and hasattr(obj, 'image'):
            # 객체의 중심 좌표
            obj_x = obj.x
            obj_y = obj.y

            # 이미지 크기 계산 (scale 속성이 있으면 적용)
            scale = getattr(obj, 'scale', 1.0)
            img_width = obj.image.w * scale
            img_height = obj.image.h * scale

            # 객체의 경계 계산 (중심 기준이므로 절반씩)
            obj_left = obj_x - img_width / 2
            obj_right = obj_x + img_width / 2
            obj_bottom = obj_y - img_height / 2
            obj_top = obj_y + img_height / 2

            # 최소/최대 값 업데이트
            min_x = min(min_x, obj_left)
            max_x = max(max_x, obj_right)
            min_y = min(min_y, obj_bottom)
            max_y = max(max_y, obj_top)

    # 유효한 범위가 계산되지 않은 경우 기본값 반환 (1280x720 화면 기준)
    if min_x == float('inf') or max_x == float('-inf'):
        print("[WARNING] 배경 범위 계산 실패, 기본값 사용")
        return (-640, 640, -360, 360)

    print(f"[play_mode] 계산된 배경 범위: X({min_x:.1f} ~ {max_x:.1f}), Y({min_y:.1f} ~ {max_y:.1f})")
    return (min_x, max_x, min_y, max_y)


def change_stage(next_stage_index):
    """다음 스테이지로 변경하는 함수"""
    global current_stage_index, loading_screen, is_loading, next_stage_to_load, is_fading_to_victory, victory_fade_elapsed, victory_fade_image

    # 다음 스테이지 인덱스 확인
    if next_stage_index >= len(stages):
        # 모든 스테이지 클리어 시 페이드인 효과 시작
        print("All stages cleared! Starting fade-in effect...")
        is_fading_to_victory = True
        victory_fade_elapsed = 0.0

        # 플레이어를 entities에서 extras 레이어로 즉시 이동
        player = world.get('player')
        if player and player in world['entities']:
            world['entities'].remove(player)
            world['extras'].append(player)
            print("[change_stage] 플레이어를 extras 레이어로 이동")

        # 페이드인 이미지 로드
        try:
            victory_fade_image = p2.load_image('resources/Texture_organize/IDK_2/Square.png')
            print("[change_stage] 승리 페이드인 이미지 로드 성공")
        except Exception as ex:
            print(f'\033[91m[change_stage] 승리 페이드인 이미지 로드 실패: {ex}\033[0m')
            victory_fade_image = None

        return

    # 로딩 화면 시작 - 스테이지 모듈의 LOADING_SCREEN_INFO 사용
    next_stage_module = stages[next_stage_index]
    loading_info = getattr(next_stage_module, 'LOADING_SCREEN_INFO', None)

    if loading_info:
        print(f"[change_stage] 스테이지 {next_stage_index + 1} 로딩 화면 시작")
        loading_screen = LoadingScreen(loading_info)
        is_loading = True
        next_stage_to_load = next_stage_index
    else:
        # LOADING_SCREEN_INFO가 없으면 로딩 화면 없이 바로 전환
        print(f"[change_stage] 스테이지 {next_stage_index + 1}에 로딩 화면 정보 없음, 즉시 전환")
        next_stage_to_load = next_stage_index
        _complete_stage_change()


class PlayModeWall:
    """플레이 모드에서 사용하는 벽 클래스 (투명 영역 감지용)"""
    def __init__(self, x, y, w, h):
        """
        벽 초기화
        Args:
            x: 벽의 월드 x 좌표 (맵 중심 기준)
            y: 벽의 월드 y 좌표 (맵 중심 기준)
            w: 벽의 너비
            h: 벽의 높이
        """
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def check_collision(self, px, py, pw, ph):
        """
        플레이어와 벽의 충돌 검사
        Args:
            px: 플레이어 x 좌표
            py: 플레이어 y 좌표
            pw: 플레이어 너비
            ph: 플레이어 높이
        Returns:
            bool: 충돌 여부
        """
        return (self.x < px + pw and self.x + self.w > px and
                self.y < py + ph and self.y + self.h > py)

    def update(self):
        """벽은 업데이트가 필요 없음"""
        return True

    def draw(self, draw_x, draw_y):
        """
        벽 디버깅용 그리기 (필요시 주석 해제)
        Args:
            draw_x: 카메라가 적용된 화면 x 좌표
            draw_y: 카메라가 적용된 화면 y 좌표
        """
        # 디버깅용: 벽을 빨간색으로 표시 (벽 위치 확인용)
        # p2.draw_rectangle(draw_x - self.w/2, draw_y - self.h/2,
        #                   draw_x + self.w/2, draw_y + self.h/2)
        pass


def generate_walls_from_png(png_path, block_size=8, map_x=0, map_y=0, map_scale=1.0):
    """
    PNG 이미지의 투명 영역을 감지하여 벽 블록 생성
    Args:
        png_path: PNG 이미지 경로
        block_size: 벽 블록의 기본 크기 (픽셀 단위, 스케일 적용 전)
        map_x: 맵의 월드 x 좌표 (중심 기준)
        map_y: 맵의 월드 y 좌표 (중심 기준)
        map_scale: 맵의 스케일
    Returns:
        list: 생성된 PlayModeWall 객체 리스트
    """
    print(f"[generate_walls_from_png] 시작: {png_path}")
    print(f"  - block_size={block_size}, map_x={map_x}, map_y={map_y}, map_scale={map_scale}")

    try:
        img = Image.open(png_path).convert('RGBA')
    except Exception as ex:
        print(f"\033[91m[generate_walls_from_png] 이미지 열기 실패: {ex}\033[0m")
        return []

    width, height = img.size
    walls = []
    pixels = img.load()
    transparent_count = 0

    # 맵 이미지의 좌상단 기준 좌표 계산 (맵 중심 기준)
    map_left = map_x - (width * map_scale) / 2
    map_bottom = map_y - (height * map_scale) / 2

    print(f"  - 이미지 크기: {width}x{height}")
    print(f"  - 맵 좌하단 좌표: ({map_left:.1f}, {map_bottom:.1f})")

    # 이미지를 블록 단위로 순회
    for y in range(0, height, block_size):
        for x in range(0, width, block_size):
            is_transparent = False
            # 블록 내부의 픽셀들을 검사
            for dy in range(block_size):
                for dx in range(block_size):
                    if x + dx < width and y + dy < height:
                        _, _, _, alpha = pixels[x + dx, y + dy]
                        if alpha == 0:  # 완전 투명
                            is_transparent = True
                            transparent_count += 1
                            break
                if is_transparent:
                    break

            # 투명 블록이면 벽 생성
            if is_transparent:
                # 이미지 좌표를 월드 좌표로 변환
                # 이미지 좌표계: 좌상단 (0,0), 우하단 (width, height)
                # 월드 좌표계: 맵 중심 (0,0)
                wall_x_img = x
                wall_y_img = height - y - block_size  # Y축 반전 (이미지는 위에서 아래로, 월드는 아래에서 위로)

                # 월드 좌표로 변환
                wall_x_world = map_left + wall_x_img * map_scale + (block_size * map_scale) / 2
                wall_y_world = map_bottom + wall_y_img * map_scale + (block_size * map_scale) / 2

                walls.append(PlayModeWall(
                    wall_x_world,
                    wall_y_world,
                    block_size * map_scale,
                    block_size * map_scale
                ))

    print(f"  - 투명 픽셀 수: {transparent_count}, 생성된 벽 수: {len(walls)}")
    return walls


def _complete_stage_change():
    """로딩이 완료된 후 실제 스테이지 전환을 수행"""
    global current_stage_index, world, is_stage_cleared, loading_screen, is_loading, next_stage_to_load, camera

    print(f"[_complete_stage_change] 스테이지 {next_stage_to_load + 1} 로드 시작")

    # 현재 스테이지의 몬스터, 배경 등 제거 (플레이어는 유지)
    player = world.get('player')
    world['entities'] = [player] if player else []
    world['bg'].clear()
    world['walls'].clear()  # 벽도 초기화
    # 다른 레이어도 필요에 따라 초기화
    world['effects_back'].clear()
    world['effects_front'].clear()

    # 다음 스테이지 인덱스로 변경
    current_stage_index = next_stage_to_load

    # 새 스테이지 로드
    stages[current_stage_index].load(world)

    # 스테이지 맵에서 벽 생성 (ground 레이어의 첫 번째 객체가 맵이라고 가정)
    try:
        if world['ground'] and len(world['ground']) > 0:
            stage_map = world['ground'][1]
            if hasattr(stage_map, 'image') and hasattr(stage_map, 'x') and hasattr(stage_map, 'y'):
                # 맵 이미지의 경로 가져오기 (StageMap 객체에서)
                next_stage_module = stages[current_stage_index]
                stage_data = getattr(next_stage_module, 'stage_data', None)

                if stage_data and 'stage_map' in stage_data:
                    map_image_path = stage_data['stage_map']['image']
                    map_scale = getattr(stage_map, 'scale', 1.0)

                    print(f"[_complete_stage_change] 맵 이미지에서 벽 생성 중...")
                    wall_blocks = generate_walls_from_png(
                        map_image_path,
                        block_size=8,
                        map_x=stage_map.x,
                        map_y=stage_map.y,
                        map_scale=map_scale
                    )

                    for wall in wall_blocks:
                        world['walls'].append(wall)

                    print(f"[_complete_stage_change] {len(wall_blocks)}개의 벽 생성 완료")
    except Exception as ex:
        print(f"\033[91m[_complete_stage_change] 벽 생성 실패: {ex}\033[0m")

    # 플레이어 위치 설정 (스테이지에 PLAYER_START_POSITION이 있으면 사용)
    if player:
        next_stage_module = stages[current_stage_index]
        player_start_pos = getattr(next_stage_module, 'PLAYER_START_POSITION', None)

        if player_start_pos:
            # 플레이어 위치를 새 스테이지 시작 위치로 설정
            new_x = player_start_pos['x']
            new_y = player_start_pos['y']
            player.x = new_x
            player.y = new_y
            print(f"[_complete_stage_change] 플레이어 위치 설정: ({player.x}, {player.y})")
        else:
            print(f"[_complete_stage_change] 플레이어 시작 위치 정보 없음, 현재 위치 유지")
    else:
        print(f'\033[91m[_complete_stage_change] 플레이어 객체 없음\033[0m')

    # 카메라 초기화 또는 업데이트
    try:
        min_x, max_x, min_y, max_y = calculate_background_bounds()
        map_width = max_x - min_x
        map_height = max_y - min_y

        screen_width = p2.get_canvas_width()
        screen_height = p2.get_canvas_height()

        # 카메라가 없으면 새로 생성 (첫 스테이지)
        if camera is None and player:
            print(f"[_complete_stage_change] 카메라 생성 중...")
            camera = Camera(player, map_width, map_height, screen_width, screen_height)
            camera.map_offset_x = (min_x + max_x) / 2
            camera.map_offset_y = (min_y + max_y) / 2
            # 카메라를 플레이어 위치로 즉시 동기화
            camera.x = player.x
            camera.y = player.y
            print(f"[_complete_stage_change] 카메라 생성 완료: ({camera.x}, {camera.y})")
        # 카메라가 이미 있으면 맵 크기만 업데이트
        elif camera is not None:
            camera.map_width = map_width
            camera.map_height = map_height
            camera.map_offset_x = (min_x + max_x) / 2
            camera.map_offset_y = (min_y + max_y) / 2
            # 카메라를 플레이어 위치로 즉시 동기화
            if player:
                camera.x = player.x
                camera.y = player.y
            print(f"[_complete_stage_change] 카메라 업데이트 완료: 맵 크기 {map_width:.1f}x{map_height:.1f}")
    except Exception as ex:
        print(f"\033[91m[_complete_stage_change] 카메라 초기화/업데이트 실패: {ex}\033[0m")

    is_stage_cleared = False

    # 로딩 화면 종료
    loading_screen = None
    is_loading = False
    next_stage_to_load = None

    print(f"[_complete_stage_change] Changed to Stage {current_stage_index + 1}")

def enter(player=None):
    global world, current_stage_index, is_stage_cleared, loading_screen, is_loading, next_stage_to_load, elapsed_time
    print("[play_mode] Starting enter()...")

    # 경과 시간 초기화
    elapsed_time = 0.0

    # clear existing
    for k in list(world.keys()):
        try:
            if isinstance(world[k], list):
                world[k].clear()
        except Exception:
            print(f'\033[91m[play_mode] Failed to clear world layer: {k}\033[0m')

    print("[play_mode] Creating player...")
    # create player (use fallback if heavy Player init fails)
    try:
        if player == None:
            player = Player()
        print("[play_mode] Player created successfully")
    except Exception as ex:
        print(f"\033[91m[play_mode] Player initialization failed, using lightweight fallback: {ex}\033[0m")
        from .inventory import InventoryData, seed_debug_inventory

        class _FallbackPlayer:
            def __init__(self):
                self.x = 0  # 맵 중심 기준 좌표
                self.y = 0
                self.face_dir = 1
                self.scale_factor = 1.0
                self.keys_down = {'w': False, 'a': False, 's': False, 'd': False}
                self.particles = []
                self.attack_effects = []
                self.inventory = InventoryData(cols=6, rows=5)
                try:
                    seed_debug_inventory(self.inventory)
                except Exception:
                    pass
                self.inventory_open = False

            def update(self):
                return True

            def rebuild_inventory_passives(self):
                return

            def consume_item_at(self, r, c):
                return False

        player = _FallbackPlayer()

    print("[play_mode] Attaching world reference to player...")
    # attach a reference to the current world so player and callbacks can access/modify it
    try:
        player.world = world
    except Exception:
        pass
    world['player'] = player # 플레이어를 world에 명시적으로 저장
    world['entities'].append(player)

    print("[play_mode] Creating inventory overlay...")
    # inventory overlay: pass world reference so InventoryOverlay can spawn WorldItem into this world
    try:
        inv = InventoryOverlay(player, world)
        print("[play_mode] InventoryOverlay created successfully")
    except Exception as ex:
        print('[play_mode] InventoryOverlay init failed, creating minimal stub:', ex)

        class _InvStub:
            def __init__(self, player, world=None):
                self.player = player
                self.world = world
                self.dragging = False
                self.drag_from = None
                self.drag_icon = None
                self.drag_qty = 0
            def handle_event(self, e):
                return
            def update(self):
                return
            def draw(self):
                return

        inv = _InvStub(player, world)
    world['ui'].append(inv)

    print("[play_mode] Creating health bar...")
    # health bar UI 생성
    try:
        health_bar = HealthBar(player)
        print("[play_mode] HealthBar created successfully")
    except Exception as ex:
        print('[play_mode] HealthBar init failed, using stub:', ex)

        class _HealthBarStub:
            def __init__(self, player):
                self.player = player
            def update(self):
                return
            def draw(self):
                return

        health_bar = _HealthBarStub(player)
    world['ui'].append(health_bar)

    print("[play_mode] Creating mana bar...")
    # mana bar UI 생성
    try:
        mana_bar = ManaBar(player)
        print("[play_mode] ManaBar created successfully")
    except Exception as ex:
        print('[play_mode] ManaBar init failed, using stub:', ex)

        class _ManaBarStub:
            def __init__(self, player):
                self.player = player
            def update(self):
                return
            def draw(self):
                return

        mana_bar = _ManaBarStub(player)
    world['ui'].append(mana_bar)

    print("[play_mode] Creating dash bar...")
    # dash bar UI 생성
    try:
        dash_bar = DashBar(player)
        print("[play_mode] DashBar created successfully")
    except Exception as ex:
        print('[play_mode] DashBar init failed, using stub:', ex)

        class _DashBarStub:
            def __init__(self, player):
                self.player = player
            def update(self):
                return
            def draw(self):
                return

        dash_bar = _DashBarStub(player)
    world['ui'].append(dash_bar)

    print("[play_mode] Creating buff indicator...")
    # buff indicator UI 생성
    try:
        buff_indicator = BuffIndicatorUI(player)
        print("[play_mode] BuffIndicatorUI created successfully")
    except Exception as ex:
        print('[play_mode] BuffIndicatorUI init failed, using stub:', ex)

        class _BuffIndicatorStub:
            def __init__(self, player):
                self.player = player
            def update(self):
                return
            def draw(self):
                return

        buff_indicator = _BuffIndicatorStub(player)
    world['ui'].append(buff_indicator)

    print("[play_mode] Creating cursor...")
    # cursor on top (safe fallback)
    try:
        cursor = Cursor(player)
        print("[play_mode] Cursor created successfully")
    except Exception as ex:
        print('[play_mode] Cursor init failed, using stub cursor:', ex)

        class _CursorStub:
            def __init__(self, player=None):
                self.player = player
                self.x = 0
                self.y = 0
            def update(self):
                return
            def draw(self):
                return
            def handle_event(self, e):
                return

        cursor = _CursorStub(player)
    world['cursor'].append(cursor)

    # expose world to __main__ for legacy code that looks up main.world
    try:
        import sys
        main_mod = sys.modules.get('__main__')
        if main_mod is not None:
            setattr(main_mod, 'world', world)
    except Exception:
        pass

    print("[play_mode] Starting first stage with loading screen...")
    # 첫 번째 스테이지를 로딩 화면과 함께 시작
    current_stage_index = -1  # change_stage가 0으로 설정할 것임
    is_stage_cleared = False

    # change_stage 함수를 사용하여 로딩 화면과 함께 첫 스테이지 로드
    change_stage(0)

    print(f"[play_mode] Entered play_mode, loading Stage 1 with loading screen")

    # Camera 초기화는 _complete_stage_change에서 진행됨

def exit():
    for k in list(world.keys()):
        try:
            if isinstance(world[k], list):
                world[k].clear()
        except Exception:
            pass


def handle_events():
    import game_framework as app_framework
    events = p2.get_events()
    for e in events:
        if e.type == SDL_QUIT:
            print("[play_mode] SDL_QUIT event received, quitting application")
            app_framework.quit()
            return
        if e.type == SDL_KEYDOWN and getattr(e, 'key', None) == SDLK_ESCAPE:
            print("[play_mode] ESCAPE key pressed, quitting application")
            app_framework.quit()
            return

        # 페이드인 중일 때는 플레이어 이동 이벤트만 무시하고 나머지는 처리
        if is_fading_to_victory:
            # extras 레이어의 플레이어는 이동 이벤트 무시 (하지만 다른 이벤트는 처리 가능)
            # UI와 커서 이벤트는 처리 (인벤토리 조작 등)
            for o in list(world['ui']):
                try:
                    if hasattr(o, 'handle_event'):
                        o.handle_event(e)
                except Exception:
                    print(f'\033[91m[play_mode] handle_event error in ui {o.__class__.__name__}\033[0m')
                    pass
            for o in list(world['cursor']):
                try:
                    if hasattr(o, 'handle_event'):
                        o.handle_event(e)
                except Exception:
                    print(f'\033[91m[play_mode] handle_event error in cursor {o.__class__.__name__}\033[0m')
                    pass
            # 페이드인 중에는 다음 이벤트로 넘어감 (entities와 extras의 이동 이벤트 무시)
            continue

        # 일반 게임 플레이 중에는 모든 이벤트 처리
        # broadcast to entities -> extras -> ui -> cursor
        for o in list(world['entities']):
            try:
                if hasattr(o, 'handle_event'):
                    o.handle_event(e)
            except Exception:
                print(f'\033[91m[play_mode] handle_event error in entity {o.__class__.__name__}\033[0m')
                pass

        # extras 레이어의 객체들도 이벤트 처리
        for o in list(world['extras']):
            try:
                if hasattr(o, 'handle_event'):
                    o.handle_event(e)
            except Exception:
                print(f'\033[91m[play_mode] handle_event error in extras {o.__class__.__name__}\033[0m')
                pass

        for o in list(world['ui']):
            try:
                if hasattr(o, 'handle_event'):
                    o.handle_event(e)
            except Exception:
                print(f'\033[91m[play_mode] handle_event error in ui {o.__class__.__name__}\033[0m')
                pass
        for o in list(world['cursor']):
            try:
                if hasattr(o, 'handle_event'):
                    o.handle_event(e)
            except Exception:
                print(f'\033[91m[play_mode] handle_event error in cursor {o.__class__.__name__}\033[0m')
                pass


def update():
    global is_stage_cleared, loading_screen, is_loading, camera, elapsed_time, is_fading_to_victory, victory_fade_elapsed

    # 로딩 중이면 로딩 화면만 업데이트
    if is_loading and loading_screen:
        loading_screen.update()

        # 로딩이 완료되었으면 실제 스테이지 전환
        if loading_screen.is_complete:
            _complete_stage_change()
            print(f'[play_mode] 스테이지 {current_stage_index + 1} 로딩 완료, 전환 완료')

        return  # 로딩 중에는 게임 로직 업데이트 안 함

    # 승리 페이드인 중이면 페이드인 타이머만 업데이트
    if is_fading_to_victory:
        dt = game_framework.get_delta_time()
        victory_fade_elapsed += dt

        # 페이드인이 완료되면 victory_mode로 전환
        if victory_fade_elapsed >= victory_fade_duration:
            print("[play_mode] 페이드인 완료, victory_mode로 전환")
            player = world.get('player')
            survival_time = elapsed_time
            game_framework.change_state(victory_mode, player, survival_time)

        return  # 페이드인 중에는 게임 로직 업데이트 안 함

    # 경과 시간 누적 (로딩 중이 아닐 때만)
    dt = game_framework.get_delta_time()
    elapsed_time += dt

    # 카메라 업데이트 추가
    if camera is not None:
        camera.update()

    # 일반 게임 업데이트
    for layer_name in ['bg', 'effects_back', 'entities', 'effects_front', 'ui', 'extra_bg', 'extras', 'cursor']:
        new_list = []
        for o in list(world[layer_name]):
            try:
                if hasattr(o, 'update'):
                    alive = o.update()
                    if alive is False:
                        continue

                # mark_for_removal 플래그 확인
                if hasattr(o, 'mark_for_removal') and o.mark_for_removal:
                    print(f"[Update] {o.__class__.__name__} 제거됨")
                    continue  # 제거 표시된 객체는 new_list에 추가하지 않음

                new_list.append(o)
            except Exception:
                try:
                    new_list.append(o)
                except Exception:
                    print(f'\033[91m[play_mode] update error in layer {layer_name} object {o.__class__.__name__}\033[0m')
                    pass
        world[layer_name][:] = new_list

    # 충돌 검사 시스템
    player = world.get('player')

    # 충돌한 이펙트와 투사체를 추적하기 위한 집합
    effects_to_remove = set()
    projectiles_to_remove = set()

    # 1. 플레이어 공격 이펙트와 몬스터 충돌 검사
    for effect in world['effects_front']:
        # VFX_Tier1_Sword_Swing 이펙트인지 확인 (플레이어 공격)
        if hasattr(effect, 'frames') and hasattr(effect, 'scale_factor'):
            for entity in world['entities']:
                # 플레이어가 아닌 엔티티 (몬스터)인지 확인
                if entity != player and hasattr(entity, 'check_collision_with_effect'):
                    if entity.check_collision_with_effect(effect):
                        # 디버그: 충돌 정보 출력
                        attacker_name = "Player"
                        if hasattr(effect, 'owner'):
                            attacker_name = effect.owner.__class__.__name__
                        target_name = entity.__class__.__name__
                        print(f"[COLLISION] {attacker_name} 공격 이펙트 -> {target_name} 피격!")
                        # 충돌 시 이펙트는 유지 (여러 적을 동시에 타격 가능)
                        pass

    # 1-2. 몬스터 공격 이펙트와 플레이어 충돌 검사
    # 피격 판정이 필요한 몬스터 공격 이펙트 클래스 리스트
    from .projectile import Projectile
    from .monsters.cat_theif import CatThiefSwingEffect  # CatThiefSwingEffect import 추가
    from .monsters.Boss_Logic.panther_assassin_2pattern import PantherBladeSwingEffect  # PantherBladeSwingEffect import 추가
    from .monsters.Boss_Logic.panther_assassin_3pattern import PantherCombo1SwingEffect
    from .monsters.Boss_Logic.panther_assassin_3pattern import PantherCombo2SwingEffect


    MONSTER_ATTACK_EFFECT_TYPES = [
        CatThiefSwingEffect,
        PantherBladeSwingEffect,
        PantherCombo1SwingEffect,
        PantherCombo2SwingEffect,
    ]

    if player:
        for effect in world['effects_front']:
            # 몬스터 공격 이펙트 타입 체크
            for effect_type in MONSTER_ATTACK_EFFECT_TYPES:
                if isinstance(effect, effect_type):
                    # 이미 맞춘 플레이어는 다시 체크하지 않음 (중복 타격 방지)
                    if not effect.has_hit_player:
                        # 먼저 방패로 방어할 수 있는지 체크
                        shield_blocked = False
                        if hasattr(player, 'shield') and player.shield:
                            if hasattr(player.shield, 'check_effect_block'):
                                if player.shield.check_effect_block(effect):
                                    # 방패로 막았으면 막은 것으로 판별, 이펙트는 지우지 않음
                                    effect.has_hit_player = True
                                    shield_blocked = True
                                    print(f"[COLLISION] Player가 방패로 {effect.__class__.__name__} 방어!")

                        # 방패로 막지 못했을 때만 플레이어와 충돌 검사
                        if not shield_blocked:
                            if hasattr(player, 'check_collision_with_effect'):
                                if player.check_collision_with_effect(effect):
                                    # 충돌 시 플레이어 타격 처리
                                    effect.has_hit_player = True
                                    # 디버그: 충돌 정보 출력
                                    attacker_name = "Unknown"
                                    if hasattr(effect, 'owner') and effect.owner:
                                        attacker_name = effect.owner.__class__.__name__
                                    print(f"[COLLISION] {attacker_name} {effect.__class__.__name__} -> Player 피격!")

                    # 해당 타입으로 확인되면 다른 타입 체크는 불필요
                    break

    # 2. 투사체와 충돌 검사 (일반화된 Projectile 기반)
    if player:
        for projectile in world['effects_front']:
            # Projectile 클래스를 상속받은 모든 투사체 체크
            if isinstance(projectile, Projectile):
                # 몬스터가 쏜 투사체는 플레이어와 충돌 검사
                if not projectile.from_player:
                    if hasattr(player, 'check_collision_with_projectile'):
                        if player.check_collision_with_projectile(projectile):
                            # 디버그: 충돌 정보 출력
                            attacker_name = "Unknown"
                            if hasattr(projectile, 'owner') and projectile.owner:
                                attacker_name = projectile.owner.__class__.__name__
                            print(f"[COLLISION] {attacker_name} 투사체 -> Player 피격!")
                            projectiles_to_remove.add(projectile)
                # 플레이어가 쏜 투사체는 몬스터와 충돌 검사
                else:
                    for entity in world['entities']:
                        if entity != player and hasattr(entity, 'check_collision_with_projectile'):
                            if entity.check_collision_with_projectile(projectile):
                                # 디버그: 충돌 정보 출력
                                target_name = entity.__class__.__name__
                                print(f"[COLLISION] Player 투사체 -> {target_name} 피격!")
                                projectiles_to_remove.add(projectile)
                                break  # 하나의 적과 충돌하면 투사체 제거

    # 충돌한 투사체 제거
    if projectiles_to_remove:
        world['effects_front'] = [obj for obj in world['effects_front'] if obj not in projectiles_to_remove]

    # 스테이지 클리어 조건 확인 (몬스터가 모두 제거되었는지)
    # 'entities' 레이어에 플레이어만 남아있는지 확인합니다.
    if not is_stage_cleared and len(world['entities']) == 1 and world.get('player') in world['entities']:
        # 이전에 몬스터가 1마리 이상 있었는지 확인하는 조건이 필요할 수 있습니다.
        # 여기서는 간단히 몬스터가 없으면 클리어로 간주합니다.
        print("Stage cleared!")
        is_stage_cleared = True # 중복 호출 방지
        change_stage(current_stage_index + 1)


def draw():
    global camera, victory_fade_image, victory_fade_elapsed, victory_fade_duration
    p2.clear_canvas()

    # 로딩 중이면 로딩 화면만 그리기
    if is_loading and loading_screen:
        loading_screen.draw()
    else:
        # 일반 게임 화면 그리기
        # 1. FixedBackground 먼저 그리기 (카메라 영향 없음)
        from .background import FixedBackground
        from .equipment import ShieldRangeEffect

        for o in world['bg']:
            if isinstance(o, FixedBackground):
                try:
                    if hasattr(o, 'draw'):
                        o.draw()  # FixedBackground는 인자 없이 호출
                except Exception as ex:
                    print(f'\033[91m[play_mode] FixedBackground 그리기 오류: {ex}\033[0m')
                    pass

        # 2. 나머지 객체들은 카메라 좌표 적용하여 그리기
        for layer_name in ['bg', 'walls', 'upper_ground', 'effects_back', 'entities', 'effects_front', 'extra_bg', 'extras']:
            for o in world[layer_name]:
                # FixedBackground는 이미 그렸으므로 스킵
                if isinstance(o, FixedBackground):
                    continue

                try:
                    if hasattr(o, 'draw'):
                        # ShieldRangeEffect는 특별 처리 (플레이어 위치 기준)
                        if isinstance(o, ShieldRangeEffect):
                            if hasattr(o, 'player') and o.player:
                                if camera is not None:
                                    draw_x, draw_y = camera.apply(o.player.x, o.player.y)
                                else:
                                    draw_x, draw_y = o.player.x, o.player.y
                                o.draw(draw_x, draw_y)
                        # x, y 속성이 있는 객체는 카메라 좌표로 변환하여 그리기
                        elif hasattr(o, 'x') and hasattr(o, 'y'):
                            if camera is not None:
                                draw_x, draw_y = camera.apply(o.x, o.y)
                            else:
                                draw_x, draw_y = o.x, o.y
                            o.draw(draw_x, draw_y)
                        else:
                            # x, y 속성이 없는 객체는 그대로 그리기
                            o.draw()
                except Exception as ex:
                    print(f'\033[91m[play_mode] {layer_name} 레이어의 {o.__class__.__name__} 그리기 오류: {ex}\033[0m')
                    pass

        # 3. UI와 커서는 카메라 적용하지 않음 (고정 UI)
        for o in world['ui']:
            try:
                if hasattr(o, 'draw'):
                    o.draw()
            except Exception as ex:
                print(f'\033[91m[play_mode] UI 레이어의 {o.__class__.__name__} 그리기 오류 : {ex}\033[0m')
                pass

        for o in world['cursor']:
            try:
                if hasattr(o, 'draw'):
                    o.draw()
            except Exception as ex:
                print(f'\033[91m[play_mode] Cursor 레이어의 {o.__class__.__name__} 그리기 오류 : {ex}\033[0m')
                pass

        # 4. 승리 페이드인 효과 그리기 (기존 화면 위에 오버레이)
        if is_fading_to_victory and victory_fade_image:
            canvas_w = p2.get_canvas_width()
            canvas_h = p2.get_canvas_height()

            # 페이드인 진행률 계산 (0.0 ~ 1.0)
            fade_progress = min(victory_fade_elapsed / victory_fade_duration, 1.0)

            # 이미지 투명도 설정 및 그리기
            victory_fade_image.opacify(fade_progress)
            victory_fade_image.draw(canvas_w // 2, canvas_h // 2, canvas_w, canvas_h)

    p2.update_canvas()
