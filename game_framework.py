import time
import game_logic.framework as gl_framework

current_state = None
_running = False


def change_state(new_state, *args, **kwargs):
    global current_state
    # exit old state
    try:
        if current_state and hasattr(current_state, 'exit'):
            current_state.exit()
    except Exception:
        print(f'\033[91m[game_framework] Exception during exit of state {current_state}\033[0m')

    # change state
    current_state = new_state
    # enter new state (with args if provided)
    run(current_state, *args, **kwargs)


def run(start_state, *args, **kwargs):
    """Start the main loop with start_state (module-like object that exposes
    enter/exit/handle_events/update/draw)."""
    global current_state, _running
    current_state = start_state
    try:
        if current_state and hasattr(current_state, 'enter'):
            if args or kwargs:
                current_state.enter(*args, **kwargs)
            else:
                current_state.enter()
    except Exception as ex:
        print(f'\033[91m[game_framework] Exception {ex} during enter of state {current_state}\033[0m')

    _running = True
    last_time = time.time()
    try:
        while _running:
            now = time.time()
            dt = now - last_time
            last_time = now
            # update global delta_time used by game_logic modules
            try:
                gl_framework.set_delta_time(dt)
            except Exception as ex:
                print(f'\033[91m[game_framework] Exception {ex} during set_delta_time() with dt={dt}\033[0m')

            if current_state is None:
                break

            # event handling
            try:
                if hasattr(current_state, 'handle_events'):
                    current_state.handle_events()
            except Exception as ex:
                print(f'\033[91m[game_framework] Exception {ex} during handle_events() of state {current_state}\033[0m')
                print(f'\033[91m[game_framework] Or Entering Next State with {current_state} handle_events()\033[0m')
                print('\033[91m[game_framework]Continuing main loop...\033[0m')

            # update
            try:
                if hasattr(current_state, 'update'):
                    current_state.update()
            except Exception as ex:
                print(f'\033[91m[game_framework] Exception {ex} during update() of state {current_state}\033[0m')

            # draw
            try:
                if hasattr(current_state, 'draw'):
                    current_state.draw()
            except Exception as ex:
                print(f'\033[91m[game_framework] Exception {ex} during draw() of state {current_state}\033[0m')

            # small sleep to avoid 100% CPU (frame limiter is handled by resource loads)
            time.sleep(gl_framework.frame_time if hasattr(gl_framework, 'frame_time') else 0.01)
    finally:
        try:
            if current_state and hasattr(current_state, 'exit'):
                current_state.exit()
        except Exception as ex:
            print(f'\033[91m[game_framework] Exception {ex} during exit() of state {current_state}\033[0m')


def quit():
    global _running
    _running = False
