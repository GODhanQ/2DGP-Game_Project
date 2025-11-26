# game_logic/title_mode.py
"""타이틀 화면 모듈"""

import pico2d as p2
import ctypes
from sdl2 import SDL_QUIT, SDL_KEYDOWN, SDLK_ESCAPE, SDLK_RETURN, SDLK_SPACE, SDL_MOUSEBUTTONDOWN, SDL_MOUSEBUTTONUP, SDL_BUTTON_LEFT, SDL_GetMouseState, SDL_MOUSEMOTION

import game_framework as framework
from . import lobby_mode
from .cursor import TitleCursor

# 타이틀 화면 이미지
title_image = None
title_back_image = None

# Tree 애니메이션
tree_begin_images = []  # TreeBegin 애니메이션 (00~29)
tree_loop_images = []   # Tree 루프 애니메이션 (00~15)
animation_frame = 0
animation_time = 0.0
animation_fps = 12  # 초당 프레임 수
is_begin_phase = True  # True: TreeBegin 재생 중, False: Tree 루프 재생 중

# 스케일 팩터
tree_scale = 3.0  # Tree 애니메이션 스케일
title_scale = 3.0  # 타이틀 로고 스케일

# 월드 레이어 (play_mode와 유사한 구조)
world = {
    'background': [],  # 배경 이미지
    'tree_animation': [],  # Tree 애니메이션
    'title': [],  # 타이틀 로고
    'buttons': [],  # 메뉴 버튼들
    'cursor': []  # 커서
}

# 배경 렌더러
class BackgroundRenderer:
    """배경 이미지를 렌더링하는 클래스"""
    def __init__(self, image):
        self.image = image

    def update(self):
        return True

    def draw(self):
        if self.image:
            canvas_width = p2.get_canvas_width()
            canvas_height = p2.get_canvas_height()
            center_x = canvas_width // 2
            center_y = canvas_height // 2
            self.image.draw(center_x, center_y, canvas_width, canvas_height)

# Tree 애니메이션 렌더러
class TreeAnimationRenderer:
    """Tree 애니메이션을 렌더링하는 클래스"""
    def __init__(self, begin_images, loop_images, scale):
        self.begin_images = begin_images
        self.loop_images = loop_images
        self.scale = scale
        self.current_frame = 0
        self.animation_time = 0.0
        self.animation_fps = 12
        self.is_begin_phase = True

    def update(self):
        dt = framework.delta_time if hasattr(framework, 'delta_time') else 0.016
        self.animation_time += dt

        frame_time = 1.0 / self.animation_fps

        if self.animation_time >= frame_time:
            self.animation_time -= frame_time

            if self.is_begin_phase:
                self.current_frame += 1
                if self.current_frame >= len(self.begin_images):
                    self.is_begin_phase = False
                    self.current_frame = 0
                    print("[title_mode] TreeBegin 완료, Tree 루프 시작")
            else:
                self.current_frame += 1
                if self.current_frame >= len(self.loop_images):
                    self.current_frame = 0

        return True

    def draw(self):
        canvas_width = p2.get_canvas_width()
        canvas_height = p2.get_canvas_height()
        center_x = canvas_width // 2
        center_y = canvas_height // 2

        if self.is_begin_phase and self.begin_images:
            if 0 <= self.current_frame < len(self.begin_images):
                tree_img = self.begin_images[self.current_frame]
                tree_width = int(tree_img.w * self.scale)
                tree_height = int(tree_img.h * self.scale)
                tree_img.draw(center_x, int(center_y * 1.3), tree_width, tree_height)
        elif not self.is_begin_phase and self.loop_images:
            if 0 <= self.current_frame < len(self.loop_images):
                tree_img = self.loop_images[self.current_frame]
                tree_width = int(tree_img.w * self.scale)
                tree_height = int(tree_img.h * self.scale)
                tree_img.draw(center_x, int(center_y * 1.3), tree_width, tree_height)

# 타이틀 로고 렌더러
class TitleRenderer:
    """타이틀 로고를 렌더링하는 클래스"""
    def __init__(self, image, scale):
        self.image = image
        self.scale = scale

    def update(self):
        return True

    def draw(self):
        if self.image:
            canvas_width = p2.get_canvas_width()
            canvas_height = p2.get_canvas_height()
            center_x = canvas_width // 2
            center_y = canvas_height // 2

            title_width = int(self.image.w * self.scale)
            title_height = int(self.image.h * self.scale)
            self.image.draw(center_x, int(center_y * 0.7), title_width, title_height)

