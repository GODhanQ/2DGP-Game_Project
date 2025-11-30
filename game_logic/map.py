import os
from typing import Dict, List, Tuple, Optional

try:
    from pico2d import draw_rectangle
except Exception:
    # pico2d가 없으면 draw_rectangle을 대체하는 더미 함수로 허용
    def draw_rectangle(l, b, r, t):
        # no-op in headless/static analysis
        return


SUPPORTED_SECTIONS = ['ground', 'upper_ground', 'walls', 'cliff', 'props']


class TileEntity:
    """맵에 배치되는 간단한 타일 엔티티.
    실제 프로젝트에서는 이미지(tileset)과 애니메이션, 충돌박스 등을 연결해서 사용하면 됩니다.
    """

    def __init__(self, tile_id: int, x: int, y: int, size: int, layer: str):
        self.tile_id = int(tile_id)
        self.x = int(x)
        self.y = int(y)
        self.size = int(size)
        self.layer = layer

    def update(self):
        # 기본 타일은 고정이므로 True를 반환하여 계속 유지
        return True

    def draw(self):
        # 디버그용 간단한 사각형 그리기 (pico2d가 있으면 보임)
        l = self.x
        b = self.y
        r = self.x + self.size
        t = self.y + self.size
        draw_rectangle(l, b, r, t)


