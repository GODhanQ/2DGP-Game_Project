# game_logic/loading_screen.py
"""스테이지 로딩 화면 모듈"""

import pico2d as p2
import game_framework as framework

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
                - loading_message (optional): 로딩 메시지 {'title', 'subtitle', 'tip'}
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

        # 폰트 로드 (텍스트 렌더링용)
        self.font_title = None
        self.font_subtitle = None
        self.font_tip = None
        self._load_fonts()

        # 이미지 로드
        self._load_images()

        print(f"[LoadingScreen] Stage {self.stage_number} 로딩 화면 초기화 완료")

    def _load_fonts(self):
        """로딩 화면에 사용할 폰트 로드"""
        font_path = 'resources/Fonts/pixelroborobo.otf'
        try:
            # 제목용 폰트 (큰 크기)
            self.font_title = p2.load_font(font_path, 60)
            # 부제목용 폰트 (중간 크기)
            self.font_subtitle = p2.load_font(font_path, 40)
            # 팁용 폰트 (작은 크기)
            self.font_tip = p2.load_font(font_path, 30)
            print(f"[LoadingScreen] 폰트 로드 완료: {font_path}")
        except Exception as e:
            print(f"\033[91m[LoadingScreen] 폰트 로드 실패: {e}\033[0m")
            # 폰트 로드 실패 시 None 유지

    def _load_images(self):
        """로딩 화면 이미지들을 로드"""
        try:
            # 검정 배경 이미지 로드
            black_bg_path = 'resources/Texture_organize/UI/Stage_Loading/BlackBG.png'
            self.black_bg = p2.load_image(black_bg_path)
            print(f"[LoadingScreen] 검정 배경 이미지 로드 완료: {black_bg_path}")

            # 배경 이미지 로드
            if self.loading_info['bg_image'] is not None:
                bg_path = self.loading_info['bg_image']
                self.bg_image = p2.load_image(bg_path)
                print(f"[LoadingScreen] 배경 이미지 로드 완료: {bg_path}")
            else:
                print(f'\033[93m[LoadingScreen] 배경 이미지가 없습니다.\033[0m')
                self.bg_image = None

            # 로딩 애니메이션 이미지 로드
            try:
                animation_prefix = self.loading_info['animation_prefix']
                animation_count = self.loading_info['animation_count']
            except Exception as ex:
                print(f'\033[93m[LoadingScreen] 애니메이션 정보가 없습니다. : {ex}\033[0m')
                animation_prefix = None
                animation_count = 0

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

        # 로딩 메시지 텍스트 그리기 (검정 배경 위에 표시)
        loading_message = self.loading_info.get('loading_message')
        if loading_message:
            title = loading_message.get('title', '')
            subtitle = loading_message.get('subtitle', '')
            tip = loading_message.get('tip', '')

            # 텍스트 색상 (흰색)
            text_color = (255, 255, 255)

            # 제목 그리기 (화면 중앙)
            if title and self.font_title:
                # 텍스트 길이 추정 (대략적으로 계산)
                title_width = len(title) * 35  # 폰트 크기 60 기준 대략적인 너비
                title_x = center_x - title_width // 2
                title_y = center_y * 0.8

                # 그림자 효과 (가독성 향상)
                self.font_title.draw(title_x - 2, title_y - 2, title, (0, 0, 0))
                # 실제 텍스트
                self.font_title.draw(title_x, title_y, title, text_color)

            # 부제목 그리기 (제목 아래)
            if subtitle and self.font_subtitle:
                # 텍스트 길이 추정
                subtitle_width = len(subtitle) * 24  # 폰트 크기 40 기준
                subtitle_x = center_x - subtitle_width // 2
                subtitle_y = center_y * 0.65

                # 그림자 효과
                self.font_subtitle.draw(subtitle_x - 2, subtitle_y - 2, subtitle, (0, 0, 0))
                # 실제 텍스트
                self.font_subtitle.draw(subtitle_x, subtitle_y, subtitle, text_color)

            # 팁 그리기 (부제목 아래)
            if tip and self.font_tip:
                # 텍스트 길이 추정
                tip_width = len(tip) * 18  # 폰트 크기 30 기준
                tip_x = center_x - tip_width // 2
                tip_y = center_y * 0.5

                # 그림자 효과
                self.font_tip.draw(tip_x - 2, tip_y - 2, tip, (0, 0, 0))
                # 실제 텍스트 (노란색으로 표시)
                self.font_tip.draw(tip_x, tip_y, tip, (255, 255, 100))

    def handle_event(self, e):
        """이벤트 처리 (로딩 중에는 입력 무시)"""
        pass
