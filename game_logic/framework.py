# 게임 전역 프레임워크 변수
delta_time = 0.0
frame_time = 0.01  # 기본 프레임 시간

def set_delta_time(dt):
    global delta_time
    delta_time = dt

def get_delta_time():
    return delta_time

