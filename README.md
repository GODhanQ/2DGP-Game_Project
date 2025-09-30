# 2DGP Game Project
# 2D 플랫포머 RPG 게임 프로젝트

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)

## 프로젝트 개요

Hollow Knight에서 영감을 받은 2D 플랫포머 RPG 게임 프로젝트입니다.

### 장르
- **타입**: 2D Platformer RPG
- **영감**: Hollow Knight
- **개발 도구**: Python + Pico2D

## 주요 구현 목표

1. **캐릭터 움직임** 🎮
   - 좌우 이동, 점프, 2단 점프
   - 대시 및 벽 점프
   - 부드러운 애니메이션

2. **맵 구현** 🗺️
   - 타일 기반 맵 시스템
   - 여러 레이어 지원
   - 연결된 방과 비밀 영역

3. **스킬 구현** ⚔️
   - 기본 공격 콤보
   - 특수 스킬 시스템
   - 스킬 업그레이드

4. **몬스터 및 보스 구현** 👹
   - 다양한 AI 패턴
   - 단계별 보스 전투
   - 도전적인 전투 시스템

## 프로젝트 문서

📊 **[게임 프로젝트 발표 자료](Game_Project_Presentation.md)** - 상세한 프로젝트 기획 및 구현 계획

## 개발 로드맵

### Phase 1: 프로토타입 (2-3주)
- [x] 프로젝트 기획 및 발표 자료 작성
- [ ] 기본 캐릭터 움직임 구현
- [ ] 간단한 맵 구현
- [ ] 기본 UI 구현

### Phase 2: 핵심 시스템 (4-5주)
- [ ] 완성된 캐릭터 컨트롤
- [ ] 타일 맵 시스템
- [ ] 기본 전투 시스템
- [ ] 몬스터 AI 기초

### Phase 3: 콘텐츠 제작 (4-6주)
- [ ] 다양한 맵 제작
- [ ] 스킬 시스템 구현
- [ ] 여러 종류 몬스터
- [ ] 보스 전투

### Phase 4: 완성 및 테스트 (2-3주)
- [ ] 게임 밸런싱
- [ ] 버그 수정
- [ ] 사운드 및 음악
- [ ] 최종 폴리싱

## 기술 스택

- **언어**: Python 3.x
- **게임 라이브러리**: Pico2D
- **버전 관리**: Git/GitHub
- **그래픽**: Sprite/Pixel Art

## 설치 방법

```bash
# 저장소 클론
git clone https://github.com/GODhanQ/2DGP-Game_Project.git
cd 2DGP-Game_Project

# 필요한 패키지 설치 (추후 업데이트 예정)
pip install pico2d
```

## 프로젝트 구조 (예정)

```
2DGP-Game_Project/
├── src/                    # 소스 코드
│   ├── main.py            # 게임 진입점
│   ├── player.py          # 플레이어 클래스
│   ├── map.py             # 맵 시스템
│   ├── monster.py         # 몬스터/보스 클래스
│   ├── skill.py           # 스킬 시스템
│   └── ui.py              # UI 시스템
├── assets/                 # 게임 리소스
│   ├── sprites/           # 스프라이트 이미지
│   ├── maps/              # 맵 데이터
│   ├── sounds/            # 효과음
│   └── music/             # 배경음악
├── docs/                   # 문서
│   └── design/            # 디자인 문서
└── tests/                  # 테스트 코드
```

## 참고 자료

- [Hollow Knight](https://www.hollowknight.com/) - 메인 영감 소스
- [Pico2D Documentation](https://github.com/kd-tree/pico2d) - 게임 라이브러리
- [Game Programming Patterns](https://gameprogrammingpatterns.com/) - 디자인 패턴

## 기여 방법

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 연락처

프로젝트 링크: [https://github.com/GODhanQ/2DGP-Game_Project](https://github.com/GODhanQ/2DGP-Game_Project)

---

**Made with ❤️ for 2DGP Course**
