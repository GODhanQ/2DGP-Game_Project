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
from PIL import Image
import math

# world layers: keep same keys as original main.py
world = {
    'sky' : [],
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
world['player'] = world['entities']  # 플레이어 참조를 위한 키 추가
world_list = ['sky', 'ground', 'upper_ground', 'walls', 'effects_back', 'entities', 'effects_front', 'ui', 'extra_bg', 'extras', 'cursor']

class Camera:
    def __init__(self, target, map_width, map_height, screen_width, screen_height):
        self.target = target
        self.x = target.x
        self.y = target.y
        self.map_width = map_width
        self.map_height = map_height
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.smooth = 0.1  # 부드러운 이동 정도 (0~1)

    def update(self):
        # 플레이어 위치를 부드럽게 따라감 (LERP)
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
        # self.x, self.y는 맵 중심 기준 카메라 위치
        # 화면 중앙이 (0,0)이 되도록 보정

    def apply(self, obj_x, obj_y):
        # 카메라 위치만큼 오브젝트 위치 보정 (화면 중앙 기준)
        # obj_x, obj_y: 맵 중심(0,0) 기준 좌표
        # 반환값: 화면에 그릴 좌표 (pico2d 기준, 화면 중앙이 0,0)
        half_w = self.screen_width // 2
        half_h = self.screen_height // 2
        return obj_x - self.x + half_w, obj_y - self.y + half_h

# Camera 객체를 전역으로 선언
camera = None

def calculate_background_bounds():
    """
    sky와 ground 레이어의 모든 배경 객체들의 실제 범위를 계산합니다.
    모든 배경 이미지를 고려하여 최소/최대 x, y 좌표를 반환합니다.

    Returns:
        tuple: (min_x, max_x, min_y, max_y) - 배경이 존재하는 실제 영역의 경계
    """
    min_x = float('inf')
    max_x = float('-inf')
    min_y = float('inf')
    max_y = float('-inf')

    # sky와 ground 레이어의 모든 객체를 순회
    for layer_name in ['sky', 'ground']:
        for obj in world[layer_name]:
            # 객체가 x, y, image, scale 속성을 가지고 있는지 확인
            if hasattr(obj, 'x') and hasattr(obj, 'y') and hasattr(obj, 'image') and hasattr(obj, 'scale'):
                # 객체의 중심 좌표
                obj_x = obj.x
                obj_y = obj.y

                # 이미지 크기 계산 (scale 적용)
                img_width = obj.image.w * obj.scale
                img_height = obj.image.h * obj.scale

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

    # 유효한 범위가 계산되지 않은 경우 기본값 반환
    if min_x == float('inf') or max_x == float('-inf'):
        print("[WARNING] 배경 범위 계산 실패, 기본값 사용")
        return (-800, 800, -600, 600)

    print(f"[lobby_mode] 계산된 배경 범위: X({min_x:.1f} ~ {max_x:.1f}), Y({min_y:.1f} ~ {max_y:.1f})")
    return (min_x, max_x, min_y, max_y)

def enter():
    global world, camera
    print("[lobby_mode] Starting enter()...")

    # clear existing
    for k in list(world.keys()):
        try:
            if isinstance(world[k], list):
                world[k].clear()
        except Exception:
            print("\033[91m[lobby_mode] Failed to clear world layer\033[0m")

    # sky
    print("[lobby_mode] Creating Sky...")
    whiteBackPath = 'resources/Texture_organize/Map/Dream_Tree/BackGround/WhiteBG.png'
    skyBackGroundPath = 'resources/Texture_organize/Map/Dream_Tree/BackGround/DreamWorldCloudBall_Gradation.png'
    skyBackPath = 'resources/Texture_organize/Map/Dream_Tree/BackGround/DreamWorldCloud_Back.png'
    skyMidPath = 'resources/Texture_organize/Map/Dream_Tree/BackGround/DreamWorldCloud_Mid.png'
    skyFrontPath = 'resources/Texture_organize/Map/Dream_Tree/BackGround/DreamWorldCloud_Front.png'
    cloudPropPath = 'resources/Texture_organize/Map/Dream_Tree/BackGround/DreamWorldCloud_Prop.png'
    whiteBack = LobbySky(whiteBackPath, 0, 0, 6.5)
    skyBackGround = LobbySky(skyBackGroundPath, 0, 0, 5.4)
    skyBack = LobbySky(skyBackPath, 0, 200)
    skyMid = LobbySky(skyMidPath, 0, 0)
    skyFront = LobbySky(skyFrontPath, 0, -200)
    cloudProp = LobbySky(cloudPropPath, 0, -400)

    world['sky'].append(whiteBack)
    world['sky'].append(skyBackGround)
    world['sky'].append(skyBack)
    world['sky'].append(skyMid)
    world['sky'].append(skyFront)
    world['sky'].append(cloudProp)

    # background
    print("[lobby_mode] Creating Background...")
    bg = LobbyBackGround()
    world['bg'].append(bg)

    # 낭떠러지(투명 영역) 벽 자동 생성
    try:
        print("[DEBUG] wall_blocks 생성 시도 중...")
        # 배경의 화면 위치와 스케일을 전달
        wall_blocks = generate_walls_from_png(
            'resources/Texture_organize/Map/Dream_Tree/BackGround/DreamWorld0.png',
            block_size=8,
            bg_x=bg.x,
            bg_y=bg.y,
            scale=bg.scale
        )
        print(f"[DEBUG] wall_blocks 반환: {len(wall_blocks)}개")
        for wall in wall_blocks:
            world['walls'].append(wall)
            pass
        print(f"[lobby_mode] Generated {len(wall_blocks)} walls from PNG transparency.")
    except Exception as ex:
        print(f"\033[91m[lobby_mode] Wall generation from PNG failed: {ex}\033[0m")

    # create portal to play mode
    print("[lobby_mode] Creating EnterTreePortal...")
    try:
        # 백그라운드 이미지와 스케일에 맞춰 가로 중앙, 세로는 위에서 30% 아래에 배치
        portal_x = bg.x
        portal_y = bg.y + (bg.image.h * bg.scale) / 2 - (bg.image.h * bg.scale) * 0.3
        enterTree = EnterTreePortal(portal_x, portal_y, scale=bg.scale)
        world['upper_ground'].append(enterTree)
        print(f"[lobby_mode] EnterTreePortal created at ({portal_x}, {portal_y}) with scale {bg.scale}")
    except Exception as ex:
        print(f"\033[91m[lobby_mode] Failed to create EnterTreePortal: {ex}\033[0m")

    print("[lobby_mode] Creating player...")
    # create player (use fallback if heavy Player init fails)
    try:
        player = Player()
        player.x = 0  # 화면 중심(0,0)으로 위치 보정
        player.y = 0  # 화면 중심(0,0)으로 위치 보정
        print("[lobby_mode] Player created successfully")
    except Exception as ex:
        print(f"\033[91m[lobby_mode] Player initialization failed, using lightweight fallback: {ex}\033[0m")
        from .inventory import InventoryData, seed_debug_inventory

        class _FallbackPlayer:
            def __init__(self):
                self.x = 0  # 화면 중심(0,0)으로 위치 보정
                self.y = 0  # 화면 중심(0,0)으로 위치 보정
                self.face_dir = 1
                self.scale_factor = 1.0
                self.keys_down = {'w': False, 'a': False, 's': False, 'd': False}
                self.particles = []
                self.attack_effects = []
                self.inventory = InventoryData(cols=6, rows=5)
                try:
                    seed_debug_inventory(self.inventory)
                except Exception:
                    print("\033[91m[lobby_mode] seed_debug_inventory failed\033[0m")
                    pass
                self.inventory_open = False

            def update(self):
                return True

            def rebuild_inventory_passives(self):
                return

            def consume_item_at(self, r, c):
                return False

        player = _FallbackPlayer()

    print("[lobby_mode] Attaching world reference to player...")
    # attach a reference to the current world so player and callbacks can access/modify it
    try:
        player.world = world
    except Exception:
        print("\033[91m[lobby_mode] Failed to attach world to player\033[0m")
    world['player'] = player # 플레이어를 world에 명시적으로 저장
    world['entities'].append(player)

    # Camera 초기화 (Player를 target으로 설정)
    # sky와 ground 레이어의 실제 배경 범위를 계산하여 카메라 제한 범위로 사용
    try:
        # 배경 범위 계산 (sky와 ground 레이어의 모든 객체 고려)
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

        print(f"[lobby_mode] Camera initialized for player at ({player.x}, {player.y})")
        print(f"[lobby_mode] Map size: {map_width:.1f} x {map_height:.1f}, Offset: ({camera.map_offset_x:.1f}, {camera.map_offset_y:.1f})")
    except Exception as ex:
        print(f"\033[91m[lobby_mode] Camera initialization failed: {ex}\033[0m")

    print("[lobby_mode] Creating inventory overlay...")
    # inventory overlay: pass world reference so InventoryOverlay can spawn WorldItem into this world
    try:
        inv = InventoryOverlay(player, world)
        print("[lobby_mode] InventoryOverlay created successfully")
    except Exception as ex:
        print(f"\033[91m[lobby_mode] InventoryOverlay init failed, creating minimal stub: {ex}\033[0m")

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

    print("[lobby_mode] Creating cursor...")
    # cursor on top (safe fallback)
    try:
        cursor = Cursor(player)
        print("[lobby_mode] Cursor created successfully")
    except Exception as ex:
        print(f"\033[91m[lobby_mode] Cursor init failed, using stub cursor: {ex}\033[0m")

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
        print("\033[91m[lobby_mode] Failed to expose world to __main__\033[0m")


def exit():
    for k in list(world.keys()):
        try:
            if isinstance(world[k], list):
                world[k].clear()
        except Exception:
            print("\033[91m[lobby_mode] Failed to clear world layer\033[0m")


def handle_events():
    import game_framework as app_framework

    events = p2.get_events()
    player = world.get('player')
    portal_triggered = False

    for e in events:
        if e.type == SDL_QUIT:
            app_framework.quit()
            return
        if e.type == SDL_KEYDOWN and getattr(e, 'key', None) == SDLK_ESCAPE:
            app_framework.quit()
            return
        # F키 입력 시 포탈 충돌 체크
        if e.type == SDL_KEYDOWN and getattr(e, 'key', None) == p2.SDLK_f:
            for obj in world['upper_ground']:
                if isinstance(obj, EnterTreePortal) and player:
                    if obj.check_player_collision(player):
                        if not portal_triggered:
                            from . import play_mode
                            print('[lobby_mode] EnterTreePortal triggered: switching to play_mode')
                            app_framework.change_state(play_mode)
                            portal_triggered = True

        # broadcast to entities -> ui -> cursor
        for o in list(world['entities']):
            try:
                if hasattr(o, 'handle_event'):
                    o.handle_event(e)
            except Exception:
                print("\033[91m[lobby_mode] Failed to handle event for entity\033[0m")
        for o in list(world['ui']):
            try:
                if hasattr(o, 'handle_event'):
                    o.handle_event(e)
            except Exception:
                print("\033[91m[lobby_mode] Failed to handle event for UI\033[0m")
        for o in list(world['cursor']):
            try:
                if hasattr(o, 'handle_event'):
                    o.handle_event(e)
            except Exception:
                print("\033[91m[lobby_mode] Failed to handle event for cursor\033[0m")


def update():
    global camera
    # 카메라 업데이트 추가
    if camera is not None:
        camera.update()

    # 일반 게임 업데이트
    for layer_name in world_list:
        new_list = []
        for o in list(world[layer_name]):
            try:
                if hasattr(o, 'update'):
                    alive = o.update()
                    if alive is False:
                        continue
            except Exception:
                print("\033[91m[lobby_mode] Failed to update object\033[0m")

            # mark_for_removal 플래그 확인
            if hasattr(o, 'mark_for_removal') and o.mark_for_removal:
                print(f"[Update] {o.__class__.__name__} 제거됨")
                continue  # 제거 표시된 객체는 new_list에 추가하지 않음

            new_list.append(o)
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

    # 포탈 위에 텍스트 표시
    for obj in world['upper_ground']:
        if isinstance(obj, EnterTreePortal) and player:
            if obj.check_player_collision(player):
                obj.trigger = True
            else:
                obj.trigger = False

def draw():
    global camera
    p2.clear_canvas()
    # 하늘을 가장 먼저 그리기 (배경 뒤)
    for obj in world['sky']:
        if hasattr(obj, 'x') and hasattr(obj, 'y'):
            if camera is not None:
                draw_x, draw_y = camera.apply(obj.x, obj.y)
            else:
                draw_x, draw_y = obj.x, obj.y
            if hasattr(obj, 'draw'):
                obj.draw(draw_x, draw_y)
        else:
            if hasattr(obj, 'draw'):
                obj.draw()

    # 나머지 레이어들 (배경, 벽, 엔티티 등)
    for layer in ['ground', 'walls', 'upper_ground', 'entities', 'effects_back', 'effects_front', 'extra_bg', 'extras']:
        for obj in world[layer]:
            if hasattr(obj, 'x') and hasattr(obj, 'y'):
                if camera is not None:
                    draw_x, draw_y = camera.apply(obj.x, obj.y)
                else:
                    draw_x, draw_y = obj.x, obj.y
                if hasattr(obj, 'draw'):
                    obj.draw(draw_x, draw_y)
            else:
                if hasattr(obj, 'draw'):
                    obj.draw()
    # UI, cursor 등은 카메라 적용하지 않음
    for obj in world['ui']:
        if hasattr(obj, 'draw'):
            obj.draw()
    for obj in world['cursor']:
        if hasattr(obj, 'draw'):
            obj.draw()
    p2.update_canvas()

class LobbySky:
    def __init__(self, path, x=0, y=0, scale=3):
        self.image = p2.load_image(path)
        self.scale = scale
        self.x = x  # 화면 중심(0,0) 기준
        self.y = y  # 화면 중심(0,0) 기준

    def update(self):
        pass

    def draw(self, draw_x, draw_y):
        self.image.draw(draw_x, draw_y, self.image.w * self.scale * 2,
                        self.image.h * self.scale * 1.5)
        # 디버그용 히트박스 (필요시 주석 처리)
        # p2.draw_rectangle(draw_x - (self.image.w * self.scale) / 2,
        #                   draw_y - (self.image.h * self.scale) / 2,
        #                   draw_x + (self.image.w * self.scale) / 2,
        #                   draw_y + (self.image.h * self.scale) / 2)


class LobbyBackGround:
    image = None
    def __init__(self):
        if LobbyBackGround.image is None:
            LobbyBackGround.image = p2.load_image('resources/Texture_organize/Map/Dream_Tree/BackGround/DreamWorld0.png')
        self.scale = 6.5
        self.x = 0  # 화면 중심(0,0)으로 위치 보정
        self.y = 0  # 화면 중심(0,0)으로 위치 보정

    def update(self):
        pass

    def draw(self, draw_x, draw_y):
        LobbyBackGround.image.draw(draw_x, draw_y, LobbyBackGround.image.w * self.scale, LobbyBackGround.image.h * self.scale)
        # p2.draw_rectangle(draw_x - (LobbyBackGround.image.w * self.scale) / 2,
        #                   draw_y - (LobbyBackGround.image.h * self.scale) / 2,
        #                   draw_x + (LobbyBackGround.image.w * self.scale) / 2,
        #                   draw_y + (LobbyBackGround.image.h * self.scale) / 2)

class EnterTreePortal:
    # frame lists (class-level so images are loaded only once)
    portalImagesBegin = []
    portalImagesCycle = []
    portalFXBegin = []
    portalFXCycle = []
    loaded = False

    def __init__(self, x, y, scale=3.0):
        # load images once (safe: catch missing files)
        if not EnterTreePortal.loaded:
            try:
                for i in range(18):
                    path = f'resources/Texture_organize/Map/Dream_Tree/Dream_Door/DreamDoor_Begin{i:02d}.png'
                    EnterTreePortal.portalImagesBegin.append(p2.load_image(path))
            except Exception:
                EnterTreePortal.portalImagesBegin = []
            try:
                # cycle uses a single image in original assets, but keep as list for consistency
                EnterTreePortal.portalImagesCycle.append(p2.load_image('resources/Texture_organize/Map/Dream_Tree/Dream_Door/DreamDoor_Cycle00.png'))
            except Exception:
                EnterTreePortal.portalImagesCycle = []
            try:
                for i in range(18):
                    path = f'resources/Texture_organize/Map/Dream_Tree/Dream_Door/DreamDoorFX_Begin{i:02d}.png'
                    EnterTreePortal.portalFXBegin.append(p2.load_image(path))
            except Exception:
                EnterTreePortal.portalFXBegin = []
            try:
                for i in range(11):
                    path = f'resources/Texture_organize/Map/Dream_Tree/Dream_Door/DreamDoorFX_Cycle{i:02d}.png'
                    EnterTreePortal.portalFXCycle.append(p2.load_image(path))
            except Exception:
                EnterTreePortal.portalFXCycle = []
            EnterTreePortal.loaded = True

        self.x = x
        self.y = y
        self.scale = scale
        # self.trigger_radius = 50  # 플레이어가 접근해야 하는 반경
        self.trigger = False

        # animation state
        self.begin_animation_done = False
        self.frame_idx = 0
        self.fx_idx = 0
        self.frame_dt = 0.0
        self.fx_dt = 0.0
        self.frame_duration = 0.06  # seconds per frame
        self.fx_duration = 0.06
        self.last_time = p2.get_time()

    def update(self):
        # advance animation based on time delta
        now = p2.get_time()
        dt = now - getattr(self, 'last_time', now)
        self.last_time = now
        # update portal image animation
        self.frame_dt += dt
        if not self.begin_animation_done and EnterTreePortal.portalImagesBegin:
            # play begin sequence once
            if self.frame_dt >= self.frame_duration:
                steps = int(self.frame_dt / self.frame_duration)
                self.frame_dt -= steps * self.frame_duration
                self.frame_idx += steps
                if self.frame_idx >= len(EnterTreePortal.portalImagesBegin):
                    # start cycle
                    self.begin_animation_done = True
                    self.frame_idx = 0
        else:
            # loop cycle frames
            if EnterTreePortal.portalImagesCycle:
                if self.frame_dt >= self.frame_duration:
                    steps = int(self.frame_dt / self.frame_duration)
                    self.frame_dt -= steps * self.frame_duration
                    self.frame_idx = (self.frame_idx + steps) % max(1, len(EnterTreePortal.portalImagesCycle))

        # update FX animation: try to play begin and then cycle
        self.fx_dt += dt
        if not self.begin_animation_done and EnterTreePortal.portalFXBegin:
            if self.fx_dt >= self.fx_duration:
                steps = int(self.fx_dt / self.fx_duration)
                self.fx_dt -= steps * self.fx_duration
                self.fx_idx += steps
                # clamp fx_idx so it doesn't grow unbounded; allow it to loop during begin
                if self.fx_idx >= len(EnterTreePortal.portalFXBegin):
                    self.fx_idx = 0
        else:
            if EnterTreePortal.portalFXCycle:
                if self.fx_dt >= self.fx_duration:
                    steps = int(self.fx_dt / self.fx_duration)
                    self.fx_dt -= steps * self.fx_duration
                    self.fx_idx = (self.fx_idx + steps) % max(1, len(EnterTreePortal.portalFXCycle))

        return True

    def draw(self, draw_x, draw_y):
        # draw portal image (begin or cycle)
        try:
            if not self.begin_animation_done and EnterTreePortal.portalImagesBegin:
                img = EnterTreePortal.portalImagesBegin[min(self.frame_idx, len(EnterTreePortal.portalImagesBegin)-1)]
                img.draw(draw_x, draw_y, img.w * self.scale, img.h * self.scale)
            elif EnterTreePortal.portalImagesCycle:
                img = EnterTreePortal.portalImagesCycle[self.frame_idx % len(EnterTreePortal.portalImagesCycle)]
                img.draw(draw_x, draw_y, img.w * self.scale, img.h * self.scale)
        except Exception:
            # drawing failure should not crash the game
            pass

        # draw FX overlay
        try:
            if not self.begin_animation_done and EnterTreePortal.portalFXBegin:
                fx = EnterTreePortal.portalFXBegin[self.fx_idx % len(EnterTreePortal.portalFXBegin)]
                fx.draw(draw_x, draw_y, fx.w * self.scale, fx.h * self.scale)
            elif EnterTreePortal.portalFXCycle:
                fx = EnterTreePortal.portalFXCycle[self.fx_idx % len(EnterTreePortal.portalFXCycle)]
                fx.draw(draw_x, draw_y, fx.w * self.scale, fx.h * self.scale)
        except Exception:
            pass

        # 포탈 위에 텍스트 그리기
        if self.trigger:
            try:
                # print(f'[lobby_mode] Drawing portal text at ({draw_x}, {draw_y})')
                font = p2.load_font('resources/Fonts/pixelroborobo.otf', 20)
                text = "[F] 모험하기"
                font_size = 40
                approx_width = int(len(text) * font_size * 0.4)
                font.draw(draw_x - approx_width // 2, draw_y + 10 * self.scale, text, (255, 255, 0))
            except Exception as ex:
                print(f'[lobby_mode] 포탈 텍스트 그리기 실패: {ex}')

    def check_player_collision(self, player):
        # 플레이어와 포탈의 히트박스 충돌 검사
        # 플레이어의 크기(w, h)는 기본값 32x32로 가정, 필요시 Player에서 가져올 것
        px = getattr(player, 'x', 0)
        py = getattr(player, 'y', 0)
        pw = getattr(player, 'w', 32)
        ph = getattr(player, 'h', 32)
        # 포탈의 히트박스는 중심 기준, 크기는 이미지 크기 * scale * 0.5 (적당히 조정)
        portal_w = 61 * self.scale
        portal_h = 47 * self.scale
        portal_x = self.x - portal_w / 2
        portal_y = self.y - portal_h / 2
        return (px < portal_x + portal_w and px + pw > portal_x and
                py < portal_y + portal_h and py + ph > portal_y)

class LobbyWall:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h


    def check_collision(self, px, py, pw, ph):
        # 플레이어와 벽의 사각형 충돌 검사
        return (self.x < px + pw and self.x + self.w > px and
                self.y < py + ph and self.y + self.h > py)

    def draw(self, draw_x, draw_y):
        # 카메라 적용 좌표로 벽 영역을 빨간색으로 표시
        try:
            # p2.draw_rectangle(draw_x, draw_y, draw_x + self.w, draw_y + self.h)
            pass
        except Exception as ex:
            print(f'[LobbyWall] draw() 실패 at ({draw_x}, {draw_y}, {self.w}, {self.h}), Exception {ex}')

def generate_walls_from_png(png_path, block_size=16, bg_x=None, bg_y=None, scale=1.0):
    print(f"[DEBUG] generate_walls_from_png 시작: {png_path}, block_size={block_size}, bg_x={bg_x}, bg_y={bg_y}, scale={scale}")
    try:
        img = Image.open(png_path).convert('RGBA')
    except Exception as ex:
        print(f"[DEBUG] 이미지 열기 실패: {ex}")
        return []
    width, height = img.size
    walls = []
    pixels = img.load()
    transparent_count = 0
    # 배경 이미지의 화면 내 좌표계 기준 좌표 계산
    if bg_x is None: bg_x = width * scale / 2
    if bg_y is None: bg_y = height * scale / 2
    screen_left = bg_x - (width * scale) / 2
    screen_top = bg_y + (height * scale) / 2
    for y in range(0, height, block_size):
        for x in range(0, width, block_size):
            is_transparent = False
            for dy in range(block_size):
                for dx in range(block_size):
                    if x+dx < width and y+dy < height:
                        _, _, _, alpha = pixels[x+dx, y+dy]
                        if alpha == 0:
                            is_transparent = True
                            transparent_count += 1
                            break
                if is_transparent:
                    break
            if is_transparent:
                # 이미지 좌표를 화면 좌표로 변환 (좌상단 기준)
                wall_x_img = x
                wall_y_img = height - y - block_size
                wall_x_screen = screen_left + wall_x_img * scale
                wall_y_screen = bg_y - (height * scale) / 2 + wall_y_img * scale
                walls.append(LobbyWall(wall_x_screen, wall_y_screen, block_size * scale, block_size * scale))
    print(f"[DEBUG] 투명 픽셀 수: {transparent_count}, 생성된 벽 수: {len(walls)}")
    return walls
