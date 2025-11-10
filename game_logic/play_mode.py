# game_logic.play_mode: play mode state that creates Player, InventoryOverlay, Cursor
# minimal, compatible with existing game_logic modules
import pico2d as p2
from sdl2 import SDL_QUIT, SDL_KEYDOWN, SDLK_ESCAPE

from .player import Player
from .ui_overlay import InventoryOverlay
from .cursor import Cursor

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


def enter():
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
