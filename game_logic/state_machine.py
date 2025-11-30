from .event_to_string import event_to_string
import game_framework
from .inventory import InventoryData


class StateMachine:
    def __init__(self, start_state, rules):
        self.cur_state = start_state
        self.rules = rules
        self.cur_state.enter(('START', None))

    def update(self):
        self.cur_state.do()

    def draw(self, draw_x = None, draw_y = None):
        self.cur_state.draw(draw_x, draw_y)

    def current_state(self):
        return self.cur_state

    def set_state(self, state):
        self.cur_state = state

    def handle_state_event(self, state_event):
        processed_event = False
        for check_event in self.rules[self.cur_state].keys():
            if check_event(state_event):
                next_state = self.rules[self.cur_state][check_event]

                # 특수 처리: INVENTORY 상태에서 Tab_down이면 prev_state로 복귀
                if next_state is None and hasattr(self.cur_state, 'prev_state') and self.cur_state.prev_state is not None:
                    next_state = self.cur_state.prev_state

                # 특수 처리: DASH 상태에서 DASH_END이면 return_to_idle에 따라 IDLE 또는 RUN으로 복귀
                if next_state is None and hasattr(self.cur_state, 'return_to_idle'):
                    # Dash의 return_to_idle 플래그 확인
                    if self.cur_state.return_to_idle:
                        # Idle로 복귀
                        next_state = self.cur_state.player.IDLE
                    else:
                        # Run으로 복귀
                        next_state = self.cur_state.player.RUN

                self.cur_state.exit(state_event)
                next_state.enter(state_event)

                print(f'{self.cur_state.__class__.__name__}'
                      f' ======{event_to_string(state_event)}======> '
                      f'{next_state.__class__.__name__}')
                self.cur_state = next_state
                processed_event = True
                return
        if not processed_event:
            event_str = event_to_string(state_event)
            es = event_str.upper() if isinstance(event_str, str) else ''
            is_mouse_motion = ('MOUSE' in es and 'MOTION' in es) or ('MOUSEMOTION' in es)
            if not is_mouse_motion:
                # print('Refused Event:', self.cur_state.__class__.__name__, 'Input : ', event_to_string(state_event))
                pass
