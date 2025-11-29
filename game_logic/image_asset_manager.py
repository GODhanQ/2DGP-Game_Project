import pico2d as p2
from PIL import Image
import os
import tempfile
import hashlib
from functools import lru_cache

# ==================== 이미지 경로 매핑 시스템 ====================

# pico2d Image 객체와 원본 파일 경로를 매핑하는 딕셔너리
_image_path_map = {}


def _get_image_path(image):
    """
    pico2d Image 객체에서 파일 경로를 가져옵니다.

    Args:
        image: pico2d Image 객체

    Returns:
        파일 경로 문자열 또는 None
    """
    # 1. 매핑 테이블에서 찾기
    image_id = id(image)
    if image_id in _image_path_map:
        return _image_path_map[image_id]

    # 2. filename 속성 확인 (일부 버전에서 지원)
    if hasattr(image, 'filename'):
        path = image.filename
        _image_path_map[image_id] = path
        return path

    # 3. 기타 속성 확인
    for attr in ['file', 'path', '_filename', 'source']:
        if hasattr(image, attr):
            path = getattr(image, attr)
            if path and isinstance(path, str):
                _image_path_map[image_id] = path
                return path

    return None


def register_image_path(image, path):
    """
    이미지 객체와 파일 경로를 수동으로 등록합니다.

    Args:
        image: pico2d Image 객체
        path: 파일 경로
    """
    _image_path_map[id(image)] = path


def load_image_with_path(path):
    """
    이미지를 로드하고 경로를 자동으로 등록합니다.

    Args:
        path: 이미지 파일 경로

    Returns:
        pico2d Image 객체
    """
    try:
        image = p2.load_image(path)
        register_image_path(image, path)
        return image
    except Exception as e:
        print(f'\033[91m[ImageAssetManager] load_image_with_path: 이미지 로드 실패 ({path}): {e}\033[0m')
        return None


# ==================== 캐시 시스템 ====================

# 변환된 이미지 캐시 (메모리 절약)
_image_cache = {}
_cache_enabled = True
_max_cache_size = 100  # 최대 캐시 크기


def enable_cache(enabled=True):
    """
    이미지 캐시 활성화/비활성화

    Args:
        enabled: True면 캐시 활성화, False면 비활성화
    """
    global _cache_enabled
    _cache_enabled = enabled
    if not enabled:
        clear_cache()


def clear_cache():
    """모든 캐시된 이미지 제거"""
    global _image_cache
    _image_cache.clear()
    print(f"[ImageAssetManager] 캐시 클리어 완료")


def set_max_cache_size(size):
    """
    최대 캐시 크기 설정

    Args:
        size: 최대 캐시 항목 수
    """
    global _max_cache_size
    _max_cache_size = size


def get_cache_stats():
    """캐시 통계 반환"""
    return {
        'size': len(_image_cache),
        'max_size': _max_cache_size,
        'enabled': _cache_enabled
    }


def _get_cache_key(image_path, operation, *params):
    """캐시 키 생성"""
    key_string = f"{image_path}_{operation}_{'_'.join(map(str, params))}"
    return hashlib.md5(key_string.encode()).hexdigest()


def _check_cache_limit():
    """캐시 크기 제한 체크 및 정리"""
    global _image_cache
    if len(_image_cache) > _max_cache_size:
        # FIFO 방식으로 오래된 항목 제거
        remove_count = len(_image_cache) - _max_cache_size
        for _ in range(remove_count):
            _image_cache.pop(next(iter(_image_cache)))


# ==================== 기본 색상 조작 함수 (캐싱 적용) ====================

