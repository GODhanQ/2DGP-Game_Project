"""
Minimal launcher: open pico2d canvas, run framework with title_mode, close canvas.
"""
from pico2d import open_canvas, close_canvas
import game_framework
import game_logic.title_mode as init_mode

window_scale = 8
window_width, window_height = 160 * window_scale, 90 * window_scale

print(f"[main] Opening canvas {window_width}x{window_height}...")
open_canvas(window_width, window_height)
print("[main] Canvas opened successfully")
try:
    print("[main] Starting game_framework.run()...")
    game_framework.run(init_mode)
    print("[main] game_framework.run() finished")
finally:
    print("[main] Closing canvas...")
    close_canvas()
    print("[main] Done")
