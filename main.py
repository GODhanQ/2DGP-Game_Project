import time
from pico2d import *
from game_logic import *
import game_logic.framework as framework

def handle_events():
    global running

    event_list = get_events()
    for event in event_list:
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False
        else:
            player.handle_event(event)

def reset_world():
    global world
    global player, cursor

    world = []

    # grass = Grass()
    # world.append(grass)

    cursor = Cursor()
    world.append(cursor)

    player = Player()
    world.append(player)

def update_world():
    for o in world:
        o.update()
    pass


def render_world():
    clear_canvas()
    for o in world:
        o.draw()
    update_canvas()


running = True
current_time = time.time()

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

    # 프레임 레이트 제한 (약 60 FPS)
    delay(0.01)
# finalization code
close_canvas()