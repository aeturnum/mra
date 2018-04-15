from typing import List
import itertools
from mra.util import is_instance
from mra.task import Task
from mra.dynamic_module import DynamicModule, DynamicModuleManager

# TODO: convert this entire file to use iterators instead of list construction. Otherwise it will get bac

class ArgStandin(DynamicModule):
    PATH = 'GeneratedArg'

    def generate(self):
        return None


class ArgFromList(ArgStandin):
    PATH = 'ArgFromList'
    def __init__(self, lst:list):
        super().__init__()
        self.list = lst
        self._indx = 0

    def __iter__(self):
        for v in self.list:
            yield v

    def __str__(self):
        return f'ArgFromList({len(self.list)}items)'

class ActionStandin(DynamicModule):
    PATH = 'GeneratedTask'
    def __init__(self, ActionClass, *args):
        super().__init__()
        # we're loading from settings
        if type(ActionClass) is str:
            ActionClass = DynamicModuleManager.LoadClass(ActionClass)
        self.action = ActionClass
        self.args = args

    def __iter__(self):
        generators = []
        positions = []
        for idx, arg in enumerate(self.args):
            if is_instance(arg, ArgStandin):
                # get to generating!
                generators.append(arg)
                positions.append(idx)

        for combo in itertools.product(*generators):
            # copy list
            args = list(self.args)
            for idx, pos in enumerate(positions):
                # pop this standin
                args.pop(pos)
                # insert this index
                args.insert(pos, combo[idx])
            yield self.action(*args)


# Behavaior for these classes is enforced in TaskGenerator
class MultipleTasks(ActionStandin):
    PATH = 'MultipleTasks'
    def __str__(self):
        return f'MultipleTasks({self.action}, {self.args})'

class MultipleActions(ActionStandin):
    PATH = 'MultipleActions'
    def __str__(self):
        return f'MultipleActions({self.action}, {self.args})'


class TaskGenerator(DynamicModule):
    PATH = 'Generator'
    def __init__(self, *actions):
        super().__init__()
        self.actions = list(actions)

    def _replace_multi_actions(self):
        action_gens = []
        for idx, action in enumerate(self.actions):
            if is_instance(action, MultipleActions):
                action_gens.append((idx, action))

        for (idx, gen) in action_gens:
            actions = [v for v in gen]
            # insert into location they will be in list
            self.actions[idx:idx] = actions
            # pop standin
            self.actions.pop(idx + len(actions))

    def __iter__(self) -> List[Task]:
        # first pass, find MultipleAction standins
        self._replace_multi_actions()
        generators = []
        positions = []
        for idx, action in enumerate(self.actions):
            if is_instance(action, ActionStandin):
                generators.append(action)
                positions.append(idx)

        for combo in itertools.product(*generators):
            # copy list
            actions = list(self.actions)
            for idx, pos in enumerate(positions):
                # pop this standin
                actions.pop(pos)
                # insert this index
                actions.insert(pos, combo[idx])

            yield Task(*actions)


