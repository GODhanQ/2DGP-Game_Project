# 패키지 내부 모듈. 공용 아이템 팩토리와 샘플 세트 제공
from .inventory import Item

# 개별 아이템 팩토리 (파일 경로는 Item 폴더 상대 경로)

class lantern:
    def __new__(cls):
        return Item.from_filename('Lantern.png', '랜턴')


class magic_glasses:
    def __new__(cls):
        return Item.from_filename('MagicGlasses.png', '마법 안경',
                                  passive={'crit_chance': 0.05})

class rabbit_guard_helm:
    def __new__(cls):
        return Item.from_filename('RabbitGuardHelm.png', '토끼 수호자 투구',
                                  passive={'defense': 5.0})

class carrot:
    def __new__(cls):
        return Item.from_filename('Carrot.png', '당근',
                                  consumable={'move_speed': 50.0}, consume_duration=8.0)

class amber:
    def __new__(cls):
        return Item.from_filename('Amber.png', '호박보석',
                                  passive={'attack_damage': 2.0})

class ruby:
    def __new__(cls):
        return Item.from_filename('Ruby.png', '루비',
                                  passive={'attack_damage': 3.0})

class white_bread:
    def __new__(cls):
        return Item.from_filename('WhiteCrustedBread.png', '하얀 빵',
                                  consumable={'defense': 2.0}, consume_duration=10.0)

