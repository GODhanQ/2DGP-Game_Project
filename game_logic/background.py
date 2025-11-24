"""
간단한 배경 이미지 클래스
"""
import pico2d as p2


class FixedBackground:
    """화면에 고정된 배경 이미지를 표시하는 클래스 (카메라 스크롤에 영향받지 않음)"""

    def __init__(self, image_path, width, height, scale=1.0):
        """
        Args:
            image_path: 배경 이미지 경로
            width: 배경 이미지 너비
            height: 배경 이미지 높이
            scale: 배경 이미지 스케일
        """
        try:
            self.image = p2.load_image(image_path)
            self.width = width
            self.height = height
            # 배경은 카메라에 영향받지 않으므로 x, y는 화면 중앙 기준
            self.x = 0
            self.y = 0
            self.scale = scale
            print(f"[FixedBackground] 배경 이미지 로드 성공: {image_path}")
        except Exception as e:
            print(f"\033[91m[FixedBackground] 배경 이미지 로드 실패: {image_path}, 에러: {e}\033[0m")
            self.image = None
            self.width = width
            self.height = height
            self.x = 0
            self.y = 0
            self.scale = 1.0

    def update(self):
        """배경은 업데이트가 필요 없음"""
        return True

    def draw(self):
        """배경 이미지 그리기 (카메라 영향 없이 화면 중앙에 고정)

        Note:
            FixedBackground는 카메라 스크롤의 영향을 받지 않고
            항상 화면 중앙에 고정되어 표시됩니다.
        """
        if self.image:
            # 화면 중앙 좌표 계산
            screen_center_x = p2.get_canvas_width() // 2
            screen_center_y = p2.get_canvas_height() // 2

            self.image.draw(screen_center_x, screen_center_y,
                            self.width * self.scale, self.height * self.scale)


class StageMap:
    """
    스테이지 맵 이미지를 표시하는 클래스
    카메라 좌표가 적용되며, 플레이어가 자유롭게 돌아다닐 수 있는 맵
    """

    def __init__(self, image_path, width, height):
        """
        Args:
            image_path: 맵 이미지 경로
            width: 맵 이미지 표시 너비 (scale 적용된 값)
            height: 맵 이미지 표시 높이 (scale 적용된 값)
        """
        try:
            self.image = p2.load_image(image_path)
            self.width = width
            self.height = height
            # 맵의 월드 좌표 (맵 중심 기준, 기본적으로 (0, 0)에 배치)
            self.x = 0
            self.y = 0
            self.scale = 1.0
            print(f"[StageMap] 맵 이미지 로드 성공: {image_path}")
        except Exception as e:
            print(f"\033[91m[StageMap] 맵 이미지 로드 실패: {image_path}, 에러: {e}\033[0m")
            self.image = None
            self.width = width
            self.height = height
            self.x = 0
            self.y = 0
            self.scale = 1.0

    def update(self):
        """맵은 업데이트가 필요 없음"""
        return True

    def draw(self, draw_x, draw_y):
        """맵 이미지 그리기 (카메라 좌표 적용)

        Args:
            draw_x: 카메라가 적용된 화면 x 좌표
            draw_y: 카메라가 적용된 화면 y 좌표
        """
        if self.image:
            # width와 height는 이미 scale이 적용된 값이므로 그대로 사용
            self.image.draw(
                draw_x,
                draw_y,
                self.width,
                self.height
            )

            # 디버깅용: 맵 경계를 초록색으로 표시 (필요시 주석 해제)
            # p2.draw_rectangle(
            #     draw_x - self.width / 2,
            #     draw_y - self.height / 2,
            #     draw_x + self.width / 2,
            #     draw_y + self.height / 2
            # )