def apply_color_bias(image, r_bias, g_bias, b_bias):
    """
    이미지에 RGB 색상 편이를 적용하여 새로운 이미지를 생성합니다.

    Args:
        image: pico2d Image 객체
        r_bias: Red 채널 편이 값 (-255 ~ 255)
        g_bias: Green 채널 편이 값 (-255 ~ 255)
        b_bias: Blue 채널 편이 값 (-255 ~ 255)

    Returns:
        색상이 조정된 새로운 pico2d Image 객체

    Example:
        >>> original_img = load_image_with_path('player.png')
        >>> red_tinted_img = apply_color_bias(original_img, 50, -20, -20)
        >>> red_tinted_img.draw(400, 300)
    """
    try:
        # 이미지 경로 가져오기
        original_path = _get_image_path(image)

        if not original_path:
            print('\033[91m[ImageAssetManager] apply_color_bias: 이미지 경로를 찾을 수 없습니다. load_image_with_path()를 사용하거나 register_image_path()로 경로를 등록하세요.\033[0m')
            return image

        # 캐시 확인
        if _cache_enabled:
            cache_key = _get_cache_key(original_path, 'bias', r_bias, g_bias, b_bias)
            if cache_key in _image_cache:
                return _image_cache[cache_key]

        # PIL로 이미지 열기
        try:
            pil_image = Image.open(original_path).convert('RGBA')
        except FileNotFoundError:
            print(f'\033[91m[ImageAssetManager] apply_color_bias: 파일을 찾을 수 없습니다: {original_path}\033[0m')
            return image
        except Exception as e:
            print(f'\033[91m[ImageAssetManager] apply_color_bias: 이미지 로드 실패: {e}\033[0m')
            return image

        pixels = pil_image.load()
        width, height = pil_image.size

        # 각 픽셀의 RGB 값 조정
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]

                # 색상 편이 적용 (0-255 범위로 클램핑)
                new_r = max(0, min(255, r + r_bias))
                new_g = max(0, min(255, g + g_bias))
                new_b = max(0, min(255, b + b_bias))

                pixels[x, y] = (new_r, new_g, new_b, a)

        # 임시 파일로 저장
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_path = temp_file.name
                pil_image.save(temp_path, 'PNG')
        except Exception as e:
            print(f'\033[91m[ImageAssetManager] apply_color_bias: 임시 파일 저장 실패: {e}\033[0m')
            return image

        # pico2d로 다시 로드
        try:
            new_image = p2.load_image(temp_path)
            # 새로 생성된 이미지도 경로 등록 (임시 파일이지만 캐시 키로 사용)
            register_image_path(new_image, original_path)
        except Exception as e:
            print(f'\033[91m[ImageAssetManager] apply_color_bias: pico2d 이미지 로드 실패: {e}\033[0m')
            if temp_path:
                try:
                    os.remove(temp_path)
                except:
                    pass
            return image

        # 임시 파일 삭제
        if temp_path:
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f'\033[91m[ImageAssetManager] apply_color_bias: 임시 파일 삭제 실패: {e}\033[0m')

        # 캐시에 저장
        if _cache_enabled:
            _image_cache[cache_key] = new_image
            _check_cache_limit()

        return new_image

    except Exception as e:
        print(f'\033[91m[ImageAssetManager] apply_color_bias: 예기치 않은 오류 발생: {e}\033[0m')
        return image


