import random

# 행동 트리 디버깅용 들여쓰기 레벨 전역 변수
level = 0

def indent():
    """디버깅 출력 시 들여쓰기 레벨 증가"""
    global level
    level += 1

def unindent():
    """디버깅 출력 시 들여쓰기 레벨 감소"""
    global level
    level -= 1

def print_indent():
    """현재 들여쓰기 레벨만큼 공백 출력"""
    for i in range(level):
        print("    ", end='')


class BehaviorTree:
    """
    행동 트리 메인 클래스
    - 루트 노드를 관리하고 매 틱마다 트리를 실행
    """
    # 노드 실행 결과 상수
    FAIL, RUNNING, SUCCESS, UNDEF = 'FAIL', 'RUNNING', 'SUCCESS', 'UNDEF'

    def __init__(self, root_node):
        """
        행동 트리 초기화
        :param root_node: 트리의 루트 노드
        """
        self.root = root_node
        self.root.tag_condition()

    def run(self):
        """
        행동 트리 실행 (매 프레임 호출)
        루트 노드가 SUCCESS를 반환하면 트리를 리셋
        """
        self.root.run()
        if self.root.value == BehaviorTree.SUCCESS:
            self.root.reset()


class Node:
    """
    행동 트리 노드의 베이스 클래스
    """

    def add_child(self, child):
        """자식 노드 추가"""
        self.children.append(child)

    def add_children(self, *children):
        """여러 자식 노드를 한 번에 추가"""
        for child in children:
            self.children.append(child)

    @staticmethod
    def show_result(f):
        """
        데코레이터: 노드 실행 결과를 출력 (디버깅용)
        """
        def inner(self):
            result = f(self)
            # 디버깅이 필요할 때 주석 해제
            # print(f'[{self.__class__.__name__:10s}] {self.name:40s} ==> ({result})')
            return result
        return inner


class Selector(Node):
    """
    Selector 노드: 자식 노드들을 순서대로 실행하며,
    하나라도 SUCCESS 또는 RUNNING을 반환하면 즉시 해당 값을 반환
    모든 자식이 FAIL이면 FAIL 반환
    """

    def __init__(self, name, *nodes):
        """
        Selector 노드 초기화
        :param name: 노드 이름 (디버깅용)
        :param nodes: 자식 노드들
        """
        self.children = list(nodes)
        self.name = name
        self.value = BehaviorTree.UNDEF
        self.has_condition = False

    def reset(self):
        """노드와 모든 자식 노드의 상태를 초기화"""
        self.value = BehaviorTree.UNDEF
        for child in self.children:
            child.reset()

    def tag_condition(self):
        """조건 노드가 있는지 하위 트리를 탐색하여 태그"""
        for child in self.children:
            child.tag_condition()
            if child.has_condition:
                self.has_condition = True

    @Node.show_result
    def run(self):
        """
        Selector 실행: 자식 노드들을 순서대로 실행
        하나라도 SUCCESS 또는 RUNNING이면 즉시 반환
        """
        for child in self.children:
            # 실행이 필요한 노드만 실행 (UNDEF, RUNNING 상태이거나 조건 노드)
            if (child.value in (BehaviorTree.UNDEF, BehaviorTree.RUNNING)) or child.has_condition:
                result = child.run()
                if result in (BehaviorTree.RUNNING, BehaviorTree.SUCCESS):
                    self.value = result
                    return self.value

        # 모든 자식이 FAIL이면 FAIL 반환
        self.value = BehaviorTree.FAIL
        return self.value


class RandomSelector(Node):
    """
    RandomSelector 노드: Selector와 동일하지만,
    자식 노드들을 랜덤한 순서로 실행
    """

    def __init__(self, name, *nodes):
        """
        RandomSelector 노드 초기화
        :param name: 노드 이름 (디버깅용)
        :param nodes: 자식 노드들
        """
        self.children = list(nodes)
        self.name = name
        self.value = BehaviorTree.UNDEF
        self.has_condition = False

    def reset(self):
        """노드와 모든 자식 노드의 상태를 초기화"""
        self.value = BehaviorTree.UNDEF
        for child in self.children:
            child.reset()

    def tag_condition(self):
        """조건 노드가 있는지 하위 트리를 탐색하여 태그"""
        for child in self.children:
            child.tag_condition()
            if child.has_condition:
                self.has_condition = True

    @Node.show_result
    def run(self):
        """
        RandomSelector 실행: 자식 노드들을 랜덤한 순서로 실행
        하나라도 SUCCESS 또는 RUNNING이면 즉시 반환
        """
        # 원본 children 순서는 보존하고 섞인 복사본으로 순회
        children = self.children[:]
        random.shuffle(children)

        for child in children:
            # 실행이 필요한 노드만 실행 (UNDEF, RUNNING 상태이거나 조건 노드)
            if (child.value in (BehaviorTree.UNDEF, BehaviorTree.RUNNING)) or child.has_condition:
                result = child.run()
                # 안전성: child.run이 None을 반환하면 FAIL로 처리
                if result is None:
                    result = BehaviorTree.FAIL

                if result in (BehaviorTree.RUNNING, BehaviorTree.SUCCESS):
                    self.value = result
                    return self.value

        # 모든 자식이 FAIL이면 FAIL 반환
        self.value = BehaviorTree.FAIL
        return self.value


