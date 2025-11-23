# game_logic.play_mode: play mode state that creates Player, InventoryOverlay, Cursor
# minimal, compatible with existing game_logic modules
import pico2d as p2
from sdl2 import SDL_QUIT, SDL_KEYDOWN, SDLK_ESCAPE

import game_framework
from .player import Player
from .ui_overlay import InventoryOverlay, HealthBar, ManaBar
from .cursor import Cursor
from .loading_screen import LoadingScreen
from . import defeat_mode
# 사용할 스테이지 모듈들을 import 합니다.
from .stages import stage_1, stage_2

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
stages = [stage_1, stage_2] # 모든 스테이지 모듈을 리스트로 관리
current_stage_index = 0
is_stage_cleared = False

# 로딩 화면 관리
loading_screen = None
is_loading = False
next_stage_to_load = None


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
    global current_stage_index, loading_screen, is_loading, next_stage_to_load

    # 다음 스테이지 인덱스 확인
    if next_stage_index >= len(stages):
        # 모든 스테이지 클리어 시 게임 종료 또는 다른 모드로 전환
        print("All stages cleared!")
        game_framework.quit()
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

def _complete_stage_change():
    """로딩이 완료된 후 실제 스테이지 전환을 수행"""
    global current_stage_index, world, is_stage_cleared, loading_screen, is_loading, next_stage_to_load, camera

    print(f"[_complete_stage_change] 스테이지 {next_stage_to_load + 1} 로드 시작")

    # 현재 스테이지의 몬스터, 배경 등 제거 (플레이어는 유지)
    player = world.get('player')
    world['entities'] = [player] if player else []
    world['bg'].clear()
    # 다른 레이어도 필요에 따라 초기화
    world['effects_back'].clear()
    world['effects_front'].clear()

    # 다음 스테이지 인덱스로 변경
    current_stage_index = next_stage_to_load

    # 새 스테이지 로드
    stages[current_stage_index].load(world)

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

            # 카메라가 존재하면 카메라도 즉시 플레이어 위치로 동기화
            # (부드러운 전환 없이 즉시 이동)
            if camera is not None:
                camera.x = new_x
                camera.y = new_y
                print(f"[_complete_stage_change] 카메라 위치 동기화: ({camera.x}, {camera.y})")
        else:
            print(f"[_complete_stage_change] 플레이어 시작 위치 정보 없음, 현재 위치 유지")

    # 새 스테이지의 배경 범위를 다시 계산하여 카메라 범위 업데이트
    if camera is not None:
        try:
            min_x, max_x, min_y, max_y = calculate_background_bounds()
            map_width = max_x - min_x
            map_height = max_y - min_y

            # 카메라의 맵 크기 및 오프셋 업데이트
            camera.map_width = map_width
            camera.map_height = map_height
            camera.map_offset_x = (min_x + max_x) / 2
            camera.map_offset_y = (min_y + max_y) / 2

            print(f"[_complete_stage_change] 카메라 맵 범위 업데이트: {map_width:.1f}x{map_height:.1f}")
        except Exception as ex:
            print(f"\033[91m[_complete_stage_change] 카메라 범위 업데이트 실패: {ex}\033[0m")

    is_stage_cleared = False

    # 로딩 화면 종료
    loading_screen = None
    is_loading = False
    next_stage_to_load = None

    print(f"[_complete_stage_change] Changed to Stage {current_stage_index + 1}")

