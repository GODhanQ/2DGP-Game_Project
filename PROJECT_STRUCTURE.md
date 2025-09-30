# 프로젝트 구조 및 아키텍처

## 전체 구조

```
2DGP-Game_Project/
│
├── README.md                           # 프로젝트 메인 문서
├── Game_Project_Presentation.md       # 프로젝트 발표 자료
├── PROJECT_STRUCTURE.md               # 이 문서
│
├── src/                               # 소스 코드 디렉토리
│   ├── main.py                       # 게임 실행 진입점
│   │
│   ├── core/                         # 핵심 시스템
│   │   ├── game.py                  # 게임 메인 루프
│   │   ├── scene_manager.py        # 씬 전환 관리
│   │   ├── input_manager.py        # 입력 처리
│   │   └── resource_manager.py     # 리소스 로딩
│   │
│   ├── entities/                     # 게임 엔티티
│   │   ├── player.py                # 플레이어 캐릭터
│   │   ├── monster.py               # 일반 몬스터
│   │   ├── boss.py                  # 보스 몬스터
│   │   └── entity_base.py           # 엔티티 베이스 클래스
│   │
│   ├── systems/                      # 게임 시스템
│   │   ├── combat_system.py        # 전투 시스템
│   │   ├── skill_system.py         # 스킬 시스템
│   │   ├── animation_system.py     # 애니메이션 시스템
│   │   └── collision_system.py     # 충돌 감지 시스템
│   │
│   ├── map/                          # 맵 관련
│   │   ├── map_manager.py          # 맵 관리
│   │   ├── tile.py                 # 타일 클래스
│   │   └── room.py                 # 방/씬 클래스
│   │
│   ├── ai/                           # AI 시스템
│   │   ├── state_machine.py        # 상태 머신
│   │   ├── behaviors.py            # AI 행동 패턴
│   │   └── pathfinding.py          # 경로 탐색
│   │
│   ├── ui/                           # UI 시스템
│   │   ├── hud.py                  # HUD (체력, 마나 등)
│   │   ├── inventory.py            # 인벤토리
│   │   ├── menu.py                 # 메뉴 시스템
│   │   └── dialogue.py             # 대화 시스템
│   │
│   └── utils/                        # 유틸리티
│       ├── constants.py            # 상수 정의
│       ├── math_utils.py           # 수학 유틸
│       └── debug.py                # 디버그 도구
│
├── assets/                           # 게임 리소스
│   ├── sprites/                     # 스프라이트 이미지
│   │   ├── player/                 # 플레이어 스프라이트
│   │   ├── monsters/               # 몬스터 스프라이트
│   │   ├── bosses/                 # 보스 스프라이트
│   │   ├── effects/                # 이펙트 스프라이트
│   │   └── ui/                     # UI 스프라이트
│   │
│   ├── maps/                        # 맵 데이터
│   │   ├── level_01.json          # 레벨 1 맵 데이터
│   │   ├── level_02.json          # 레벨 2 맵 데이터
│   │   └── tilesets/              # 타일셋 이미지
│   │
│   ├── sounds/                      # 효과음
│   │   ├── player/                # 플레이어 효과음
│   │   ├── monsters/              # 몬스터 효과음
│   │   └── environment/           # 환경 효과음
│   │
│   ├── music/                       # 배경음악
│   │   ├── menu.mp3
│   │   ├── stage_01.mp3
│   │   └── boss_battle.mp3
│   │
│   └── data/                        # 게임 데이터
│       ├── skills.json            # 스킬 데이터
│       ├── monsters.json          # 몬스터 데이터
│       └── items.json             # 아이템 데이터
│
├── docs/                            # 문서
│   ├── design/                     # 디자인 문서
│   │   ├── game_design.md         # 게임 디자인
│   │   ├── level_design.md        # 레벨 디자인
│   │   └── character_design.md    # 캐릭터 디자인
│   │
│   └── technical/                  # 기술 문서
│       ├── architecture.md        # 아키텍처
│       └── api_reference.md       # API 레퍼런스
│
└── tests/                           # 테스트 코드
    ├── test_player.py
    ├── test_combat.py
    └── test_collision.py
```

## 핵심 클래스 다이어그램

### 1. Entity 계층 구조

```
Entity (Base Class)
├── position: Vector2
├── velocity: Vector2
├── sprite: Sprite
├── state: State
│
├── Player
│   ├── health: int
│   ├── mana: int
│   ├── skills: List[Skill]
│   ├── input_handler: InputHandler
│   └── methods:
│       ├── move()
│       ├── jump()
│       ├── attack()
│       └── use_skill()
│
└── Monster
    ├── health: int
    ├── attack_power: int
    ├── ai_controller: AIController
    ├── drop_items: List[Item]
    └── methods:
        ├── patrol()
        ├── chase()
        └── attack()
        │
        └── Boss (extends Monster)
            ├── phases: List[Phase]
            ├── special_attacks: List[Attack]
            └── methods:
                ├── change_phase()
                └── special_attack()
```

### 2. 시스템 구조