# 메뉴 버튼
class MenuButton:
    """클릭 가능한 메뉴 버튼 클래스"""
    _font = None  # 클래스 변수로 폰트 공유

    def __init__(self, text, x, y, width, height, callback):
        self.text = text
        self.x = x  # 중심 x 좌표
        self.y = y  # 중심 y 좌표
        self.width = width
        self.height = height
        self.callback = callback
        self.hovered = False

        # 폰트 로드 (최초 1회만)
        if MenuButton._font is None:
            try:
                from pico2d import load_font
                import os
                # 폰트 경로 후보 (한글 지원 폰트 우선)
                font_candidates = [
                    'resources/Fonts/pixelroborobo.otf',
                ]
                for font_path in font_candidates:
                    try:
                        MenuButton._font = load_font(font_path, 40)  # 버튼용 폰트 크기 40으로 증가
                        print(f"[MenuButton] 폰트 로드 성공: {font_path}")
                        break
                    except Exception:
                        continue
            except Exception as ex:
                print(f'\033[91m[MenuButton] 폰트 로드 실패: {ex}\033[0m')

    def contains_point(self, px, py):
        """점이 버튼 내부에 있는지 확인"""
        left = self.x - self.width // 2
        right = self.x + self.width // 2
        bottom = self.y - self.height // 2
        top = self.y + self.height // 2
        return left <= px <= right and bottom <= py <= top

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
        """버튼 그리기"""
        # 버튼 배경 박스
        if self.hovered:
            # hover 상태: 밝은 테두리
            # p2.draw_rectangle(
            #     self.x - self.width // 2,
            #     self.y - self.height // 2,
            #     self.x + self.width // 2,
            #     self.y + self.height // 2
            # )
            pass
        else:
            # 일반 상태: 어두운 테두리
            # p2.draw_rectangle(
            #     self.x - self.width // 2,
            #     self.y - self.height // 2,
            #     self.x + self.width // 2,
            #     self.y + self.height // 2
            # )
            pass

        # 텍스트 표시
        if MenuButton._font:
            # 텍스트 색상 (hover 상태에 따라 변경)
            if self.hovered:
                # hover 상태: 밝은 흰색
                text_color = (255, 255, 150)
                shadow_color = (0, 0, 0)
            else:
                # 일반 상태: 회색
                text_color = (200, 200, 200)
                shadow_color = (50, 50, 50)

            # 그림자 효과 (가독성 향상)
            MenuButton._font.draw(self.x - 2, self.y - 2, self.text, shadow_color)
            MenuButton._font.draw(self.x - 1, self.y - 1, self.text, shadow_color)
            # 실제 텍스트
            MenuButton._font.draw(self.x, self.y, self.text, text_color)

    def on_click(self):
        """버튼 클릭 시 콜백 실행"""
        if self.callback:
            self.callback()

# 메뉴 버튼 리스트
mouse_x, mouse_y = 0, 0

def start_game():
    """게임 시작 버튼 콜백"""
    print("[title_mode] 게임 시작")
    import game_logic.play_mode as play_mode
    import game_logic.lobby_mode as lobby_mode
    framework.change_state(lobby_mode)

def quit_game():
    """게임 종료 버튼 콜백"""
    print("[title_mode] 게임 종료")
    framework.quit()

