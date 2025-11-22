"""
간단한 배경 이미지 클래스
"""
import pico2d as p2


class FixedBackground:
    """고정된 배경 이미지를 표시하는 클래스"""

    def __init__(self, image_path, width, height):
        """
        Args:
            image_path: 배경 이미지 경로
            width: 배경 이미지 너비
            height: 배경 이미지 높이
        """
        try:
            self.image = p2.load_image(image_path)
            self.width = width
            self.height = height
            # 배경의 월드 좌표 (맵 중심 기준)
            self.x = 0
            self.y = 0
            self.scale = 1.0
            print(f"[FixedBackground] 배경 이미지 로드 성공: {image_path}")
        except Exception as e:
            print(f"[FixedBackground] 배경 이미지 로드 실패: {image_path}, 에러: {e}")
            self.image = None
            self.width = width
            self.height = height
            self.x = 0
            self.y = 0
            self.scale = 1.0

    def update(self):
        """배경은 업데이트가 필요 없음"""
        return True

    def draw(self, draw_x, draw_y):
        """배경 이미지 그리기 (카메라 좌표 적용)

        Args:
            draw_x: 카메라가 적용된 화면 x 좌표
            draw_y: 카메라가 적용된 화면 y 좌표
        """
        if self.image:
            self.image.draw(
                draw_x,
                draw_y,
                self.width,
                self.height
            )
