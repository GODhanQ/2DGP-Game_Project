import time
from pico2d import *
from game_logic import *
import game_logic.framework as framework

# 레이어 기반 월드: 배경, 엔티티, UI, 커서(최상단)
world = {
    'bg': [],        # 배경 레이어
    'entities': [],  # 플레이어/몬스터 등 엔티티 레이어
    'ui': [],        # 인벤토리 등 UI 레이어
    'cursor': []     # 커서 레이어 (항상 최상단)
}

running = True
current_time = time.time()


def handle_events():
    global running

    event_list = get_events()
    for event in event_list:
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False
        else:
            # 엔티티, UI, 커서 순으로 이벤트 브로드캐스트
            for o in world['entities']:
                if hasattr(o, 'handle_event'):
                    o.handle_event(event)
            for o in world['ui']:
                if hasattr(o, 'handle_event'):
                    o.handle_event(event)
            for o in world['cursor']:
                if hasattr(o, 'handle_event'):
                    o.handle_event(event)


def reset_world():
    # 레이어 초기화
    world['bg'].clear()
    world['entities'].clear()
    world['ui'].clear()
    world['cursor'].clear()

    # 배경 오브젝트가 있다면 world['bg'].append(Background()) 형태로 추가

    # 엔티티: 플레이어
    player = Player()
    world['entities'].append(player)

    # UI: 인벤토리 오버레이(플레이어 상태 기반)
    inv_overlay = InventoryOverlay(player)
    world['ui'].append(inv_overlay)

    # 커서: 최상단 레이어에 추가 (player 참조 전달)
    cursor = Cursor(player)
    world['cursor'].append(cursor)


def update_world():
    # 배경 → 엔티티 → UI → 커서 순으로 업데이트
    for layer_name in ['bg', 'entities', 'ui', 'cursor']:
        for o in world[layer_name]:
            if hasattr(o, 'update'):
                o.update()


def render_world():
    clear_canvas()
    # 배경 → 엔티티 → UI → 커서 순으로 그리기 (커서가 최상단)
    for layer_name in ['bg', 'entities', 'ui', 'cursor']:
        for o in world[layer_name]:
            if hasattr(o, 'draw'):
                o.draw()
    update_canvas()


open_canvas()
reset_world()

# game loop
while running:
    last_time = current_time
    current_time = time.time()
    delta_time = current_time - last_time

    # 전역 delta_time 업데이트
    framework.set_delta_time(delta_time)

    handle_events()
    update_world()
    render_world()

# finalization code
close_canvas()