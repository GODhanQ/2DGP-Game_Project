# game_logic/loading_screen.py
"""스테이지 로딩 화면 모듈"""

import pico2d as p2
from . import framework

class LoadingScreen:
    """스테이지 로딩 화면 클래스"""

    def __init__(self, loading_info):
        """
        Args:
            loading_info: 스테이지 모듈의 LOADING_SCREEN_INFO 딕셔너리
                - stage_number: 스테이지 번호
                - bg_image: 배경 이미지 경로
                - animation_prefix: 애니메이션 이미지 경로 접두사
                - animation_count: 애니메이션 프레임 수
                - extra_animation (optional): 추가 애니메이션 정보
        """
        self.loading_info = loading_info
        self.stage_number = loading_info['stage_number']
        self.bg_image = None
        self.black_bg = None  # 검정 배경 이미지
        self.loading_images = []
        self.extra_images = []  # 추가 애니메이션 이미지
        self.current_frame = 0
        self.animation_time = 0.0
        self.animation_speed = 10  # fps
        self.is_complete = False
        self.loading_duration = 0.0  # 로딩 경과 시간
        self.min_loading_time = 3.0  # 최소 로딩 시간 (초)

        # 이미지 로드
        self._load_images()

        print(f"[LoadingScreen] Stage {self.stage_number} 로딩 화면 초기화 완료")

    def _load_images(self):
        """로딩 화면 이미지들을 로드"""
        try:
            # 검정 배경 이미지 로드
            black_bg_path = 'resources/Texture_organize/UI/Stage_Loading/BlackBG.png'
            self.black_bg = p2.load_image(black_bg_path)
            print(f"[LoadingScreen] 검정 배경 이미지 로드 완료: {black_bg_path}")

            # 배경 이미지 로드
            bg_path = self.loading_info['bg_image']
            self.bg_image = p2.load_image(bg_path)
            print(f"[LoadingScreen] 배경 이미지 로드 완료: {bg_path}")

            # 로딩 애니메이션 이미지 로드
            animation_prefix = self.loading_info['animation_prefix']
            animation_count = self.loading_info['animation_count']

            for i in range(animation_count):
                img_path = f'{animation_prefix}{i:02d}.png'
                img = p2.load_image(img_path)
                self.loading_images.append(img)
            print(f"[LoadingScreen] 로딩 애니메이션 {len(self.loading_images)}개 이미지 로드 완료")

            # 추가 애니메이션 로드 (있는 경우)
            extra_anim = self.loading_info.get('extra_animation')
            if extra_anim:
                extra_prefix = extra_anim['prefix']
                extra_count = extra_anim['count']

                for i in range(extra_count):
                    img_path = f'{extra_prefix}{i:02d}.png'
                    img = p2.load_image(img_path)
                    self.extra_images.append(img)
                print(f"[LoadingScreen] 추가 애니메이션 {len(self.extra_images)}개 이미지 로드 완료")

        except Exception as e:
            print(f"\033[91m[LoadingScreen] 이미지 로드 실패: {e}\033[0m")
            # 로드 실패 시 빈 이미지 리스트로 계속 진행
            self.loading_images = []

    def update(self):
        """로딩 화면 업데이트"""
        dt = framework.get_delta_time()
        self.loading_duration += dt

        # 애니메이션 업데이트
        if len(self.loading_images) > 0:
            self.animation_time += dt
            if self.animation_time >= 1.0 / self.animation_speed:
                self.current_frame = (self.current_frame + 1) % len(self.loading_images)
                self.animation_time = 0.0

        # 최소 로딩 시간이 지나면 완료 표시
        if self.loading_duration >= self.min_loading_time:
            self.is_complete = True

        return True

    def draw(self):
        """로딩 화면 그리기"""
        # 캔버스 중앙 좌표 계산
        canvas_width = p2.get_canvas_width()
        canvas_height = p2.get_canvas_height()
        center_x = canvas_width // 2
        center_y = canvas_height // 2
        scale = 5.0

        # 캔버스 클리어
        p2.clear_canvas()

        # 검정 배경 이미지로 전체 화면 채우기 (위치를 아래로 이동)
        if self.black_bg:
            # center_y 값을 줄여서 아래로 이동 (0.8을 곱하면 화면 중앙보다 아래로)
            bg_y = center_y * 0.05  # 값을 줄일수록 더 아래로 내려감
            self.black_bg.draw(center_x, bg_y, canvas_width, canvas_height)

        # 배경 그리기
        if self.bg_image:
            self.bg_image.draw(center_x, center_y * 1.55, canvas_width, canvas_height // 2)

        # 로딩 애니메이션 그리기
        if len(self.loading_images) > 0:
            loading_img = self.loading_images[self.current_frame]
            # 화면 하단 중앙에 로딩 애니메이션 배치
            loading_x = center_x
            loading_y = canvas_height // 4  # 하단 1/4 위치

            # 로딩 애니메이션 크기 설정
            loading_width = loading_img.w * scale
            loading_height = loading_img.h * scale

            loading_img.draw(loading_x, loading_y * 3.18, loading_width, loading_height)

        # 추가 애니메이션 그리기 (카트 등)
        if len(self.extra_images) > 0:
            extra_anim = self.loading_info.get('extra_animation', {})
            extra_scale = extra_anim.get('scale', 5.0)
            position = extra_anim.get('position', 'bottom_left')

            extra_img = self.extra_images[self.current_frame]
            extra_width = extra_img.w * extra_scale
            extra_height = extra_img.h * extra_scale

            # 위치에 따라 좌표 계산
            if position == 'bottom_left':
                extra_x = canvas_width // 4  # 왼쪽 1/4 지점
                extra_y = canvas_height // 4  # 하단 1/4 위치
            elif position == 'bottom_right':
                extra_x = canvas_width * 3 // 4  # 오른쪽 3/4 지점
                extra_y = canvas_height // 4
            elif position == 'center':
                extra_x = center_x
                extra_y = center_y
            elif position == 'Cart':
                extra_x = canvas_width // 2 * 1.1
                extra_y = canvas_height // 2 * 1.23
            else:
                extra_x = canvas_width // 4
                extra_y = canvas_height // 4

            extra_img.draw(extra_x, extra_y, extra_width, extra_height)

        # 로딩 텍스트 (옵션)
        # p2.draw_text를 사용하려면 폰트 설정이 필요합니다

    def handle_event(self, e):
        """이벤트 처리 (로딩 중에는 입력 무시)"""
        pass