def apply_color_multiply(image, r_mult, g_mult, b_mult):
    """
    이미지에 RGB 색상 곱셈을 적용하여 새로운 이미지를 생성합니다.

    Args:
        image: pico2d Image 객체
        r_mult: Red 채널 곱셈 값 (0.0 ~ 2.0)
        g_mult: Green 채널 곱셈 값 (0.0 ~ 2.0)
        b_mult: Blue 채널 곱셈 값 (0.0 ~ 2.0)

    Returns:
        색상이 조정된 새로운 pico2d Image 객체

    Example:
        >>> original_img = load_image_with_path('enemy.png')
        >>> darkened_img = apply_color_multiply(original_img, 0.5, 0.5, 0.5)
        >>> darkened_img.draw(400, 300)
    """
    try:
        # 이미지 경로 가져오기
        original_path = _get_image_path(image)

        if not original_path:
            print('\033[91m[ImageAssetManager] apply_color_multiply: 이미지 경로를 찾을 수 없습니다. load_image_with_path()를 사용하거나 register_image_path()로 경로를 등록하세요.\033[0m')
            return image

        # 캐시 확인
        if _cache_enabled:
            cache_key = _get_cache_key(original_path, 'multiply', r_mult, g_mult, b_mult)
            if cache_key in _image_cache:
                return _image_cache[cache_key]

        # PIL로 이미지 열기
        try:
            pil_image = Image.open(original_path).convert('RGBA')
        except FileNotFoundError:
            print(f'\033[91m[ImageAssetManager] apply_color_multiply: 파일을 찾을 수 없습니다: {original_path}\033[0m')
            return image
        except Exception as e:
            print(f'\033[91m[ImageAssetManager] apply_color_multiply: 이미지 로드 실패: {e}\033[0m')
            return image

        pixels = pil_image.load()
        width, height = pil_image.size

        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]

                # 색상 곱셈 적용
                new_r = max(0, min(255, int(r * r_mult)))
                new_g = max(0, min(255, int(g * g_mult)))
                new_b = max(0, min(255, int(b * b_mult)))

                pixels[x, y] = (new_r, new_g, new_b, a)

        # 임시 파일로 저장
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_path = temp_file.name
                pil_image.save(temp_path, 'PNG')
        except Exception as e:
            print(f'\033[91m[ImageAssetManager] apply_color_multiply: 임시 파일 저장 실패: {e}\033[0m')
            return image

        # pico2d로 다시 로드
        try:
            new_image = p2.load_image(temp_path)
            # 새로 생성된 이미지도 경로 등록
            register_image_path(new_image, original_path)
        except Exception as e:
            print(f'\033[91m[ImageAssetManager] apply_color_multiply: pico2d 이미지 로드 실패: {e}\033[0m')
            if temp_path:
                try:
                    os.remove(temp_path)
                except:
                    pass
            return image

        # 임시 파일 삭제
        if temp_path:
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f'\033[91m[ImageAssetManager] apply_color_multiply: 임시 파일 삭제 실패: {e}\033[0m')

        # 캐시에 저장
        if _cache_enabled:
            _image_cache[cache_key] = new_image
            _check_cache_limit()

        return new_image

    except Exception as e:
        print(f'\033[91m[ImageAssetManager] apply_color_multiply: 예기치 않은 오류 발생: {e}\033[0m')
        return image