def enter():
    """타이틀 모드 진입"""
    global title_image, title_back_image, tree_begin_images, tree_loop_images
    global animation_frame, animation_time, is_begin_phase, world

    print("[title_mode] 타이틀 화면 진입")

    # 월드 레이어 초기화
    for layer in world.values():
        if isinstance(layer, list):
            layer.clear()

    # 이미지 로드 (예외 방지)
    try:
        title_back_image = p2.load_image('resources/Texture_organize/IDK_2/Title/N_Title_Back.png')
    except Exception as ex:
        print(f'\033[91m[title_mode] 타이틀 배경 이미지 로드 실패: {ex}\033[0m')
        title_back_image = None
    try:
        title_image = p2.load_image('resources/Texture_organize/IDK_2/Title/N_Title.png')
    except Exception as ex:
        print(f'\033[91m[title_mode] 타이틀 로고 이미지 로드 실패: {ex}\033[0m')
        title_image = None

    # Tree Begin 애니메이션 로드 (00~29)
    tree_begin_images = []
    for i in range(30):
        path = f'resources/Texture_organize/IDK_2/Title/N_Title_TreeBegin{i:02d}.png'
        try:
            tree_begin_images.append(p2.load_image(path))
        except Exception as ex:
            print(f'\033[91m[title_mode] TreeBegin 이미지 로드 실패: {path}, {ex}\033[0m')

    # Tree 루프 애니메이션 로드 (00~15)
    tree_loop_images = []
    for i in range(16):
        path = f'resources/Texture_organize/IDK_2/Title/N_Title_Tree{i:02d}.png'
        try:
            tree_loop_images.append(p2.load_image(path))
        except Exception as ex:
            print(f'\033[91m[title_mode] TreeLoop 이미지 로드 실패: {path}, {ex}\033[0m')

    # world에 렌더러 추가
    if title_back_image:
        world['background'].append(BackgroundRenderer(title_back_image))
    if tree_begin_images or tree_loop_images:
        world['tree_animation'].append(TreeAnimationRenderer(tree_begin_images, tree_loop_images, tree_scale))
    if title_image:
        world['title'].append(TitleRenderer(title_image, title_scale))

    # 버튼 추가
    start_btn = MenuButton(
        text="게임 시작",
        x=p2.get_canvas_width() // 2 - 300,
        y=p2.get_canvas_height() // 7,
        width=300,
        height=80,
        callback=start_game
    )
    quit_btn = MenuButton(
        text="게임 종료",
        x=p2.get_canvas_width() // 2 + 100,
        y=p2.get_canvas_height() // 7,
        width=300,
        height=80,
        callback=quit_game
    )
    world['buttons'].append(start_btn)
    world['buttons'].append(quit_btn)

    # 커서
    try:
        cursor = TitleCursor()
        world['cursor'].append(cursor)
    except Exception as ex:
        print(f'\033[91m[title_mode] 커서 생성 실패: {ex}\033[0m')

    print("[title_mode] 타이틀 이미지 로드 완료")

def exit():
    """타이틀 모드 종료"""
    global title_image, title_back_image, tree_begin_images, tree_loop_images, world

    title_image = None
    title_back_image = None
    tree_begin_images = []
    tree_loop_images = []

    # 월드 레이어 정리
    for layer in world.values():
        if isinstance(layer, list):
            layer.clear()

    print("[title_mode] 타이틀 화면 종료")

def update():
    """타이틀 화면 업데이트"""
    # 모든 레이어의 객체 업데이트
    for layer_name in ['background', 'tree_animation', 'title', 'buttons', 'cursor']:
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
    """타이틀 화면 그리기"""
    p2.clear_canvas()

    # 레이어 순서대로 그리기
    render_order = ['background', 'tree_animation', 'title', 'buttons', 'cursor']

    for layer_name in render_order:
        layer = world.get(layer_name, [])
        for obj in layer:
            try:
                if hasattr(obj, 'draw'):
                    obj.draw()
            except Exception as ex:
                print(f'\033[91m[title_mode] Draw error in {layer_name}: {ex}\033[0m')

    p2.update_canvas()

def handle_events():
    """이벤트 처리 (framework가 호출하는 함수)"""
    events = p2.get_events()
    for e in events:
        if e.type == SDL_QUIT:
            framework.quit()
        elif e.type == SDL_KEYDOWN:
            if e.key == SDLK_ESCAPE:
                framework.quit()
            elif e.key == SDLK_RETURN or e.key == SDLK_SPACE:
                # Enter 또는 Space 키를 누르면 게임 시작 (기존 동작 유지)
                print("[title_mode] 게임 시작")
                import game_logic.play_mode as play_mode
                framework.change_state(play_mode)
        elif e.type == SDL_MOUSEBUTTONDOWN:
            if e.button == SDL_BUTTON_LEFT:
                # 마우스 클릭 시 버튼 체크
                for button in world.get('buttons', []):
                    if button.hovered:
                        button.on_click()
                        break

        # 커서에 이벤트 전달 (클릭 애니메이션 처리)
        for cursor in world.get('cursor', []):
            try:
                if hasattr(cursor, 'handle_event'):
                    cursor.handle_event(e)
            except Exception:
                print(f'\033[91m[title_mode] Cursor handle_event error: {e}\033[0m')

def pause():
    """타이틀 모드 일시 정지"""
    pass

def resume():
    """타이틀 모드 재개"""
    pass
