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
            print(f"[FixedBackground] 배경 이미지 로드 성공: {image_path}")
        except Exception as e:
            print(f"[FixedBackground] 배경 이미지 로드 실패: {image_path}, 에러: {e}")
            self.image = None
            self.width = width
            self.height = height

    def update(self):
        """배경은 업데이트가 필요 없음"""
        return True

    def draw(self):
        """배경 이미지 그리기"""
        if self.image:
            # 화면 중앙에 배경 그리기
            canvas_width = p2.get_canvas_width()
            canvas_height = p2.get_canvas_height()

            self.image.draw(
                canvas_width // 2,
                canvas_height // 2,
                self.width,
                self.height
            )

