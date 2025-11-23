import pico2d as p2
from pico2d import draw_rectangle

import game_framework

# defeat_mode의 world 레이어 구조 (play_mode와 유사)
world = {
    'backgrounds': [],
    'entities': [],  # player 등
    'ui': [],
}

def enter(player):
    """패배 모드 진입. 기존 player 객체를 그대로 world에 보관."""
    print("[defeat_mode] enter() - player 객체 전달받음")
    world['entities'].clear()
    world['ui'].clear()
    world['entities'].append(player)
    player.x = p2.get_canvas_width() // 2
    player.y = p2.get_canvas_height() // 2
    BG = BGimage('resources/Texture_organize/UI/Stage_Loading/BlackBG.png')
    world['backgrounds'].append(BG)



def exit():
    world['entities'].clear()
    world['ui'].clear()

def update():
    # 필요시 player 등 업데이트
    for layer in ['backgrounds', 'entities', 'ui']:
        for o in world[layer]:
            if hasattr(o, 'update'):
                o.update()

def draw():
    try:
        p2.clear_canvas()
        # (원한다면 player 등 그리기)
        for layer in ['backgrounds', 'entities', 'ui']:
            for o in world[layer]:
                try:
                    if hasattr(o, 'draw'):
                        o.draw()
                except Exception as e:
                    print(f"\033[91m[defeat_mode] draw error in {layer}: {e}\033[0m")

        # 화면 중앙에 "패배" 메시지 출력
        canvas_w = p2.get_canvas_width()
        canvas_h = p2.get_canvas_height()
        center_x = canvas_w // 2
        center_y = canvas_h // 1.25
        # 폰트 로드 (한글 지원 폰트 우선)
        try:
            font = p2.load_font('resources/Fonts/pixelroborobo.otf', 80)
        except Exception:
            font = None
        text = "패배"
        font_size = 80
        approx_width = int(len(text) * font_size * 1.0)

        if font:
            font.draw(center_x - approx_width // 2, center_y, text, (255, 80, 80))
        else:
            p2.draw_text(text, center_x - 40, center_y, (255, 80, 80))
    except Exception as e:
        print(f"\033[91m[defeat_mode] draw() exception: {e}\033[0m")
    p2.update_canvas()

def handle_events():
    events = p2.get_events()
    for e in events:
        if e.type == p2.SDL_QUIT:
            game_framework.quit()
        elif e.type == p2.SDL_KEYDOWN:
            if e.key == p2.SDLK_ESCAPE:
                game_framework.quit()
            # 필요시 엔터 등으로 타이틀로 복귀 등 추가 가능

def pause():
    pass

def resume():
    pass

class BGimage:
    """패배 모드용 배경 이미지 클래스"""
    def __init__(self, image_path):
        try:
            self.image = p2.load_image(image_path)
        except Exception:
            self.image = None

    def update(self):
        pass

    def do(self):
        pass

    def draw(self):
        if self.image:
            canvas_w = p2.get_canvas_width()
            canvas_h = p2.get_canvas_height()
            self.image.draw(canvas_w // 2, canvas_h // 2, canvas_w, canvas_h)