```
Game Loop
    │
    ├─► Input System
    │   └─► Process player input
    │
    ├─► Update Systems
    │   ├─► Physics System
    │   │   └─► Update positions, apply gravity
    │   │
    │   ├─► AI System
    │   │   └─► Update monster behaviors
    │   │
    │   ├─► Combat System
    │   │   └─► Process attacks, damage
    │   │
    │   └─► Animation System
    │       └─► Update sprite frames
    │
    ├─► Collision Detection
    │   └─► Check and resolve collisions
    │
    └─► Render System
        ├─► Draw background
        ├─► Draw entities
        ├─► Draw effects
        └─► Draw UI
```

## 데이터 구조

### Map Data (JSON)
```json
{
  "width": 100,
  "height": 50,
  "layers": [
    {
      "name": "background",
      "tiles": [[...]]
    },
    {
      "name": "collision",
      "tiles": [[...]]
    }
  ],
  "entities": [
    {
      "type": "monster",
      "id": "slime_01",
      "position": [10, 5]
    }
  ],
  "transitions": [
    {
      "from": [95, 25],
      "to": "level_02",
      "spawn": [5, 25]
    }
  ]
}
```

### Skill Data (JSON)
```json
{
  "skills": [
    {
      "id": "slash",
      "name": "Slash Attack",
      "type": "melee",
      "damage": 10,
      "cooldown": 0.5,
      "mana_cost": 0,
      "animation": "player_attack_01"
    },
    {
      "id": "fireball",
      "name": "Fireball",
      "type": "projectile",
      "damage": 25,
      "cooldown": 2.0,
      "mana_cost": 10,
      "animation": "fireball_cast"
    }
  ]
}
```

### Monster Data (JSON)
```json
{
  "monsters": [
    {
      "id": "slime",
      "name": "Slime",
      "health": 30,
      "attack_power": 5,
      "speed": 2,
      "ai_type": "patrol",
      "drop_items": ["coin", "slime_gel"],
      "sprites": {
        "idle": "slime_idle.png",
        "move": "slime_move.png",
        "attack": "slime_attack.png"
      }
    }
  ]
}
```

## 상태 머신 다이어그램

### Player States
```
┌─────────────┐
│    IDLE     │◄─────────┐
└──────┬──────┘          │
       │                 │
       ├──►┌─────────┐   │
       │   │  WALK   │───┘
       │   └─────────┘
       │
       ├──►┌─────────┐
       │   │  JUMP   │
       │   └─────────┘
       │
       ├──►┌─────────┐
       │   │  DASH   │
       │   └─────────┘
       │
       ├──►┌─────────┐
       │   │ ATTACK  │
       │   └─────────┘
       │
       └──►┌─────────┐
           │   HIT   │
           └─────────┘
```

### Monster AI States
```
┌─────────────┐
│   PATROL    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   DETECT    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    CHASE    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   ATTACK    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   RETREAT   │
└─────────────┘
```

## 개발 우선순위

### 1차 개발 (프로토타입)
1. 기본 게임 루프
2. 플레이어 이동 (좌우, 점프)
3. 간단한 맵 (타일)
4. 카메라 시스템

### 2차 개발 (핵심 기능)
1. 플레이어 공격
2. 몬스터 추가 (간단한 AI)
3. 충돌 감지
4. 체력/마나 시스템

### 3차 개발 (콘텐츠)
1. 다양한 스킬
2. 여러 종류의 몬스터
3. 보스 전투
4. 맵 확장

### 4차 개발 (폴리싱)
1. 애니메이션 개선
2. 이펙트 추가
3. 사운드/음악
4. UI 완성

## 코딩 규칙

### 네이밍 컨벤션
- **클래스**: PascalCase (예: `PlayerController`)
- **함수/메서드**: snake_case (예: `update_position`)
- **상수**: UPPER_SNAKE_CASE (예: `MAX_HEALTH`)
- **변수**: snake_case (예: `current_health`)

### 파일 구조
```python
# 파일 상단: 임포트
import pico2d
from typing import List, Tuple

# 상수 정의
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# 클래스 정의
class Player:
    """플레이어 캐릭터를 나타내는 클래스"""
    
    def __init__(self, x: int, y: int):
        """초기화 메서드"""
        pass
    
    def update(self, delta_time: float):
        """업데이트 메서드"""
        pass
    
    def draw(self):
        """그리기 메서드"""
        pass
```

## 성능 고려사항

1. **객체 풀링**: 자주 생성/삭제되는 객체 (발사체, 이펙트)
2. **공간 분할**: 충돌 감지 최적화 (Quad-tree)
3. **타일 컬링**: 화면에 보이는 타일만 그리기
4. **애니메이션 최적화**: 스프라이트 아틀라스 사용

## 버그 추적 및 테스트

### 테스트 항목
- [ ] 플레이어 움직임 테스트
- [ ] 충돌 감지 테스트
- [ ] 스킬 시스템 테스트
- [ ] AI 행동 테스트
- [ ] 맵 전환 테스트
- [ ] 성능 테스트

### 알려진 이슈
- 추후 업데이트 예정

---

**문서 버전**: 1.0
**최종 업데이트**: 2024
