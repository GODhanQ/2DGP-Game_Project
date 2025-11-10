Room.txt 기반 맵 로더 (간단 사용법)

개요
- `game_logic/map.py`에 Room.txt를 파싱하여 `world` 딕셔너리에 `TileEntity`를 추가하는 간단한 Map 클래스가 있습니다.

Room.txt 형식(예시)
- 섹션: [ground], [upper_ground], [walls], [cliff], [props]
- 각 섹션 아래에 콤마(,)로 구분된 정수 행을 작성합니다. 0은 빈 칸(타일 없음)입니다.

예:
[ground]
1,1,1,0,0
1,2,2,0,0

[upper_ground]
0,0,3,3,0

[walls]
0,4,0,0,0

동작 방식
- `Map.load_from_room_txt(path)` : Room.txt 파싱
- `Map.build_into_world(world, tile_size=None, origin=(0,0))` : 파싱된 타일을 `world`의 레이어(ground, upper_ground, walls)에 `TileEntity`로 추가
- `TileEntity.draw()`는 현재 `pico2d.draw_rectangle`을 사용한 디버그용 사각형입니다.

통합 팁
- `main.py`는 자동으로 프로젝트 루트와 `resources/`에서 `Room.txt` 또는 `room.txt`를 찾아 로드합니다.
- 실제 타일 이미지를 사용하려면 `TileEntity`에 이미지 속성(예: `image`)을 추가하고, `tile_id` → 이미지 매핑 로직을 구현하면 됩니다.

다음 권장 작업
- 타일 ID를 실제 tileset 이미지에 매핑하는 로더 추가
- 벽/절벽 타일에 충돌 박스(solid flag) 추가
- props 섹션 파싱 및 props 엔티티 추가

