import ctypes

import pico2d as p2
from sdl2 import SDL_GetMouseState, SDL_QUIT, SDL_KEYDOWN, SDLK_ESCAPE, SDL_MOUSEBUTTONDOWN, SDL_BUTTON_LEFT

import game_framework
from .cursor import TitleCursor
from . import title_mode  # title_mode 모듈 import 추가

# defeat_mode의 world 레이어 구조 (play_mode와 유사)
world = {
    'backgrounds': [],
    'entities': [],  # player 등
    'ui': [],
    'cursor': []
}
world_layers = ['backgrounds', 'entities', 'ui', 'cursor']

# 생존 시간 저장 변수
elapsed_time = 0.0

def enter(player, survival_time=0.0):
    """패배 모드 진입. 기존 player 객체와 생존 시간을 전달받음."""
    print(f"[defeat_mode] enter() - player 객체 및 생존 시간({survival_time:.2f}초) 전달받음")

    # 생존 시간을 전역 변수에 저장
    global elapsed_time
    elapsed_time = survival_time

    # world 레이어 초기화
    world['entities'].clear()
    world['ui'].clear()
    world['backgrounds'].clear()
    world['cursor'].clear()

    # 플레이어 추가
    world['entities'].append(player)
    player.x = p2.get_canvas_width() // 2 + 200
    player.y = p2.get_canvas_height() // 7

    # 배경 이미지 추가
    BG = BGimage('resources/Texture_organize/UI/Stage_Loading/BlackBG.png')
    world['backgrounds'].append(BG)

    # "메인 메뉴로 돌아가기" 버튼 (title_mode 모듈 객체 전달)
    ReturnButton = Button(
        text="메인 메뉴로 돌아가기",
        x=p2.get_canvas_width() // 2 - 200,
        y=p2.get_canvas_height() // 7,
        width=300,
        height=80,
        callback=lambda: game_framework.change_state(title_mode)  # 문자열 -> 모듈 객체로 수정
    )
    world['ui'].append(ReturnButton)

    # "게임 종료" 버튼
    ExitButton = Button(
        text="게임 종료",
        x=p2.get_canvas_width() // 2 + 200,
        y=p2.get_canvas_height() // 7,
        width=300,
        height=80,
        callback=lambda: game_framework.quit()
    )
    world['ui'].append(ExitButton)

    # 커서 생성
    try:
        cursor = TitleCursor()  # 타이틀 전용 커서 (인벤토리 커서 애니메이션 사용)
        world['cursor'].append(cursor)
        print("[defeat_mode] 타이틀 커서 생성 완료")
    except Exception as ex:
        print(f'\033[91m[defeat_mode] 타이틀 커서 생성 실패: {ex}\033[0m')

def exit():
    """defeat_mode 종료 시 world 정리"""
    print("[defeat_mode] exit() - world 정리")
    world['entities'].clear()
    world['ui'].clear()
    world['backgrounds'].clear()
    world['cursor'].clear()

def update():
    """패배 화면 업데이트"""
    # 모든 레이어의 객체 업데이트
    for layer_name in ['backgrounds', 'entities', 'ui', 'cursor']:
        layer = world.get(layer_name, [])
        new_list = []
        for obj in layer:
            try:
                if hasattr(obj, 'update'):
                    keep = obj.update()
                    if keep is None or keep:
                        new_list.append(obj)
            except Exception as ex:
                print(f'\033[91m[title_mode] Update error in {layer_name}: {ex}\033[0m')
                new_list.append(obj)
        world[layer_name] = new_list

