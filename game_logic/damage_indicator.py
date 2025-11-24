import pico2d as p2
from PIL import Image, ImageDraw, ImageFont
import io

import game_framework as framework

class DamageIndicator:
    """
    데미지를 화면에 표시하는 인디케이터 클래스
    지정된 시간 동안 위로 올라가면서 페이드아웃 효과를 보여줍니다.
    텍스트를 이미지로 렌더링하여 알파값(투명도)이 제대로 적용되도록 합니다.
    """

    def __init__(self, x, y, damage, duration=1.0, font_size=20):
        """
        데미지 인디케이터 초기화

        Args:
            x: 월드 x 좌표
            y: 월드 y 좌표
            damage: 표시할 데미지 값
            duration: 인디케이터가 표시될 시간 (초)
            font_size: 폰트 크기
        """
        self.x = x
        self.y = y
        self.damage = damage
        self.duration = duration
        self.elapsed = 0.0
        self.font_size = font_size
        self.mark_for_removal = False  # 제거 플래그

        # PIL 폰트 로드 (텍스트를 이미지로 렌더링하기 위함)
        self.pil_font_path = 'resources/Fonts/pixelroborobo.otf'
        try:
            self.pil_font = ImageFont.truetype(self.pil_font_path, font_size)
        except Exception as e:
            print(f"[DamageIndicator] PIL 폰트 로드 실패: {e}, 기본 폰트 사용")
            self.pil_font = ImageFont.load_default()

        # 텍스트 내용
        self.text = f"{int(damage)}"

        # 텍스트 이미지를 미리 생성 (알파값만 나중에 변경)
        self.text_images = {}  # 알파값별로 캐싱 (성능 최적화)
        self.current_image = None
        self.image_width = 0
        self.image_height = 0

    def _create_text_image(self, alpha):
        """
        텍스트를 이미지로 렌더링 (알파값 적용)

        Args:
            alpha: 투명도 (0.0 ~ 1.0)

        Returns:
            pico2d Image 객체
        """
        # 알파값을 10단계로 양자화하여 캐싱 (성능 최적화)
        alpha_key = int(alpha * 10) / 10.0

        if alpha_key in self.text_images:
            return self.text_images[alpha_key]

        # PIL로 텍스트 이미지 생성
        # 먼저 텍스트 크기를 측정
        bbox = self.pil_font.getbbox(self.text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 여유 공간을 두고 이미지 생성
        img_width = text_width + 10
        img_height = text_height + 10

        # RGBA 모드로 투명 배경 이미지 생성
        pil_image = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(pil_image)

        # 텍스트 색상 + 알파값 적용
        r, g, b = 255, 0, 0
        text_color = (r, g, b, int(alpha * 255))

        # 텍스트 그리기 (중앙 정렬)
        draw.text((5, 5), self.text, font=self.pil_font, fill=text_color)

        # PIL 이미지를 pico2d 이미지로 변환
        # 임시 파일로 저장 후 로드하는 방식
        try:
            # 메모리 버퍼를 사용하여 임시 파일 생성
            buffer = io.BytesIO()
            pil_image.save(buffer, format='PNG')
            buffer.seek(0)

            # 임시 파일명 생성 (알파값 포함)
            temp_filename = f'temp_damage_{id(self)}_{alpha_key}.png'
            with open(temp_filename, 'wb') as f:
                f.write(buffer.getvalue())

            # pico2d로 이미지 로드
            p2d_image = p2.load_image(temp_filename)

            # 임시 파일 삭제
            import os
            try:
                os.remove(temp_filename)
            except:
                pass

            # 이미지 크기 저장
            self.image_width = img_width
            self.image_height = img_height

            # 캐싱
            self.text_images[alpha_key] = p2d_image

            return p2d_image

        except Exception as e:
            print(f"[DamageIndicator] 이미지 변환 실패: {e}")
            return None

    def update(self):
        """
        인디케이터 업데이트 - 위로 이동하고 시간 경과 체크

        Returns:
            bool: 계속 유지되어야 하면 True, 제거되어야 하면 False
        """
        delta_time = framework.get_delta_time()
        self.elapsed += delta_time
        self.y += 30 * delta_time  # 시간에 따라 위로 이동

        # duration 이후에는 제거 표시
        if self.elapsed >= self.duration:
            self.mark_for_removal = True
            return False  # 제거되어야 함을 반환

        return True  # 계속 유지

    def draw(self, draw_x, draw_y):
        """
        데미지 인디케이터 그리기 (페이드아웃 효과 포함)
        텍스트 이미지를 사용하여 알파값이 제대로 적용되도록 합니다.

        Args:
            draw_x: 카메라가 적용된 화면 x 좌표
            draw_y: 카메라가 적용된 화면 y 좌표
        """
        # 알파 값 계산 (시간이 지남에 따라 투명해짐)
        alpha = max(0.0, 1.0 - (self.elapsed / self.duration))

        # 알파값에 맞는 텍스트 이미지 생성/로드
        text_image = self._create_text_image(alpha)

        if text_image:
            # 이미지 그리기 (중앙 정렬)
            text_image.draw(
                draw_x,
                draw_y,
                self.image_width,
                self.image_height
            )

    def is_expired(self):
        """
        인디케이터가 만료되었는지 확인

        Returns:
            bool: 만료되었으면 True
        """
        return self.elapsed >= self.duration

    def __del__(self):
        """
        소멸자 - 캐싱된 이미지 리소스 정리
        """
        # 캐싱된 이미지들을 정리
        self.text_images.clear()


# Example usage:
# 데미지 인디케이터를 월드에 추가하는 방법:
# damage_indicator = DamageIndicator(monster.x, monster.y + 20, final_damage, duration=1.0, font_size=30)
# world['effects_front'].append(damage_indicator)
