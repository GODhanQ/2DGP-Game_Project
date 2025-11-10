"""
Minimal launcher: open pico2d canvas, run framework with play_mode, close canvas.
"""
from pico2d import open_canvas, close_canvas
import game_framework
import game_logic.play_mode as play_mode

open_canvas()
try:
    game_framework.run(play_mode)
finally:
    close_canvas()
