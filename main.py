"""
Minimal launcher: open pico2d canvas, run framework with title_mode, close canvas.
"""
from pico2d import open_canvas, close_canvas
import game_framework
import game_logic.title_mode as init_mode

window_scale = 5
window_width, window_height = 160 * window_scale, 90 * window_scale

print(f"[main.py] Opening canvas {window_width}x{window_height}...")
open_canvas(window_width, window_height)
print("[main.py] Canvas opened successfully")
try:
    print("[main.py] Starting game_framework.run()...")
    game_framework.run(init_mode)
    print("[main.py] game_framework.run() finished")
finally:
    print("[main.py] Closing canvas...")
    close_canvas()
    print("[main.py] Done")