def apply_hue_shift(image, hue_shift):
    """
    이미지의 색조(Hue)를 변경하여 새로운 이미지를 생성합니다.

    Args:
        image: pico2d Image 객체
        hue_shift: 색조 이동 값 (0 ~ 360 도)

    Returns:
        색조가 조정된 새로운 pico2d Image 객체

    Example:
        >>> original_img = load_image_with_path('character.png')
        >>> purple_img = apply_hue_shift(original_img, 60)
    """
    try:
        # 이미지 경로 가져오기
        original_path = _get_image_path(image)

        if not original_path:
            print('\033[91m[ImageAssetManager] apply_hue_shift: 이미지 경로를 찾을 수 없습니다. load_image_with_path()를 사용하거나 register_image_path()로 경로를 등록하세요.\033[0m')
            return image

        # 캐시 확인
        if _cache_enabled:
            cache_key = _get_cache_key(original_path, 'hue', hue_shift)
            if cache_key in _image_cache:
                return _image_cache[cache_key]

        # PIL로 이미지 열기
        try:
            pil_image = Image.open(original_path).convert('RGBA')
        except FileNotFoundError:
            print(f'\033[91m[ImageAssetManager] apply_hue_shift: 파일을 찾을 수 없습니다: {original_path}\033[0m')
            return image
        except Exception as e:
            print(f'\033[91m[ImageAssetManager] apply_hue_shift: 이미지 로드 실패: {e}\033[0m')
            return image

        # RGB를 HSV로 변환하여 색조 변경
        try:
            rgb_image = pil_image.convert('RGB')
            hsv_image = rgb_image.convert('HSV')
            pixels = hsv_image.load()

            width, height = hsv_image.size

            for y in range(height):
                for x in range(width):
                    h, s, v = pixels[x, y]
                    # 색조 이동 (0-255 범위에서 순환)
                    new_h = (h + int(hue_shift * 255 / 360)) % 256
                    pixels[x, y] = (new_h, s, v)

            # 다시 RGBA로 변환
            rgb_converted = hsv_image.convert('RGB')

            # 원본 알파 채널 복원
            rgb_converted.putalpha(pil_image.split()[3])
        except Exception as e:
            print(f'\033[91m[ImageAssetManager] apply_hue_shift: 색조 변환 실패: {e}\033[0m')
            return image

        # 임시 파일로 저장
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_path = temp_file.name
                rgb_converted.save(temp_path, 'PNG')
        except Exception as e:
            print(f'\033[91m[ImageAssetManager] apply_hue_shift: 임시 파일 저장 실패: {e}\033[0m')
            return image

        # pico2d로 다시 로드
        try:
            new_image = p2.load_image(temp_path)
            # 새로 생성된 이미지도 경로 등록
            register_image_path(new_image, original_path)
        except Exception as e:
            print(f'\033[91m[ImageAssetManager] apply_hue_shift: pico2d 이미지 로드 실패: {e}\033[0m')
            if temp_path:
                try:
                    os.remove(temp_path)
                except:
                    pass
            return image

        # 임시 파일 삭제
        if temp_path:
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f'\033[91m[ImageAssetManager] apply_hue_shift: 임시 파일 삭제 실패: {e}\033[0m')

        # 캐시에 저장
        if _cache_enabled:
            _image_cache[cache_key] = new_image
            _check_cache_limit()

        return new_image

    except Exception as e:
        print(f'\033[91m[ImageAssetManager] apply_hue_shift: 예기치 않은 오류 발생: {e}\033[0m')
        return image


def apply_brightness(image, brightness):
    """
    이미지의 밝기를 조정하여 새로운 이미지를 생성합니다.

    Args:
        image: pico2d Image 객체
        brightness: 밝기 값 (0.0 = 검정, 1.0 = 원본, 2.0 = 2배 밝게)

    Returns:
        밝기가 조정된 새로운 pico2d Image 객체

    Example:
        >>> original_img = p2.load_image('background.png')
        >>> bright_img = apply_brightness(original_img, 1.5)
    """
    return apply_color_multiply(image, brightness, brightness, brightness)


# ==================== 간편 함수 ====================

def make_dark(image, darkness=0.5):
    """
    이미지를 어둡게 만듭니다. (간편 함수)

    Args:
        image: pico2d Image 객체
        darkness: 어둡게 만드는 정도 (0.0 = 완전 검정, 1.0 = 원본)

    Returns:
        어두워진 새로운 pico2d Image 객체

    Example:
        >>> sprite = p2.load_image('character.png')
        >>> dark_sprite = make_dark(sprite, 0.5)  # 50% 어둡게
        >>> very_dark_sprite = make_dark(sprite, 0.3)  # 30% 밝기 (70% 어둡게)
    """
    return apply_brightness(image, darkness)


def make_shadow(image):
    """
    그림자 효과 이미지를 생성합니다. (매우 어둡게)

    Args:
        image: pico2d Image 객체

    Returns:
        그림자처럼 어두운 새로운 pico2d Image 객체

    Example:
        >>> player = p2.load_image('player.png')
        >>> shadow = make_shadow(player)
        >>> shadow.draw(player_x, player_y - 10)  # 발 밑에 그림자
    """
    return apply_brightness(image, 0.2)


