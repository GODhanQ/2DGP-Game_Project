# 게임 전역 프레임워크 변수
delta_time = 0.0
frame_time = 0.01  # 기본 프레임 시간
paused = False  # 시뮬레이션 일시정지 플래그


def set_delta_time(dt):
    global delta_time
    delta_time = dt


def get_delta_time():
    # 시뮬레이션이 일시정지 되어 있으면 dt는 0으로 반환하여 업데이트가 멈추게 함
    return 0.0 if paused else delta_time


def set_paused(flag: bool):
    global paused
    paused = bool(flag)


def get_paused():
    return paused