class Sequence(Node):
    """
    Sequence 노드: 자식 노드들을 순서대로 실행하며,
    모두 SUCCESS를 반환해야 SUCCESS 반환
    하나라도 FAIL 또는 RUNNING을 반환하면 즉시 해당 값을 반환
    """

    def __init__(self, name, *nodes):
        """
        Sequence 노드 초기화
        :param name: 노드 이름 (디버깅용)
        :param nodes: 자식 노드들
        """
        self.children = list(nodes)
        self.name = name
        self.value = BehaviorTree.UNDEF
        self.has_condition = False

    def reset(self):
        """노드와 모든 자식 노드의 상태를 초기화"""
        self.value = BehaviorTree.UNDEF
        for child in self.children:
            child.reset()

    def tag_condition(self):
        """조건 노드가 있는지 하위 트리를 탐색하여 태그"""
        for child in self.children:
            child.tag_condition()
            if child.has_condition:
                self.has_condition = True

    @Node.show_result
    def run(self):
        """
        Sequence 실행: 자식 노드들을 순서대로 실행
        하나라도 FAIL 또는 RUNNING이면 즉시 반환
        """
        for child in self.children:
            # 실행이 필요한 노드만 실행 (UNDEF, RUNNING 상태이거나 조건 노드)
            if (child.value in (BehaviorTree.UNDEF, BehaviorTree.RUNNING)) or child.has_condition:
                result = child.run()
                if result in (BehaviorTree.RUNNING, BehaviorTree.FAIL):
                    self.value = result
                    return self.value

        # 모든 자식이 SUCCESS이면 SUCCESS 반환
        self.value = BehaviorTree.SUCCESS
        return self.value


class Action(Node):
    """
    Action 노드 (Leaf 노드): 실제 행동을 수행하는 노드
    주어진 함수를 실행하고 그 결과를 반환
    """

    def __init__(self, name, func, *args):
        """
        Action 노드 초기화
        :param name: 노드 이름 (디버깅용)
        :param func: 실행할 함수
        :param args: 함수에 전달할 인자들
        """
        self.name = name
        self.func = func
        self.args = list(args) if args else []
        self.value = BehaviorTree.UNDEF
        self.has_condition = False

    def tag_condition(self):
        """Action 노드는 조건 노드가 아님"""
        self.has_condition = False

    def reset(self):
        """노드 상태 초기화"""
        self.value = BehaviorTree.UNDEF

    def add_child(self, child):
        """Leaf 노드에는 자식을 추가할 수 없음"""
        print("ERROR: you cannot add child node to leaf node")

    def add_children(self, *children):
        """Leaf 노드에는 자식을 추가할 수 없음"""
        print("ERROR: you cannot add children node to leaf node")

    @Node.show_result
    def run(self):
        """
        Action 실행: 지정된 함수를 호출하고 결과 반환
        """
        self.value = self.func(*self.args)
        return self.value


class Condition(Node):
    """
    Condition 노드 (Leaf 노드): 조건을 검사하는 노드
    SUCCESS 또는 FAIL만 반환 가능 (RUNNING은 불가)
    """

    def __init__(self, name, func, *args):
        """
        Condition 노드 초기화
        :param name: 노드 이름 (디버깅용)
        :param func: 조건을 검사할 함수
        :param args: 함수에 전달할 인자들
        """
        self.name = name
        self.func = func
        self.args = list(args) if args else []
        self.value = BehaviorTree.UNDEF
        self.has_condition = False

    def reset(self):
        """노드 상태 초기화"""
        self.value = BehaviorTree.UNDEF

    def tag_condition(self):
        """이 노드가 조건 노드임을 표시"""
        self.has_condition = True

    def add_child(self, child):
        """Leaf 노드에는 자식을 추가할 수 없음"""
        print("ERROR: you cannot add child node to leaf node")

    def add_children(self, *children):
        """Leaf 노드에는 자식을 추가할 수 없음"""
        print("ERROR: you cannot add children node to leaf node")

    @Node.show_result
    def run(self):
        """
        Condition 실행: 조건을 검사하고 SUCCESS 또는 FAIL 반환
        RUNNING을 반환하면 에러 발생
        """
        self.value = self.func(*self.args)
        if self.value == BehaviorTree.RUNNING:
            print("ERROR: condition node cannot return RUNNING")
            raise ValueError("Condition node returned RUNNING")

        return self.value