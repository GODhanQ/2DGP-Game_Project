# game_logic.play_mode: play mode state that creates Player, InventoryOverlay, Cursor
# minimal, compatible with existing game_logic modules
import pico2d as p2
from sdl2 import SDL_QUIT, SDL_KEYDOWN, SDLK_ESCAPE

import game_framework
from .player import Player
from .ui_overlay import InventoryOverlay, HealthBar, ManaBar
from .cursor import Cursor
from .loading_screen import LoadingScreen
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
    global current_stage_index, world, is_stage_cleared, loading_screen, is_loading, next_stage_to_load

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
            player.x = player_start_pos['x']
            player.y = player_start_pos['y']
            print(f"[_complete_stage_change] 플레이어 위치 설정: ({player.x}, {player.y})")
        else:
            print(f"[_complete_stage_change] 플레이어 시작 위치 정보 없음, 현재 위치 유지")

    is_stage_cleared = False

    # 로딩 화면 종료
    loading_screen = None
    is_loading = False
    next_stage_to_load = None

    print(f"[_complete_stage_change] Changed to Stage {current_stage_index + 1}")

def enter():
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
        player = Player()
        print("[play_mode] Player created successfully")
    except Exception as ex:
        print('[play_mode] Player initialization failed, using lightweight fallback:', ex)
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
    global is_stage_cleared, loading_screen, is_loading

    # 로딩 중이면 로딩 화면만 업데이트
    if is_loading and loading_screen:
        loading_screen.update()

        # 로딩이 완료되었으면 실제 스테이지 전환
        if loading_screen.is_complete:
            _complete_stage_change()

        return  # 로딩 중에는 게임 로직 업데이트 안 함

    # 일반 게임 업데이트
    for layer_name in ['bg', 'effects_back', 'entities', 'effects_front', 'ui', 'cursor']:
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
    p2.clear_canvas()

    # 로딩 중이면 로딩 화면만 그리기
    if is_loading and loading_screen:
        loading_screen.draw()
    else:
        # 일반 게임 화면 그리기
        for layer_name in ['bg', 'effects_back', 'entities', 'effects_front', 'ui', 'cursor']:
            for o in world[layer_name]:
                try:
                    if hasattr(o, 'draw'):
                        o.draw()
                except Exception:
                    pass

    p2.update_canvas()
