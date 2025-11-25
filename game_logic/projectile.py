"""
투사체(Projectile) 베이스 클래스
모든 발사체는 이 클래스를 상속받아 구현합니다.
"""
import pico2d as p2
import math
import game_framework as framework


class Projectile:
    """투사체 베이스 클래스

    모든 투사체(수리검, 화살, 마법탄 등)가 상속받는 기본 클래스입니다.
    이 클래스를 상속받으면 play_mode에서 자동으로 충돌 검사가 수행됩니다.

    Attributes:
        x, y: 투사체 위치
        speed: 이동 속도
        dx, dy: 정규화된 방향 벡터
        from_player: 플레이어가 쏜 투사체인지 (True), 몬스터가 쏜 투사체인지 (False)
    """

    def __init__(self, x, y, target_x, target_y, speed=400, from_player=False):
        """
        Args:
            x, y: 시작 위치
            target_x, target_y: 목표 위치
            speed: 이동 속도 (픽셀/초)
            from_player: 플레이어가 쏜 투사체인지 여부
        """
        self.x = x
        self.y = y
        self.speed = speed
        self.from_player = from_player

        # Bounding box 크기 초기화
        self.collision_width, self.collision_height = 30, 30

        # 방향 벡터 계산
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx**2 + dy**2)

        if dist > 0:
            self.dx = dx / dist
            self.dy = dy / dist
        else:
            self.dx = 0
            self.dy = -1 if not from_player else 1

    def update(self):
        """투사체 위치 업데이트

        Returns:
            bool: True면 계속 존재, False면 제거
        """
        dt = framework.get_delta_time()
        self.x += self.dx * self.speed * dt
        self.y += self.dy * self.speed * dt

        # 화면 밖으로 나가면 제거
        if (self.x < -1000 or self.x > p2.get_canvas_width() + 1000 or
            self.y < -1000 or self.y > p2.get_canvas_height() + 1000):
            return False

        return True

    def draw(self, draw_x, draw_y):
        """투사체 렌더링 (서브클래스에서 구현)

        Args:
            draw_x: 카메라 좌표가 적용된 x 위치
            draw_y: 카메라 좌표가 적용된 y 위치
        """
        pass

    def get_collision_box(self):
        """충돌 박스 반환 (서브클래스에서 오버라이드 가능)

        Returns:
            tuple: (width, height) 충돌 박스 크기
        """
        return (self.collision_width, self.collision_height)
