# 빠른 참조 가이드 (Quick Reference)

## 프로젝트 개요

**장르**: 2D 플랫포머 RPG  
**영감**: Hollow Knight  
**개발 도구**: Python + Pico2D  
**예상 기간**: 12-16주  

---

## 문서 구조

| 문서 | 설명 | 대상 |
|------|------|------|
| `README.md` | 프로젝트 소개 및 시작 가이드 | 모든 사용자 |
| `Game_Project_Presentation.md` | 프로젝트 발표 자료 (PPT 대체) | 발표/평가 |
| `PROJECT_STRUCTURE.md` | 코드 구조 및 아키텍처 | 개발자 |
| `DEVELOPMENT_ROADMAP.md` | 개발 일정 및 마일스톤 | 프로젝트 관리 |
| `QUICK_REFERENCE.md` | 이 문서 | 빠른 참조 |

---

## 핵심 구현 목표

### 1. 캐릭터 움직임 🎮
```python
# 구현할 동작
- 좌우 이동 (가속/감속)
- 점프 (높이 조절)
- 2단 점프
- 대시
- 벽 점프
- 공격 중 이동
```

### 2. 맵 구현 🗺️
```python
# 구현할 요소
- 타일 기반 맵 시스템
- 여러 레이어 (배경, 충돌, 전경)
- 연결된 방 (3-5개)
- 상호작용 오브젝트
- 함정 및 비밀 영역
```

### 3. 스킬 구현 ⚔️
```python
# 구현할 스킬
1. 기본 공격 (3단 콤보)
2. 강 공격 (차지)
3. 원거리 공격 (발사체)
4. 범위 공격 (AoE)
5. 버프/디버프 스킬
```

### 4. 몬스터 및 보스 👹
```python
# 구현할 적
- 일반 몬스터: 5종류
  ├─ 슬라임 (근접)
  ├─ 박쥐 (비행)
  ├─ 해골 전사 (근접)
  ├─ 고블린 궁수 (원거리)
  └─ 골렘 (탱커)

- 보스: 2종류
  ├─ 숲의 수호자 (3 페이즈)
  └─ 어둠의 기사 (3 페이즈)
```

---

## 개발 단계 요약

| Phase | 주차 | 주요 작업 | 완료 기준 |
|-------|------|-----------|-----------|
| 1. 프로토타입 | 1-2 | 기본 설정 | 플레이어 이동 가능 |
| 2. 캐릭터 | 3-5 | 움직임 시스템 | 모든 동작 완성 |
| 3. 맵 | 6-8 | 맵 시스템 | 3개 맵 완성 |
| 4. 전투 | 9-11 | 전투/스킬 | 몬스터 전투 가능 |
| 5. 보스 | 12-14 | 보스 전투 | 2개 보스 완성 |
| 6. 폴리싱 | 15-16 | 사운드/버그 | 완성 |

---

## 핵심 클래스 구조

### Player 클래스
```python
class Player:
    # 속성
    position: Vector2
    velocity: Vector2
    health: int
    mana: int
    state: PlayerState
    
    # 메서드
    def update(dt)
    def move(direction)
    def jump()
    def attack()
    def use_skill(skill_id)
```

### Monster 클래스
```python
class Monster:
    # 속성
    position: Vector2
    health: int
    attack_power: int
    ai_state: AIState
    
    # 메서드
    def update(dt)
    def patrol()
    def chase(target)
    def attack()
```

### Map 클래스
```python
class Map:
    # 속성
    tiles: List[List[Tile]]
    collision_layer: List[List[bool]]
    entities: List[Entity]
    
    # 메서드
    def load(filename)
    def get_tile(x, y)
    def check_collision(x, y)
```

---

## 주요 시스템

### 1. 게임 루프
```
┌─────────────────────┐
│   게임 시작          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   초기화             │
│   - 리소스 로드      │
│   - 화면 설정        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   ◄──────────┐      │
│   게임 루프   │      │
│   ├─ 입력     │      │
│   ├─ 업데이트 │      │
│   ├─ 충돌     │      │
│   └─ 렌더링   │      │
│   ───────────┘      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   종료               │
└─────────────────────┘
```

### 2. 상태 머신
```python
# 플레이어 상태
class PlayerState(Enum):
    IDLE = 0
    WALK = 1
    JUMP = 2
    FALL = 3
    DASH = 4
    ATTACK = 5
    HIT = 6
    DEAD = 7
```

### 3. 충돌 감지
```python
def check_collision(rect1, rect2):
    """AABB 충돌 감지"""
    return (rect1.left < rect2.right and
            rect1.right > rect2.left and
            rect1.top < rect2.bottom and
            rect1.bottom > rect2.top)
```

---

## 파일 구조 (간단 버전)

```
2DGP-Game_Project/
├── src/
│   ├── main.py              # 시작점
│   ├── player.py            # 플레이어
│   ├── monster.py           # 몬스터
│   ├── map.py               # 맵
│   ├── skill.py             # 스킬
│   └── ui.py                # UI
│
├── assets/
│   ├── sprites/             # 이미지
│   ├── maps/                # 맵 데이터
│   ├── sounds/              # 효과음
│   └── music/               # 배경음악
│
└── docs/                    # 문서들
```