class Map:
    def __init__(self, tile_size: int = 32):
        self.tile_size = int(tile_size)
        # 각 섹션에 대해 2D 리스트(행 리스트)로 타일 인덱스를 보관
        self.layers: Dict[str, List[List[int]]] = {s: [] for s in SUPPORTED_SECTIONS}
        self.width = 0
        self.height = 0

    @staticmethod
    def _normalize_section_name(name: str) -> str:
        return name.strip().lower()

    def load_from_room_txt(self, path: str) -> None:
        """
        Room.txt 형식(간단한 INI 스타일)을 파싱하여 self.layers에 채웁니다.
        빈 라인 또는 주석(//, ;, #)은 무시합니다.

        변경: 토큰 구분자는 공백(whitespace)을 사용합니다. 라인 내의 ','는 공백으로 대체되어
        기존 콤마 형식과도 호환됩니다. 토큰 '0' 및 'X'/'x'는 빈 타일(0)으로 처리됩니다.
        """
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Room file not found: {path}")

        current = None
        with open(path, 'r', encoding='utf-8') as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                if line.startswith('//') or line.startswith('#') or line.startswith(';'):
                    continue
                if line.startswith('[') and line.endswith(']'):
                    sec = self._normalize_section_name(line[1:-1])
                    if sec not in SUPPORTED_SECTIONS:
                        # 새 섹션을 만드려 하지 말고 지원되는 섹션만 처리
                        current = None
                        continue
                    current = sec
                    # reset existing content for the section
                    self.layers[current] = []
                    continue

                if current is None:
                    # 섹션 밖의 데이터는 무시
                    continue

                # ',' 구분자를 공백으로 바꿔 공백 분할을 사용하여 유연하게 처리
                normalized = line.replace(',', ' ')
                parts = [p.strip() for p in normalized.split() if p.strip() != '']
                if not parts:
                    continue
                row: List[int] = []
                for p in parts:
                    # '0' 과 'X' 또는 'x' 를 빈타일로 처리
                    if p == '0' or p.lower() == 'x':
                        row.append(0)
                        continue
                    try:
                        row.append(int(p))
                    except ValueError:
                        # 숫자로 변환할 수 없는 토큰이 있으면 빈타일로 처리
                        row.append(0)
                self.layers[current].append(row)

        # 맵 전체 크기 계산 (가장 큰 폭/높이 사용)
        max_w = 0
        max_h = 0
        for sec in SUPPORTED_SECTIONS:
            h = len(self.layers.get(sec, []))
            if h > max_h:
                max_h = h
            for row in self.layers.get(sec, []):
                if len(row) > max_w:
                    max_w = len(row)
        self.width = max_w
        self.height = max_h

    def build_into_world(self, world: Dict[str, list], tile_size: Optional[int] = None, origin: Tuple[int, int] = (0, 0), replace: bool = True) -> None:
        """
        파싱된 레이어 데이터를 바탕으로 `world` 딕셔너리의 레이어 리스트에 TileEntity들을 추가합니다.
        - world: main.py에서 사용되는 world 딕셔너리 (예: keys: 'ground','upper_ground','walls',...)
        - tile_size: 맵의 타일 픽셀 크기 (기본은 Map.tile_size)
        - origin: (x0,y0) 맵 원점 좌표 (왼쪽 하단 기준)
        - replace: True이면 이 함수가 추가할 레이어(ground/upper_ground/walls)의 기존 리스트를 비우고 새로 채웁니다.

        이 함수는 props 섹션은 현재 무시합니다.
        """
        ts = int(tile_size) if tile_size is not None else self.tile_size
        x0, y0 = origin

        target_layers = ['ground', 'upper_ground', 'walls']
        if replace:
            for tl in target_layers:
                if tl in world and isinstance(world[tl], list):
                    world[tl].clear()

        # 맵 데이터의 행렬은 텍스트 상에서는 보통 위에서 아래로 작성됨을 가정.
        # 여기서는 텍스트 행(0)이 맵의 "상단"이라고 가정하고 화면 좌표로는 높이를 고려해 y를 계산합니다.
        for sec in ['ground', 'upper_ground', 'walls', 'cliff']:
            rows = self.layers.get(sec, [])
            h = len(rows)
            for row_idx, row in enumerate(rows):
                # 텍스트의 첫 행 -> 맵 상단이므로 y 계산
                # 맵 상단을 origin_y + (height - 1 - row_idx) * ts 로 배치
                for col_idx, tile_id in enumerate(row):
                    if tile_id == 0:
                        continue
                    # compute position
                    # bottom-left origin
                    x = x0 + col_idx * ts
                    y = y0 + (self.height - 1 - row_idx) * ts
                    ent = TileEntity(tile_id=tile_id, x=x, y=y, size=ts, layer=sec)
                    # 저장된 그리드 좌표를 붙여 두면 나중에 크기 변경 시 재계산에 사용 가능
                    ent._grid_col = col_idx
                    ent._grid_row = row_idx
                    ent._map_height = self.height
                    ent._origin = (x0, y0)
                    # 월드에 맞는 레이어 키가 존재하면 append
                    if sec == 'ground':
                        world.setdefault('ground', []).append(ent)
                    elif sec == 'upper_ground':
                        world.setdefault('upper_ground', []).append(ent)
                    elif sec == 'walls' or sec == 'cliff':
                        # 벽/절벽은 충돌 처리용으로 walls 레이어에 넣음
                        world.setdefault('walls', []).append(ent)
                    else:
                        # props 등은 현재 무시
                        pass

    def rebuild_into_world(self, world: Dict[str, list], tile_size: Optional[int] = None, origin: Tuple[int, int] = (0, 0)) -> None:
        """
        편의 메서드: 기존 내용을 교체(replace=True)하여 다시 빌드합니다.
        """
        self.build_into_world(world, tile_size=tile_size, origin=origin, replace=True)

    def apply_tile_size_to_world(self, world: Dict[str, list], new_tile_size: int, origin: Tuple[int, int] = (0, 0)) -> None:
        """
        기존에 world에 배치된 TileEntity들이 그리드 좌표를 가지고 있다면,
        각 엔티티의 size와 x,y를 새 타일 크기에 맞게 in-place로 갱신합니다.
        - world: 월드 딕셔너리
        - new_tile_size: 적용할 새 타일 크기
        - origin: 맵 원점

        이 방법은 엔티티를 새로 생성하지 않으므로 외부 참조가 유지됩니다.
        만약 엔티티에 그리드 좌표가 없다면 동작하지 않습니다(그럴 경우 재빌드 필요).
        """
        ts = int(new_tile_size)
        x0, y0 = origin
        layers = ['ground', 'upper_ground', 'walls']
        updated = 0
        for layer in layers:
            for ent in list(world.get(layer, [])):
                # ent가 grid 정보(_grid_col/_grid_row/_map_height)를 가지고 있으면 위치 재계산
                if hasattr(ent, '_grid_col') and hasattr(ent, '_grid_row') and hasattr(ent, '_map_height'):
                    col = int(ent._grid_col)
                    row = int(ent._grid_row)
                    map_h = int(ent._map_height)
                    ent.size = ts
                    ent.x = x0 + col * ts
                    ent.y = y0 + (map_h - 1 - row) * ts
                    # update stored origin too
                    ent._origin = (x0, y0)
                    updated += 1
                else:
                    # grid 정보가 없으면 이 엔티티는 무시 (재빌드를 권장)
                    continue
        try:
            print(f"apply_tile_size_to_world: applied new_tile_size={ts}, updated_entities={updated}")
        except Exception:
            pass

    def set_tile_size(self, new_tile_size: int, world: Optional[Dict[str, list]] = None, origin: Tuple[int, int] = (0, 0)) -> None:
        """
        Map의 기본 타일 크기를 변경합니다. 만약 `world`를 전달하면 해당 월드에 대해
        가능한 경우 in-place로 크기/위치를 갱신하고, grid 정보가 부족하면 재빌드를 수행합니다.
        """
        self.tile_size = int(new_tile_size)
        if world is not None:
            # 먼저 시도: in-place 적용 (grid 좌표가 있는 경우)
            # 검사: 모든 엔티티들이 grid 좌표를 가지고 있는지 확인
            ok = True
            total = 0
            for layer in ['ground', 'upper_ground', 'walls']:
                for ent in world.get(layer, []):
                    total += 1
                    if not (hasattr(ent, '_grid_col') and hasattr(ent, '_grid_row') and hasattr(ent, '_map_height')):
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                try:
                    self.apply_tile_size_to_world(world, self.tile_size, origin)
                    print(f"set_tile_size: in-place applied to {total} entities, new_tile_size={self.tile_size}")
                except Exception as e:
                    print(f"\033[91mset_tile_size: in-place apply failed: {e}\033[0m")
            else:
                # 일부 엔티티에 grid 정보가 없으면 안전하게 재빌드
                try:
                    self.rebuild_into_world(world, tile_size=self.tile_size, origin=origin)
                    print(f"set_tile_size: rebuilt world with new_tile_size={self.tile_size}")
                except Exception as e:
                    print(f"\033[91mset_tile_size: rebuild failed: {e}\033[0m")