def enter(player=None):
    global world, current_stage_index, is_stage_cleared
    print("[play_mode] Starting enter()...")

    # clear existing
    for k in list(world.keys()):
        try:
            if isinstance(world[k], list):
                world[k].clear()
        except Exception:
            pass

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
                self.x = 400
                self.y = 300
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

    # Camera 초기화 (Player를 target으로 설정)
    # ground 레이어의 실제 배경 범위를 계산하여 카메라 제한 범위로 사용
    try:
        # 배경 범위 계산 (ground 레이어의 모든 객체 고려)
        min_x, max_x, min_y, max_y = calculate_background_bounds()

        # 배경 전체 크기 계산
        map_width = max_x - min_x
        map_height = max_y - min_y

        screen_width = p2.get_canvas_width()
        screen_height = p2.get_canvas_height()

        global camera
        camera = Camera(player, map_width, map_height, screen_width, screen_height)

        # 카메라에 실제 배경 범위의 중심점 정보 전달 (오프셋 계산용)
        camera.map_offset_x = (min_x + max_x) / 2
        camera.map_offset_y = (min_y + max_y) / 2

        print(f"[play_mode] Camera initialized for player at ({player.x}, {player.y})")
        print(f"[play_mode] Map size: {map_width:.1f} x {map_height:.1f}, Offset: ({camera.map_offset_x:.1f}, {camera.map_offset_y:.1f})")
    except Exception as ex:
        print(f"[play_mode] Camera initialization failed: {ex}")

    print("[play_mode] Loading first stage...")
    # 첫 번째 스테이지 로드
    current_stage_index = 0
    is_stage_cleared = False
    stages[current_stage_index].load(world)
    print(f"[play_mode] Entered play_mode, loaded Stage {current_stage_index + 1}")

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
            app_framework.quit()
            return
        if e.type == SDL_KEYDOWN and getattr(e, 'key', None) == SDLK_ESCAPE:
            app_framework.quit()
            return
        # broadcast to entities -> ui -> cursor
        for o in list(world['entities']):
            try:
                if hasattr(o, 'handle_event'):
                    o.handle_event(e)
            except Exception:
                pass
        for o in list(world['ui']):
            try:
                if hasattr(o, 'handle_event'):
                    o.handle_event(e)
            except Exception:
                pass
        for o in list(world['cursor']):
            try:
                if hasattr(o, 'handle_event'):
                    o.handle_event(e)
            except Exception:
                pass


def update():
    global is_stage_cleared, loading_screen, is_loading, camera

    # 로딩 중이면 로딩 화면만 업데이트
    if is_loading and loading_screen:
        loading_screen.update()

        # 로딩이 완료되었으면 실제 스테이지 전환
        if loading_screen.is_complete:
            _complete_stage_change()
            print(f'[play_mode] 스테이지 {current_stage_index + 1} 로딩 완료, 전환 완료')

        return  # 로딩 중에는 게임 로직 업데이트 안 함

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
                    pass
        world[layer_name][:] = new_list

    # 충돌 검사 시스템
    from .projectile import Projectile
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
    global camera
    p2.clear_canvas()

    # 로딩 중이면 로딩 화면만 그리기
    if is_loading and loading_screen:
        loading_screen.draw()
    else:
        # 일반 게임 화면 그리기 (카메라 적용)
        # 배경, 벽, 엔티티 등은 카메라 위치를 적용하여 그리기
        for layer_name in ['bg', 'walls', 'upper_ground', 'effects_back', 'entities', 'effects_front', 'extra_bg', 'extras']:
            for o in world[layer_name]:
                try:
                    if hasattr(o, 'draw'):
                        # x, y 속성이 있는 객체는 카메라 좌표로 변환하여 그리기
                        if hasattr(o, 'x') and hasattr(o, 'y'):
                            if camera is not None:
                                draw_x, draw_y = camera.apply(o.x, o.y)
                            else:
                                draw_x, draw_y = o.x, o.y
                            o.draw(draw_x, draw_y)
                        else:
                            # x, y 속성이 없는 객체는 그대로 그리기
                            o.draw()
                except Exception:
                    pass

        # UI와 커서는 카메라 적용하지 않음 (고정 UI)
        for o in world['ui']:
            try:
                if hasattr(o, 'draw'):
                    o.draw()
            except Exception:
                pass

        for o in world['cursor']:
            try:
                if hasattr(o, 'draw'):
                    o.draw()
            except Exception:
                pass

    p2.update_canvas()