---

## 자주 사용하는 Pico2D 함수

### 기본 설정
```python
from pico2d import *

# 초기화
open_canvas(width, height)
close_canvas()

# 이미지
img = load_image('path/to/image.png')
img.draw(x, y)
img.draw(x, y, width, height)

# 프레임
draw_img.clip_draw(sx, sy, sw, sh, x, y, w, h)

# 입력
event = get_events()
for e in event:
    if e.type == SDL_KEYDOWN:
        if e.key == SDLK_LEFT:
            # 왼쪽 키
```

### 게임 루프
```python
def main():
    open_canvas()
    
    # 초기화
    player = Player()
    
    while True:
        clear_canvas()
        
        # 업데이트
        player.update()
        
        # 그리기
        player.draw()
        
        update_canvas()
        delay(0.01)
    
    close_canvas()
```

---

## 유용한 상수

```python
# 화면 크기
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# 물리
GRAVITY = -980  # 픽셀/초^2
JUMP_POWER = 500  # 픽셀/초
MOVE_SPEED = 300  # 픽셀/초

# 게임플레이
PLAYER_MAX_HEALTH = 100
PLAYER_MAX_MANA = 50
DASH_COOLDOWN = 1.0  # 초
ATTACK_DAMAGE = 10

# 타일
TILE_SIZE = 32  # 픽셀
```

---

## 디버깅 팁

### 1. 출력 디버깅
```python
print(f"Player pos: ({self.x}, {self.y})")
print(f"Player state: {self.state}")
```

### 2. 시각적 디버깅
```python
# 충돌 박스 그리기
draw_rectangle(x1, y1, x2, y2)
```

### 3. 프레임률 확인
```python
import time
fps_start = time.time()
frame_count = 0
# 매 프레임마다
frame_count += 1
if frame_count % 60 == 0:
    fps = 60 / (time.time() - fps_start)
    print(f"FPS: {fps}")
    fps_start = time.time()
```

---

## 테스트 체크리스트

### 캐릭터 움직임
- [ ] 좌우 이동 부드러움
- [ ] 점프 높이 적절
- [ ] 2단 점프 작동
- [ ] 대시 쿨다운 작동
- [ ] 벽 점프 방향 정확
- [ ] 애니메이션 자연스러움

### 전투 시스템
- [ ] 공격 히트 정확
- [ ] 데미지 계산 정확
- [ ] 스킬 쿨다운 작동
- [ ] 마나 소모 정확
- [ ] 넉백 작동

### 맵 시스템
- [ ] 충돌 감지 정확
- [ ] 맵 전환 부드러움
- [ ] 카메라 추적 자연스러움
- [ ] 타일 정렬 정확

### AI 시스템
- [ ] 순찰 패턴 자연스러움
- [ ] 플레이어 감지 작동
- [ ] 추격 로직 정확
- [ ] 공격 타이밍 적절

---

## 일반적인 문제 해결

### 문제: 플레이어가 바닥을 통과함
```python
# 해결: 충돌 처리 추가
if player.y <= ground_y:
    player.y = ground_y
    player.velocity_y = 0
    player.on_ground = True
```

### 문제: 애니메이션이 너무 빠름
```python
# 해결: 프레임 속도 조절
self.frame_delay = 0.1  # 초
self.frame_timer += delta_time
if self.frame_timer >= self.frame_delay:
    self.frame = (self.frame + 1) % self.frame_count
    self.frame_timer = 0
```

### 문제: 입력 반응이 느림
```python
# 해결: 즉시 상태 변경
def handle_event(self, event):
    if event.type == SDL_KEYDOWN:
        if event.key == SDLK_SPACE:
            self.jump()  # 바로 점프
```

---

## 다음 단계

### 지금 당장
1. ✅ 문서 읽기 (지금 하는 중)
2. [ ] 개발 환경 설정
3. [ ] 첫 번째 프로토타입 시작

### 이번 주
- [ ] `main.py` 작성
- [ ] 기본 플레이어 이동
- [ ] 간단한 맵 표시

### 이번 달
- [ ] 캐릭터 움직임 완성
- [ ] 맵 시스템 구축
- [ ] 첫 몬스터 추가

---

## 리소스

### 학습 자료
- Pico2D 공식 문서
- Python 게임 프로그래밍 튜토리얼
- 게임 디자인 패턴

### 무료 에셋
- OpenGameArt.org
- itch.io (Free Assets)
- Kenney.nl

### 참고 게임
- Hollow Knight (주요 영감)
- Celeste (플랫포머 참고)
- Dead Cells (전투 참고)

---

## 연락처 및 도움

**프로젝트 저장소**: https://github.com/GODhanQ/2DGP-Game_Project

**이슈 제기**: GitHub Issues 사용

---

**마지막 업데이트**: 2024
**버전**: 1.0