def draw():
    try:
        p2.clear_canvas()
        # (원한다면 player 등 그리기)

        for layer in ['backgrounds', 'entities']:
            for o in world[layer]:
                try:
                    if hasattr(o, 'draw'):
                        if hasattr(o, 'x') and hasattr(o, 'y'):
                            draw_x = o.x
                            draw_y = o.y
                            o.draw(draw_x, draw_y)
                        else:
                            o.draw()
                except Exception as e:
                    print(f"\033[91m[defeat_mode] draw error in {layer}: {e}\033[0m")

        for layer in ['ui', 'cursor']:
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
        center_y = canvas_h // 2 - 100

        # 폰트 로드 (한글 지원 폰트 우선)
        try:
            font_large = p2.load_font('resources/Fonts/pixelroborobo.otf', 80)
            font_small = p2.load_font('resources/Fonts/pixelroborobo.otf', 40)
        except Exception:
            print(f'\033[91m[defeat_mode] draw() 폰트 로드 실패: pixelroborobo.otf\033[0m')
            font_large = None
            font_small = None

        # "패배" 메시지
        text = "패배"
        font_size = 80
        approx_width = int(len(text) * font_size * 1.0)

        if font_large:
            font_large.draw(center_x - approx_width // 2, center_y, text, (255, 80, 80))
        else:
            print(f'\033[91m[defeat_mode] draw() 폰트 로드 실패로 "패배" 메시지를 그릴 수 없습니다.\033[0m')

        # 생존 시간 표시 (패배 메시지 아래에)
        if font_small:
            # 시간을 분:초 형식으로 변환
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            time_text = f"생존 시간: {minutes}분 {seconds}초"

            # 텍스트 길이 계산
            time_font_size = 40
            time_text_width = int(len(time_text) * time_font_size * 0.6)

            # 패배 메시지 아래 100px에 표시
            time_y = center_y - 100

            # 그림자 효과
            font_small.draw(center_x - time_text_width // 2 - 2, time_y - 2, time_text, (50, 50, 50))
            # 실제 텍스트
            font_small.draw(center_x - time_text_width // 2, time_y, time_text, (200, 200, 200))

    except Exception as e:
        print(f"\033[91m[defeat_mode] draw() exception: {e}\033[0m")

    p2.update_canvas()

def handle_events():
    """이벤트 처리 (framework가 호출하는 함수)"""
    events = p2.get_events()
    for e in events:
        if e.type == SDL_QUIT:
            game_framework.quit()
        elif e.type == SDL_KEYDOWN:
            if e.key == SDLK_ESCAPE:
                game_framework.quit()
        elif e.type == SDL_MOUSEBUTTONDOWN:
            if e.button == SDL_BUTTON_LEFT:
                # 마우스 클릭 시 버튼 체크 (world['ui']에서 Button 객체만 처리)
                for obj in world.get('ui', []):
                    if isinstance(obj, Button) and obj.hovered:
                        obj.on_click()
                        break

        # 커서에 이벤트 전달 (클릭 애니메이션 처리)
        for cursor in world.get('cursor', []):
            try:
                if hasattr(cursor, 'handle_event'):
                    cursor.handle_event(e)
            except Exception:
                print(f'\033[91m[title_mode] Cursor handle_event error: {e}\033[0m')

def pause():
    game_framework.paused = True

def resume():
    game_framework.paused = False

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

class Button:
    """클릭 가능한 메뉴 버튼 클래스
    1. 버튼 배경 이미지 로드
    2. 텍스트 렌더링
    3. 마우스 오버 및 클릭 처리
    4. 콜백 함수 호출
    5. 한글 지원 폰트 사용
    """
    _font = None  # 클래스 변수로 폰트 공유
    _button_image = None  # 버튼 배경 이미지

    def __init__(self, text, x, y, width, height, callback):
        self.text = text
        self.x = x  # 중심 x 좌표
        self.y = y  # 중심 y 좌표
        self.width = width
        self.height = height
        self.callback = callback
        self.hovered = False
        self.font_size = 20

        # 폰트 로드 (최초 1회만)
        if Button._font is None:
            try:
                from pico2d import load_font
                import os
                # 폰트 경로 후보 (한글 지원 폰트 우선)
                font_candidates = [
                    'resources/Fonts/pixelroborobo.otf',
                ]
                for font_path in font_candidates:
                    try:
                        Button._font = load_font(font_path, self.font_size)  # 버튼용 폰트 크기 40으로 증가
                        print(f"[MenuButton] 폰트 로드 성공: {font_path}")
                        break
                    except Exception as ex:
                        print(f"\033[91m[MenuButton] 폰트 로드 실패: {ex}\033[0m")
            except Exception as ex:
                print(f'\033[91m[MenuButton] 폰트 로드 실패: {ex}\033[0m')

        # 버튼 배경 이미지 로드 (최초 1회만)
        if Button._button_image is None:
            try:
                Button._button_image = p2.load_image('resources/Texture_organize/UI/Button/Button_Brown0.png')
                print("[MenuButton] 버튼 배경 이미지 로드 성공")
            except Exception as ex:
                print(f"\033[91m[MenuButton] 버튼 배경 이미지 로드 실패: {ex}\033[0m")


    def update(self):
        """마우스 위치에 따라 hover 상태 업데이트"""
        # 마우스 위치 가져오기
        mx_ptr = ctypes.c_int(0)
        my_ptr = ctypes.c_int(0)
        SDL_GetMouseState(ctypes.byref(mx_ptr), ctypes.byref(my_ptr))
        mouse_x = mx_ptr.value
        mouse_y = p2.get_canvas_height() - my_ptr.value

        self.hovered = self.contains_point(mouse_x, mouse_y)
        return True

    def draw(self):
        # 버튼 배경 그리기
        if Button._button_image:
            scale_x = self.width / Button._button_image.w
            scale_y = self.height / Button._button_image.h
            Button._button_image.draw(self.x, self.y, Button._button_image.w * scale_x, Button._button_image.h * scale_y)
        else:
            print(f'\033[93m[MenuButton] 버튼 배경 이미지 없음\033[0m')

        # 텍스트 그리기
        if Button._font:
            # 텍스트 길이 및 높이 계산 (대략적 추정)
            text_width = int(len(self.text) * self.font_size * 0.9)
            text_height = self.font_size * 0.1

            # 그림자 효과 (가독성 향상)
            shadow_color = (100, 100, 100)
            Button._font.draw(self.x - text_width // 2 - 2, self.y - text_height // 2 - 2, self.text, shadow_color)
            Button._font.draw(self.x - text_width // 2 - 1, self.y - text_height // 2 - 1, self.text, shadow_color)

            # 실제 텍스트 (중앙 정렬)
            if self.hovered:
                Button._font.draw(self.x - text_width // 2, self.y - text_height // 2, self.text, (255, 255, 200))
            else:
                Button._font.draw(self.x - text_width // 2, self.y - text_height // 2, self.text, (255, 255, 255))
        else:
            print(f'\033[91m[MenuButton] 폰트가 로드되지 않아 텍스트를 그릴 수 없습니다.\033[0m')

    def contains_point(self, px, py):
        """점이 버튼 내부에 있는지 확인"""
        left = self.x - self.width // 2
        right = self.x + self.width // 2
        bottom = self.y - self.height // 2
        top = self.y + self.height // 2
        return left <= px <= right and bottom <= py <= top

    def on_click(self):
        """버튼 클릭 시 콜백 실행"""
        if self.callback:
            self.callback()
