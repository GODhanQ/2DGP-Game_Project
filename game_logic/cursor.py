import ctypes
import os
import math
from pico2d import load_image, get_canvas_height, get_canvas_width
from sdl2 import SDL_GetMouseState, SDL_ShowCursor, SDL_DISABLE, SDL_MOUSEBUTTONDOWN, SDL_MOUSEBUTTONUP, SDL_BUTTON_LEFT, SDL_BUTTON_RIGHT
from . import framework

class Cursor:
    def __init__(self, player=None):
        # 기본 커서(인벤토리 닫힘 상태에서 사용)
        self.image = load_image('resources/Texture_organize/UI/Cursor_Combat0.png')
        self.x, self.y = 0, 0
        self.scale_factor = 2.0 # 커서 크기 배율
        SDL_ShowCursor(SDL_DISABLE) # 기본 시스템 커서 숨기기

        # 플레이어 참조(인벤토리 열림 여부 확인용)
        self.player = player
        self.last_inventory_open = False

        # 인벤토리 전용 커서 애니메이션 프레임 로드
        mouse_folder = os.path.join('resources', 'Texture_organize', 'UI', 'Mouse_Arrow')
        self.inv_frames = []
        for i in range(0, 7):
            path = os.path.join(mouse_folder, f'Multi_Arrow_UI_14_Mouse_{i}.png')
            try:
                self.inv_frames.append(load_image(path))
            except Exception as ex:
                print('Failed to load cursor frame:', path, ex)
                self.inv_frames = []
                break

        # 인벤토리 커서 핫스팟(앵커) 비율: (ax, ay) in [0,1]
        # - ax=0은 이미지의 가장 왼쪽, ax=1은 가장 오른쪽
        # - ay=0은 이미지의 가장 아래, ay=1은 가장 위쪽
        # 팁이 좌측 상단 쪽에 있을 것으로 가정하여 기본 (0.10, 0.90)으로 설정
        self.inv_anchor = (0.10, 0.90)

        # 방패 범위 이미지 (최상단 오버레이로 그리기)
        try:
            self.shield_range_image = load_image('resources/Texture_organize/Weapon/shieldRange.png')
        except Exception as ex:
            print('Failed to load shield range image in cursor:', ex)
            self.shield_range_image = None
        self.shield_range_scale = 4.0

        # 애니메이션 상태
        self.anim_state = 'idle_up'  # 'down', 'up', 'idle_up'
        self.frame_idx = 6            # idle은 마지막 프레임(6) 유지
        self.frame_timer = 0.0
        self.frame_duration = 0.06    # 프레임당 시간
        self.mouse_down = False

    def update(self):
        # 마우스 위치 갱신
        mx = ctypes.c_int(0)
        my = ctypes.c_int(0)
        SDL_GetMouseState(ctypes.byref(mx), ctypes.byref(my))
        canvas_h = get_canvas_height()
        self.x = mx.value
        self.y = canvas_h - 1 - my.value # pico2d 좌표계로 변환

        inv_open = bool(getattr(self.player, 'inventory_open', False)) if self.player else False

        # 인벤토리 토글 시 애니메이션 상태 초기화
        if inv_open != self.last_inventory_open:
            self.anim_state = 'idle_up'
            self.frame_idx = 6
            self.frame_timer = 0.0
            self.mouse_down = False
            self.last_inventory_open = inv_open

        # 인벤토리 열렸을 때만 애니메이션 적용
        if inv_open and self.inv_frames:
            dt = framework.get_delta_time()
            self.frame_timer += dt
            if self.anim_state == 'down':
                # 0 -> 1 재생 후, 눌려있는 동안 1 유지
                if self.frame_timer >= self.frame_duration:
                    self.frame_timer -= self.frame_duration
                    if self.frame_idx < 1:
                        self.frame_idx += 1
                # 눌린 상태 유지 시 frame 1 고정
                if self.mouse_down:
                    self.frame_idx = max(self.frame_idx, 1)
                else:
                    # 버튼 해제되었다면 업 애니메이션으로 전환
                    self.anim_state = 'up'
                    self.frame_idx = 2
                    self.frame_timer = 0.0
            elif self.anim_state == 'up':
                # 2 -> 6까지 재생 후 idle_up로 전환
                if self.frame_timer >= self.frame_duration:
                    self.frame_timer -= self.frame_duration
                    if self.frame_idx < 6:
                        self.frame_idx += 1
                    if self.frame_idx >= 6:
                        self.anim_state = 'idle_up'
                        self.frame_idx = 6
            else:
                # idle_up: 프레임 6 유지
                self.frame_idx = 6

    def draw(self, draw_x=None, draw_y=None):
        if draw_x is None:
            draw_x = self.x
        if draw_y is None:
            draw_y = self.y
        # 방패 전개 범위 오버레이(항상 최상단). 단, 엔티티 레이어에서 그릴 경우 여기서는 생략
        right_held = False
        try:
            mx = ctypes.c_int(0)
            my = ctypes.c_int(0)
            state = SDL_GetMouseState(ctypes.byref(mx), ctypes.byref(my))
            right_mask = 1 << (SDL_BUTTON_RIGHT - 1)
            right_held = bool(state & right_mask)
        except Exception:
            right_held = False

        shield_block = False
        draw_in_entity = False
        if self.player and hasattr(self.player, 'shield') and self.player.shield:
            shield_block = getattr(self.player.shield, 'blocking', False)
            draw_in_entity = getattr(self.player.shield, 'draw_range_in_entity', False)

        # 우클릭을 홀드할 때만 방패 범위 이미지를 플레이어 주변에 생성 (카메라 적용)
        if right_held and self.shield_range_image is not None and not draw_in_entity:
            # 카메라 가져오기 - play_mode와 lobby_mode 모두 지원
            camera = None
            try:
                # 먼저 play_mode에서 카메라 가져오기 시도
                import game_logic.play_mode as play
                camera = getattr(play, 'camera', None)

                # play_mode 카메라가 없으면 lobby_mode에서 시도
                if camera is None:
                    import game_logic.lobby_mode as lobby
                    camera = getattr(lobby, 'camera', None)
            except Exception as ex:
                print(f'[Cursor] 카메라 가져오기 실패: {ex}')
                camera = None

            # 마우스 화면 좌표 가져오기
            mx2 = ctypes.c_int(0)
            my2 = ctypes.c_int(0)
            SDL_GetMouseState(ctypes.byref(mx2), ctypes.byref(my2))

            canvas_h = get_canvas_height()
            canvas_w = get_canvas_width()
            mouse_screen_x = mx2.value
            mouse_screen_y = canvas_h - my2.value

            # 마우스 화면 좌표를 월드 좌표로 변환
            if camera is not None:
                half_w = canvas_w // 2
                half_h = canvas_h // 2
                mouse_world_x = mouse_screen_x - half_w + camera.x
                mouse_world_y = mouse_screen_y - half_h + camera.y
            else:
                mouse_world_x = mouse_screen_x
                mouse_world_y = mouse_screen_y

            # 플레이어(월드 좌표)에서 마우스(월드 좌표)로 향하는 벡터 계산
            dx = mouse_world_x - self.player.x
            dy = mouse_world_y - self.player.y

            # 각도 계산
            angle = math.atan2(dy, dx)
            base_offset = -math.pi / 2
            theta = angle + base_offset

            # 플레이어의 월드 좌표를 화면 좌표로 변환
            if camera is not None:
                half_w = canvas_w // 2
                half_h = canvas_h // 2
                player_screen_x = self.player.x - camera.x + half_w
                player_screen_y = self.player.y - camera.y + half_h
            else:
                player_screen_x = self.player.x
                player_screen_y = self.player.y

            # 방패 이펙트를 플레이어의 화면 좌표 기준으로 그리기
            half_h_scaled = (self.shield_range_image.h * self.shield_range_scale) * 0.5
            draw_x_shield = player_screen_x - half_h_scaled * math.sin(theta)
            draw_y_shield = player_screen_y + half_h_scaled * math.cos(theta)

            self.shield_range_image.clip_composite_draw(
                0, 0, self.shield_range_image.w, self.shield_range_image.h,
                theta, '',
                draw_x_shield, draw_y_shield,
                self.shield_range_image.w * self.shield_range_scale,
                self.shield_range_image.h * self.shield_range_scale
            )
            # 디버그 로그 - 카메라 정보 추가
            # if camera is not None:
            #     print(f'[Cursor] Drew shield range at screen ({draw_x_shield:.1f}, {draw_y_shield:.1f}), '
            #           f'player world ({self.player.x:.1f}, {self.player.y:.1f}), '
            #           f'player screen ({player_screen_x:.1f}, {player_screen_y:.1f}), '
            #           f'camera ({camera.x:.1f}, {camera.y:.1f}), angle {theta:.2f}')
            # else:
            #     print(f'[Cursor] Drew shield range at ({draw_x_shield:.1f}, {draw_y_shield:.1f}) with angle {theta:.2f} (NO CAMERA)')

        # 인벤토리 열림 + 프레임 로드 성공 시 전용 커서 사용 (팁 위치를 마우스 좌표에 정렬)
        if self.player and getattr(self.player, 'inventory_open', False) and self.inv_frames:
            img = self.inv_frames[self.frame_idx]
            w = img.w * self.scale_factor
            h = img.h * self.scale_factor
            ax, ay = self.inv_anchor
            cx = self.x + (0.5 - ax) * w
            cy = self.y + (0.5 - ay) * h
            img.draw(cx, cy, w, h)
        else:
            self.image.draw(draw_x, draw_y, self.image.w * self.scale_factor, self.image.h * self.scale_factor)

    def handle_event(self, event):
        # 인벤토리 열렸을 때만 클릭 애니메이션 처리
        inv_open = bool(getattr(self.player, 'inventory_open', False)) if self.player else False
        if not inv_open:
            return
        if not self.inv_frames:
            return
        # 마우스 좌클릭 이벤트 처리
        if event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            self.mouse_down = True
            self.anim_state = 'down'
            self.frame_idx = 0
            self.frame_timer = 0.0
        elif event.type == SDL_MOUSEBUTTONUP and event.button == SDL_BUTTON_LEFT:
            self.mouse_down = False
            # 업 애니메이션 시작 (2부터)
            self.anim_state = 'up'
            self.frame_idx = 2
            self.frame_timer = 0.0