def make_night_version(image):
    """
    밤 버전 이미지를 생성합니다. (중간 정도 어둡게)

    Args:
        image: pico2d Image 객체

    Returns:
        밤 버전의 새로운 pico2d Image 객체

    Example:
        >>> day_bg = p2.load_image('background_day.png')
        >>> night_bg = make_night_version(day_bg)
    """
    return apply_brightness(image, 0.4)


# ==================== 프리셋 함수 ====================

def make_damaged_version(image):
    """
    피격 효과 버전 (빨간색 틴트)

    Example:
        >>> player = p2.load_image('player.png')
        >>> hit_effect = make_damaged_version(player)
    """
    return apply_color_bias(image, 100, -30, -30)


def make_frozen_version(image):
    """
    얼음 상태 버전 (파란색 틴트)

    Example:
        >>> enemy = p2.load_image('enemy.png')
        >>> frozen_enemy = make_frozen_version(enemy)
    """
    return apply_color_bias(image, -40, -20, 80)


def make_poison_version(image):
    """
    독 상태 버전 (녹색 틴트)

    Example:
        >>> player = p2.load_image('player.png')
        >>> poisoned = make_poison_version(player)
    """
    return apply_color_bias(image, -30, 50, -30)


def make_golden_version(image):
    """
    황금 버전 (금색 효과)

    Example:
        >>> item = p2.load_image('item.png')
        >>> golden_item = make_golden_version(item)
    """
    return apply_color_bias(image, 80, 60, -40)


def make_invincible_version(image):
    """
    무적 상태 버전 (밝고 하얀 효과)

    Example:
        >>> player = p2.load_image('player.png')
        >>> invincible = make_invincible_version(player)
    """
    return apply_color_multiply(image, 1.5, 1.5, 1.5)


# ==================== 배치 처리 ====================

def batch_process_images(images, operation, *params):
    """
    여러 이미지에 동일한 작업을 배치로 처리

    Args:
        images: pico2d Image 객체 리스트
        operation: 'brightness', 'bias', 'multiply', 'hue' 중 하나
        *params: operation에 필요한 파라미터들

    Returns:
        처리된 이미지 리스트

    Example:
        >>> sprites = [p2.load_image(f'sprite{i}.png') for i in range(5)]
        >>> dark_sprites = batch_process_images(sprites, 'brightness', 0.5)
    """
    try:
        if not images:
            print('\033[91m[ImageAssetManager] batch_process_images: 이미지 리스트가 비어있습니다.\033[0m')
            return []

        results = []

        for i, img in enumerate(images):
            try:
                if operation == 'brightness':
                    results.append(apply_brightness(img, *params))
                elif operation == 'bias':
                    results.append(apply_color_bias(img, *params))
                elif operation == 'multiply':
                    results.append(apply_color_multiply(img, *params))
                elif operation == 'hue':
                    results.append(apply_hue_shift(img, *params))
                else:
                    print(f'\033[91m[ImageAssetManager] batch_process_images: 알 수 없는 작업: {operation}\033[0m')
                    results.append(img)  # 실패시 원본 이미지 추가
            except Exception as e:
                print(f'\033[91m[ImageAssetManager] batch_process_images: 이미지 {i} 처리 실패: {e}\033[0m')
                results.append(img)  # 실패시 원본 이미지 추가

        return results

    except Exception as e:
        print(f'\033[91m[ImageAssetManager] batch_process_images: 예기치 않은 오류 발생: {e}\033[0m')
        return images  # 오류 발생시 원본 리스트 반환