class potion_red0:
    def __new__(cls):
        item = Item.from_filename('Potion/Item_RedPotion0.png', '빨간 포션',
                                  consumable={'attack_damage': 5.0}, consume_duration=15.0)

        # VFX 리소스 경로
        item.consume_vfx_path = r'resources\Texture_organize\VFX\Potion_Common'
        # VFX 시각 크기 배율(기본 1.0 -> 2.0으로 키움)
        item.consume_vfx_scale = 2.0

        # 소비 시 호출 가능한 안전한 콜백 (consumer는 플레이어 엔티티)
        def _play_consume_vfx(consumer, world=None, x=None, y=None):
            import sys
            import os

            # debug
            try:
                print(f"[items._play_consume_vfx] called for item {getattr(item,'name', getattr(item,'id', 'Unknown'))}, world_set={bool(world)}")
            except Exception:
                pass

            # 안전한 world 조회 (폴백)
            w = world
            if w is None:
                main_mod = sys.modules.get('__main__')
                if main_mod:
                    w = getattr(main_mod, 'world', None)
            if not w:
                print('[items._play_consume_vfx] no world available, aborting VFX')
                return

            # 위치 결정
            px = x if x is not None else getattr(consumer, 'x', None)
            py = y if y is not None else getattr(consumer, 'y', None)

            # 경로 확인
            vfx_folder = getattr(item, 'consume_vfx_path', None)
            if not vfx_folder:
                print('[items._play_consume_vfx] item has no consume_vfx_path')
                return
            # normalize folder path
            vfx_folder = os.path.normpath(vfx_folder)

            print(f"[items._play_consume_vfx] vfx_folder={vfx_folder} px={px} py={py}")

            # 기본 옵션
            frame_time = getattr(item, 'consume_vfx_frame_time', 0.06)

            # 가능한 파일명 접두사(백/프론트)와 프레임 수
            back_prefixes = ['Potion_Back_FX', 'Potionl_Back_FX', 'Potion_Back_FX00', 'Potion_Back_FX0']
            front_prefixes = ['Potion_Front_FX', 'Potion_Front_FX00', 'Potion_Front_FX0']
            back_frames = getattr(item, 'consume_vfx_back_frames', 8)
            front_frames = getattr(item, 'consume_vfx_front_frames', 4)

            # 우선 world.spawn_vfx API가 있다면 사용 (지원하면 더 간단)
            spawn = getattr(w, 'spawn_vfx', None)
            if callable(spawn):
                print('[items._play_consume_vfx] using world.spawn_vfx API')
                try:
                    # spawn a back effect (if files exist)
                    for bp in back_prefixes:
                        try:
                            spawn(os.path.join(vfx_folder, bp), px, py, frames=back_frames, frame_time=frame_time, layer='effects_back', loop=False)
                            print(f'[items._play_consume_vfx] spawned back with prefix {bp}')
                            break
                        except Exception:
                            print(f'[items._play_consume_vfx] spawn back failed for prefix {bp}')
                            continue
                except Exception:
                    pass
                try:
                    for fp in front_prefixes:
                        try:
                            spawn(os.path.join(vfx_folder, fp), px, py, frames=front_frames, frame_time=frame_time, layer='effects_front', loop=False)
                            print(f'[items._play_consume_vfx] spawned front with prefix {fp}')
                            break
                        except Exception:
                            print(f'[items._play_consume_vfx] spawn front failed for prefix {fp}')
                            continue
                except Exception:
                    pass
                return

            # fallback: create AnimatedVFX and append to world layers
            try:
                from .vfx import AnimatedVFX
            except Exception:
                AnimatedVFX = None

            # candidate layer names to try for back/front
            back_layer_candidates = ['effects_back', 'effects.back', 'vfx_back', 'back_effects', 'effects_back_layer', 'effects_back']
            front_layer_candidates = ['effects_front', 'effects.front', 'vfx_front', 'front_effects', 'effects_front_layer', 'effects_front']

            # helper to find or create layer list
            def _find_layer(lst_candidates):
                for name in lst_candidates:
                    if name in w and isinstance(w[name], list):
                        return name
                # if none found, create the first candidate key as empty list
                name = lst_candidates[0]
                try:
                    w.setdefault(name, [])
                    return name
                except Exception:
                    return None

            back_layer = _find_layer(back_layer_candidates)
            front_layer = _find_layer(front_layer_candidates)

            # create and append back VFX
            if AnimatedVFX is not None and back_layer is not None:
                # try prefixes until frames load
                for bp in back_prefixes:
                    try:
                        # pass bp unchanged; AnimatedVFX will look for bp00, bp01 ...
                        vfx = AnimatedVFX(vfx_folder, bp, back_frames, frame_time, px, py, scale=getattr(item, 'consume_vfx_scale', 1.0), life=back_frames*frame_time)
                        # debug
                        print(f'[items._play_consume_vfx] created AnimatedVFX for back prefix {bp} frames_loaded={getattr(vfx, "frames_count", 0)}')
                        # only append if frames loaded
                        if getattr(vfx, 'frames_count', 0) > 0:
                            w[back_layer].append(vfx)
                            print(f'[items._play_consume_vfx] appended back vfx to layer {back_layer}')
                            break
                    except Exception as ex:
                        print(f'[items._play_consume_vfx] back prefix {bp} failed:', ex)
                        continue

            # create and append front VFX
            if AnimatedVFX is not None and front_layer is not None:
                for fp in front_prefixes:
                    try:
                        vfx = AnimatedVFX(vfx_folder, fp, front_frames, frame_time, px, py, scale=getattr(item, 'consume_vfx_scale', 1.0), life=front_frames*frame_time)
                        print(f'[items._play_consume_vfx] created AnimatedVFX for front prefix {fp} frames_loaded={getattr(vfx, "frames_count", 0)}')
                        if getattr(vfx, 'frames_count', 0) > 0:
                            w[front_layer].append(vfx)
                            print(f'[items._play_consume_vfx] appended front vfx to layer {front_layer}')
                            break
                    except Exception as ex:
                        print(f'[items._play_consume_vfx] front prefix {fp} failed:', ex)
                        continue

            # 마지막 폴백: world에 'vfx' 리스트 추가
            try:
                if 'vfx' not in w:
                    w['vfx'] = []
                # if nothing added and AnimatedVFX available, add a combined short effect
                if AnimatedVFX is not None and (front_layer is None and back_layer is None):
                    try:
                        v = AnimatedVFX(vfx_folder, front_prefixes[0], front_frames, frame_time, px, py, scale=getattr(item, 'consume_vfx_scale', 1.0))
                        if getattr(v, 'frames_count', 0) > 0:
                            w['vfx'].append(v)
                            print('[items._play_consume_vfx] appended fallback vfx to w[vfx]')
                    except Exception:
                        pass
            except Exception:
                pass

        item.on_consume_vfx = _play_consume_vfx
        return item



# 디버그용 샘플 목록 생성기

def sample_debug_list():
    """디버그 시드에 사용할 (Item, qty) 리스트를 반환"""
    return [
        (lantern(), 1),
        (magic_glasses(), 1),
        (rabbit_guard_helm(), 1),
        (carrot(), 3),              # 비스택: 각 1개씩 여러 슬롯
        (amber(), 2),
        (ruby(), 2),
        (white_bread(), 1),
        (potion_red0(), 15),        # 스택: 한 슬롯에 누적
    ]
