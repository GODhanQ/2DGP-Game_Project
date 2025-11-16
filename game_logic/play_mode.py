# game_logic.play_mode: play mode state that creates Player, InventoryOverlay, Cursor
# minimal, compatible with existing game_logic modules
import pico2d as p2
from sdl2 import SDL_QUIT, SDL_KEYDOWN, SDLK_ESCAPE

from . import game_framework
from .player import Player
from .ui_overlay import InventoryOverlay
from .cursor import Cursor
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

def change_stage(next_stage_index):
    """다음 스테이지로 변경하는 함수"""
    global current_stage_index, world, is_stage_cleared

    # 현재 스테이지의 몬스터, 배경 등 제거 (플레이어는 유지)
    player = world.get('player')
    world['entities'] = [player] if player else []
    world['bg'].clear()
    # 다른 레이어도 필요에 따라 초기화
    world['effects_back'].clear()
    world['effects_front'].clear()


    # 다음 스테이지 인덱스로 변경
    current_stage_index = next_stage_index
    if current_stage_index >= len(stages):
        # 모든 스테이지 클리어 시 게임 종료 또는 다른 모드로 전환
        print("All stages cleared!")
        game_framework.quit()
        return

    # 새 스테이지 로드
    stages[current_stage_index].load(world)
    is_stage_cleared = False
    print(f"Changed to Stage {current_stage_index + 1}")


def enter():
    global world, current_stage_index, is_stage_cleared
    # clear existing
    for k in list(world.keys()):
        try:
            if isinstance(world[k], list):
                world[k].clear()
        except Exception:
            pass

    # create player (use fallback if heavy Player init fails)
    try:
        player = Player()
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

    # attach a reference to the current world so player and callbacks can access/modify it
    try:
        player.world = world
    except Exception:
        pass
    world['player'] = player # 플레이어를 world에 명시적으로 저장
    world['entities'].append(player)

    # inventory overlay: pass world reference so InventoryOverlay can spawn WorldItem into this world
    try:
        inv = InventoryOverlay(player, world)
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

    # cursor on top (safe fallback)
    try:
        cursor = Cursor(player)
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

    # 첫 번째 스테이지 로드
    current_stage_index = 0
    is_stage_cleared = False
    stages[current_stage_index].load(world)


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
    global is_stage_cleared
    for layer_name in ['bg', 'effects_back', 'entities', 'effects_front', 'ui', 'cursor']:
        new_list = []
        for o in list(world[layer_name]):
            try:
                if hasattr(o, 'update'):
                    alive = o.update()
                    if alive is False:
                        continue
                new_list.append(o)
            except Exception:
                try:
                    new_list.append(o)
                except Exception:
                    pass
        world[layer_name][:] = new_list

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
    for layer_name in ['bg', 'effects_back', 'entities', 'effects_front', 'ui', 'cursor']:
        for o in world[layer_name]:
            try:
                if hasattr(o, 'draw'):
                    o.draw()
            except Exception:
                pass
    p2.update_canvas()
