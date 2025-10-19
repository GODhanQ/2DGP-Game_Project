from .event_to_string import event_to_string
from . import framework

class StateMachine:
    def __init__(self, start_state, rules):
        self.cur_state = start_state
        self.rules = rules
        self.cur_state.enter(('START', None))

    def update(self):
        self.cur_state.do()

    def draw(self):
        self.cur_state.draw()

    def handle_state_event(self, state_event):
        processed_event = False
        for check_event in self.rules[self.cur_state].keys():
            if check_event(state_event):
                next_state = self.rules[self.cur_state][check_event]
                self.cur_state.exit(state_event)
                next_state.enter(state_event)

                print(f'{self.cur_state.__class__.__name__}'
                      f' ======{event_to_string(state_event)}======> '
                      f'{next_state.__class__.__name__}')
                self.cur_state = next_state
                processed_event = True
                return
        if not processed_event:
            print('Refused Event:', self.cur_state.__class__.__name__, 'Input : ', event_to_string(state_event))
