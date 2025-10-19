import ctypes
from pico2d import load_image, get_canvas_height
from sdl2 import SDL_GetMouseState, SDL_ShowCursor, SDL_DISABLE
from . import framework

class Cursor:
    def __init__(self):
        # 'resources/Texture_organize/UI/Cursor_Combat0.png' 경로에 커서 이미지가 있다고 가정합니다.
        self.image = load_image('resources/Texture_organize/UI/Cursor_Combat0.png')
        self.x, self.y = 0, 0
        self.scale_factor = 2.0 # 커서 크기 배율
        SDL_ShowCursor(SDL_DISABLE) # 기본 시스템 커서 숨기기

    def update(self):
        mx = ctypes.c_int(0)
        my = ctypes.c_int(0)
        SDL_GetMouseState(ctypes.byref(mx), ctypes.byref(my))
        canvas_h = get_canvas_height()
        self.x = mx.value
        self.y = canvas_h - 1 - my.value # pico2d 좌표계로 변환

    def draw(self):
        self.image.draw(self.x, self.y, self.image.w * self.scale_factor, self.image.h * self.scale_factor)

    def handle_event(self, event):
        # 커서는 이벤트를 직접 처리할 필요가 없을 수 있지만, 일관성을 위해 메서드를 유지합니다.
        pass