def create_color_variants(image, presets=None):
    """
    하나의 이미지에서 여러 색상 변형 생성

    Args:
        image: 원본 pico2d Image
        presets: 생성할 프리셋 리스트 (None이면 전부)
                ['damaged', 'frozen', 'poison', 'golden', 'shadow']

    Returns:
        딕셔너리 {프리셋명: 변형 이미지}

    Example:
        >>> player = p2.load_image('player.png')
        >>> variants = create_color_variants(player, ['damaged', 'frozen'])
        >>> variants['damaged'].draw(400, 300)
    """
    try:
        if presets is None:
            presets = ['damaged', 'frozen', 'poison', 'golden', 'shadow', 'invincible']

        variants = {}

        for preset in presets:
            try:
                if preset == 'damaged':
                    variants['damaged'] = make_damaged_version(image)
                elif preset == 'frozen':
                    variants['frozen'] = make_frozen_version(image)
                elif preset == 'poison':
                    variants['poison'] = make_poison_version(image)
                elif preset == 'golden':
                    variants['golden'] = make_golden_version(image)
                elif preset == 'shadow':
                    variants['shadow'] = make_shadow(image)
                elif preset == 'invincible':
                    variants['invincible'] = make_invincible_version(image)
                elif preset == 'night':
                    variants['night'] = make_night_version(image)
                else:
                    print(f'\033[91m[ImageAssetManager] create_color_variants: 알 수 없는 프리셋: {preset}\033[0m')
            except Exception as e:
                print(f'\033[91m[ImageAssetManager] create_color_variants: {preset} 프리셋 생성 실패: {e}\033[0m')

        return variants

    except Exception as e:
        print(f'\033[91m[ImageAssetManager] create_color_variants: 예기치 않은 오류 발생: {e}\033[0m')
        return {}


# ==================== 리소스 관리 ====================

class ImageVariantManager:
    """
    이미지 변형 버전들을 관리하는 클래스
    게임 시작 시 미리 생성하여 성능 향상
    """

    def __init__(self):
        self.originals = {}
        self.variants = {}

    def register_image(self, name, image_path):
        """
        원본 이미지 등록

        Args:
            name: 이미지 식별 이름
            image_path: 이미지 파일 경로
        """
        try:
            self.originals[name] = p2.load_image(image_path)
            self.variants[name] = {}
        except FileNotFoundError:
            print(f'\033[91m[ImageVariantManager] register_image: 파일을 찾을 수 없습니다: {image_path}\033[0m')
        except Exception as e:
            print(f'\033[91m[ImageVariantManager] register_image: 이미지 등록 실패 ({name}): {e}\033[0m')

    def create_variant(self, name, variant_name, operation, *params):
        """
        특정 이미지의 변형 생성

        Args:
            name: 원본 이미지 이름
            variant_name: 변형 버전 이름
            operation: 'brightness', 'bias', 'multiply', 'hue'
            *params: operation 파라미터
        """
        try:
            if name not in self.originals:
                print(f'\033[91m[ImageVariantManager] create_variant: 이미지 \'{name}\'이 등록되지 않았습니다.\033[0m')
                return

            original = self.originals[name]

            if operation == 'brightness':
                variant = apply_brightness(original, *params)
            elif operation == 'bias':
                variant = apply_color_bias(original, *params)
            elif operation == 'multiply':
                variant = apply_color_multiply(original, *params)
            elif operation == 'hue':
                variant = apply_hue_shift(original, *params)
            else:
                print(f'\033[91m[ImageVariantManager] create_variant: 알 수 없는 작업: {operation}\033[0m')
                return

            self.variants[name][variant_name] = variant
        except Exception as e:
            print(f'\033[91m[ImageVariantManager] create_variant: 변형 생성 실패 ({name}/{variant_name}): {e}\033[0m')

    def create_all_presets(self, name):
        """
        모든 프리셋 변형 생성

        Args:
            name: 원본 이미지 이름
        """
        try:
            if name not in self.originals:
                print(f'\033[91m[ImageVariantManager] create_all_presets: 이미지 \'{name}\'이 등록되지 않았습니다.\033[0m')
                return

            original = self.originals[name]
            variants = create_color_variants(original)
            self.variants[name].update(variants)
        except Exception as e:
            print(f'\033[91m[ImageVariantManager] create_all_presets: 프리셋 생성 실패 ({name}): {e}\033[0m')

    def get(self, name, variant_name=None):
        """
        이미지 가져오기

        Args:
            name: 이미지 이름
            variant_name: 변형 버전 이름 (None이면 원본)

        Returns:
            pico2d Image 객체
        """
        try:
            if variant_name is None:
                if name not in self.originals:
                    print(f'\033[91m[ImageVariantManager] get: 이미지 \'{name}\'을 찾을 수 없습니다.\033[0m')
                    return None
                return self.originals.get(name)

            if name not in self.variants:
                print(f'\033[91m[ImageVariantManager] get: 이미지 \'{name}\'의 변형을 찾을 수 없습니다.\033[0m')
                return None

            if variant_name not in self.variants[name]:
                print(f'\033[91m[ImageVariantManager] get: 변형 \'{variant_name}\'을 찾을 수 없습니다 (이미지: {name}).\033[0m')
                return None

            return self.variants.get(name, {}).get(variant_name)
        except Exception as e:
            print(f'\033[91m[ImageVariantManager] get: 이미지 가져오기 실패 ({name}/{variant_name}): {e}\033[0m')
            return None

    def clear(self):
        """모든 이미지 제거"""
        try:
            self.originals.clear()
            self.variants.clear()
        except Exception as e:
            print(f'\033[91m[ImageVariantManager] clear: 캐시 클리어 실패: {e}\033[0m')


