import asyncio
import time
import os
import re
import ast
from typing import List

from mra.task import TaskMeta, Task
from mra.task_generator import (
    TaskGenerator,
    ArgStandin,
    ActionStandin,
)
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
        print(f"plan({tasks}, {setup_task})")
        self.tasks = list(tasks)
        self.setup = list(setup_task)
        print(f"plan({tasks}, {setup_task}) done")

    def run(self, print=True) -> List[TaskMeta]:
        loop = asyncio.get_event_loop()
        task_factory = lambda loop, coro: TimedTask(coro, loop=loop)
        loop.set_task_factory(task_factory)
        # setup queue

        if self.setup:
            loop.run_until_complete(asyncio.gather(
                *[t.run(False) for t in self.setup]
            ))
        result = loop.run_until_complete(asyncio.gather(
            *[t.run(print=print) for t in self.tasks]
        ))
        # loop.close()
        return result


# why do I always do this to myself?
class ArgParser(object):
    _seps = ('(', ',')
    _special_classes = (
        ArgStandin,
        ActionStandin,
    )

    def __init__(self, arg_str: str):
        self.args = arg_str
        self.contains_generator = False

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
        action = cls(*[a for a in sub_ap])
        if is_instance(action, self._special_classes) or sub_ap.contains_generator:
            self.contains_generator = True

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

    _dsl_re = '([^\()]+)\(([^\)]*)\)'

    _special_classes = (
        ArgStandin,
        ActionStandin,
    )

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
        print('create_plan')
        setup = None
        if self.setup:
            setup = []
            generator = False
            for action in self.setup:
                ap = ArgParser(action)
                # todo: god help me, fix this
                action = [a for a in ap]
                if len(action) > 1:
                    raise SettingsError(f'Action {action} is malformed')
                setup.append(action[0])
                generator = generator or ap.contains_generator
            if generator:
                setup = TaskGenerator(*setup)
                setup = [t for t in setup]
            else:
                setup = Task(*setup)

        print('setup done')
        generator = False
        action_list = []
        for action in self.actions:
            ap = ArgParser(action)
            # todo: god help me, fix this
            action = [a for a in ap]
            if len(action) > 1:
                raise SettingsError(f'Action {action} is malformed')
            action_list.append(action[0])
            generator = generator or ap.contains_generator

        if generator:
            task = TaskGenerator(*action_list)
            print('generating tasks')
            return Plan(*[t for t in task], setup_task=setup)
        else:
            return Plan(Task(*action_list), setup_task=setup)


    def __str__(self):
        return f'JobSpec[{self.path}]'
