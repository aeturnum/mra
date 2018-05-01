import asyncio
import time
import os
import itertools
from copy import deepcopy
from typing import List

from mra.task import TaskMeta, Task
# from mra.task_generator import (
#     TaskGenerator,
#     ArgStandin,
#     ActionStandin,
# )
from mra.settings import Settings, SettingsError
from mra.util import load_json, is_instance
from mra.dynamic_module import DynamicModuleManager

_default_directory = './'

class TimedTask(asyncio.Task):

    cputime = 0.0

    def _step(self, *args, **kwargs):
        start = time.time()
        result = super()._step(*args, **kwargs)
        self.cputime += time.time() - start
        return result

class Plan(object):
    PATH = "Plan"
    def __init__(self, *tasks, setup_task=None):
        self.tasks = list(tasks)
        self.setup = list(setup_task)
        self.registry = {}

    def run(self, print_result=True) -> List[TaskMeta]:
        loop = asyncio.get_event_loop()
        task_factory = lambda loop, coro: TimedTask(coro, loop=loop)
        loop.set_task_factory(task_factory)
        # setup queue

        if self.setup:
            loop.run_until_complete(asyncio.gather(
                *[t.run(False, registry=self.registry) for t in self.setup]
            ))
        result = loop.run_until_complete(asyncio.gather(
            *[t.run(print_result=print_result, registry=self.registry) for t in self.tasks]
        ))
        # loop.close()
        return result


# why do I always do this to myself?
# TODO: Add support for kwargs
class ArgParser(object):
    _seps = ('(', ',')

    def __init__(self, arg_str: str):
        self.args = arg_str

    def _edge_trim(self, s: str, ends:str):
        if s[0] == ends[0] and s[-1] == ends[-1]:
            s = s[1:-1]

        return s

    @staticmethod
    def _convert(arg, converter):
        if type(arg) is str:
            try:
                arg = converter(arg)
            except ValueError:
                pass
        return arg

    def _process_call(self, arg: str):
        arg = arg.strip()
        loc = arg.find('(')
        name, inner_args = arg[:loc], arg[loc:]
        try:
            cls = DynamicModuleManager.LoadClass(name)
        except SettingsError:
            # treat it as a string literal
            return self._process_arg(arg)

        sub_ap = ArgParser(inner_args)
        sub_ap = [a for a in sub_ap]
        action = cls(*sub_ap)

        return action


    def _process_arg(self, arg: str):
        arg = arg.strip()
        arg = self._convert(arg, int)
        arg = self._convert(arg, float)
        # normalize strings
        if type(arg) is str:
            # strip quotes and escapes
            arg = arg.strip('\'"\\')

        return arg

    def _next_sep(self, s: str):
        min = [None]
        distance = [(sep, s.find(sep)) for sep in self._seps]
        for d in distance:
            # not found
            if d[1] == -1:
                continue

            if min[0] is None:
                min = d
            if d[1] < min[1]:
                min = d

        return min[0]

    def _match_parens(self, s: str):
        parens = []
        for idx, c in enumerate(s):
            if c == '(':
                parens.append('(')
            if c == ')':
                if len(parens) == 0:
                    raise Exception(f"Something has gone wrong parsing {s}")
                parens.pop()
                if len(parens) == 0:
                    return idx + 1

        raise Exception(f"Unmatched parens in {s}")

    def __iter__(self):
        args = self.args.strip()  # whitespace
        args = self._edge_trim(args, '()')

        # are you ready for amateur parsing code?
        while True:
            # we don't care about white space
            args = args.strip()

            if args == '':
                # done
                break

            # can be left after parsing an object
            if args[0] == ',':
                args = args[1:]

            sep = self._next_sep(args)
            if sep == '(':
                # open paren before a comma. We need to count open / close parens
                idx = self._match_parens(args)
                arg, args = args[:idx], args[idx:]
                yield self._process_call(arg)
            elif sep == ',':
                # comma before paren. Easy case
                arg, args = args.split(',', 1)
                yield self._process_arg(arg)
            elif sep == None:
                yield self._process_arg(args)
                break
            else:
                raise Exception(f"huh?: {args}")

class JobSpec(Settings):
    _title_key = 'title'
    _actions_key = 'actions'
    _setup_key = 'setup'

    @staticmethod
    def load_directory(settings, path=None):
        if path is None:
            path = _default_directory

        for entry in os.listdir(path):
            # todo: skip settings file
            name, ext = os.path.splitext(entry)
            if '.json' in ext and name.startswith('job_'):
                # we got one
                f = open(os.path.join(path, entry))
                job = load_json(f.read())
                f.close()
                yield JobSpec(settings, job, entry)

    def __init__(self, settings, job_data, filename):
        # todo: put data into settings?
        super().__init__(job_data, filename)
        self.settings = settings
        self.generator = False

    @property
    def actions(self):
        return self.get(self._actions_key, [])

    @property
    def setup(self):
        return self.get(self._setup_key, [])

    def _process_actions(self, action_strings):
        created_actions = []
        generators = []
        positions = []

        for idx, astr in enumerate(action_strings):
            ap = ArgParser(astr)
            # should do better than this
            action = [a for a in ap]
            if len(action) > 1:
                raise SettingsError(f'Action {action} is malformed')

            action = action[0]

            if action.generator:
                # print(f'found: {action}')
                generators.append(action)
                positions.append(idx)

            created_actions.append(action)

        tasks = []
        for combo in itertools.product(*generators):
            # copy list
            actions = [deepcopy(action) for action in created_actions]
            for idx, pos in enumerate(positions):
                # pop this standin
                actions.pop(pos)
                # insert this index
                actions.insert(pos, combo[idx])

            tasks.append(Task(*actions))

        return tasks

    def create_plan(self) -> Plan:
        # {
        #     "title": "test",
        #     "actions": [
        #                < name > (arg, arg, arg),
        # // or
        # {"name": "name", args: [arg, arg, arg]}
        # ]
        # }
        # make a task
        setup = self._process_actions(self.setup)
        if len(setup) > 1:
            raise Exception("Cannot have more than one task in setup!")

        tasks = self._process_actions(self.actions)

        return Plan(*tasks, setup_task=setup)


    def __str__(self):
        return f'JobSpec[{self.path}]'