# 전역 매니저 인스턴스
_global_manager = ImageVariantManager()


def get_global_manager():
    """전역 이미지 매니저 가져오기"""
    return _global_manager


# ==================== 테스트 및 정보 ====================

if __name__ == "__main__":
    print("Image Asset Manager - Color Manipulation Module")
    print("=" * 60)

    print("\n💡 기본 함수:")
    print("  1. apply_color_bias(image, r, g, b)")
    print("  2. apply_color_multiply(image, r, g, b)")
    print("  3. apply_hue_shift(image, hue)")
    print("  4. apply_brightness(image, brightness)")

    print("\n🌙 간편 함수:")
    print("  1. make_dark(image, darkness=0.5)")
    print("  2. make_shadow(image)")
    print("  3. make_night_version(image)")

    print("\n🎨 프리셋 함수:")
    print("  1. make_damaged_version(image)    # 빨간 틴트")
    print("  2. make_frozen_version(image)     # 파란 틴트")
    print("  3. make_poison_version(image)     # 녹색 틴트")
    print("  4. make_golden_version(image)     # 금색 효과")
    print("  5. make_invincible_version(image) # 밝은 효과")

    print("\n📦 캐싱 함수:")
    print("  1. enable_cache(True/False)")
    print("  2. clear_cache()")
    print("  3. set_max_cache_size(size)")
    print("  4. get_cache_stats()")

    print("\n⚡ 배치 처리:")
    print("  1. batch_process_images(images, operation, *params)")
    print("  2. create_color_variants(image, presets)")

    print("\n🗂️ 리소스 매니저:")
    print("  manager = ImageVariantManager()")
    print("  manager.register_image('player', 'player.png')")
    print("  manager.create_all_presets('player')")
    print("  manager.get('player', 'damaged').draw(x, y)")

    print("\n" + "=" * 60)
    print("\n📝 사용 예시:")
    print("-" * 60)
    print("""
# 1. 기본 사용
original = p2.load_image('sprite.png')
dark = make_dark(original, 0.5)

# 2. 캐싱 활성화 (성능 향상)
enable_cache(True)
set_max_cache_size(50)

# 3. 배치 처리
sprites = [p2.load_image(f's{i}.png') for i in range(5)]
dark_sprites = batch_process_images(sprites, 'brightness', 0.5)

# 4. 리소스 매니저 사용 (권장)
manager = get_global_manager()
manager.register_image('player', 'resources/player.png')
manager.create_all_presets('player')

# 게임 루프에서
manager.get('player', 'damaged').draw(x, y)  # 피격 상태
manager.get('player', 'frozen').draw(x, y)   # 얼음 상태
    """)
