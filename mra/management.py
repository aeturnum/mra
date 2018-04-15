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
    def __init__(self, *tasks):
        self.tasks = list(tasks)

    def run(self, print=True) -> List[TaskMeta]:
        loop = asyncio.get_event_loop()
        task_factory = lambda loop, coro: TimedTask(coro, loop=loop)
        loop.set_task_factory(task_factory)
        # setup queue


        result = loop.run_until_complete(asyncio.gather(
            *[t.run(print=print) for t in self.tasks]
        ))
        # loop.close()
        return result


class JobSpec(Settings):
    _title_key = 'title'
    _actions_key = 'actions'

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
            name, ext = os.path.split(entry)
            if '.json' in ext and name.startswith('job_'):
                # we got one
                job = load_json(open(os.path.join(path, entry)).read())
                yield JobSpec(settings, job, entry)

    def __init__(self, settings, job_data, filename):
        # todo: put data into settings?
        super().__init__(job_data, filename)
        self.settings = settings
        self.generator = False

    @property
    def actions(self):
        return self.get(self._actions_key, [])

    def _create_arg_from_str(self, arg):
        # ClassName(arg, arg, arg)
        match = re.match(self._dsl_re, arg)
        if not match:
            return arg
        # a version of eval that won't do anything algorithmic
        try:
            return self._create_action(match.group(1), ast.literal_eval(f'[{match.group(2)}]'))
        except:
            self._warn('Tried to parse arg "{}" as a python object, but failed.', arg)
            # if this breaks, try the other way
            return arg

    def _create_action(self, name, args):
        converted_args = []
        # check for special arguments
        for arg in args:
            if type(arg) is str:
                converted_args.append(self._create_arg_from_str(arg))
            elif type(arg) is dict:
                if 'name' in arg and 'args' in arg and len(arg.keys()) == 2:
                    # this could go on forever, so we'll just cut it here
                    converted_args.append(self._create_action(
                        arg['name'],
                        arg['args']
                    ))
            else:
                converted_args.append(arg)


        action = DynamicModuleManager.CreateClass(name, converted_args)
        if is_instance(action, self._special_classes):
            self.generator = True

        return action

    def _parse_dsl(self, dsl_str:str):
        # ClassName(arg, arg, arg)
        loc = dsl_str.find('(')
        if loc < 0:
            raise SettingsError(f'Action "{dsl_str}" incorrectly formatted.')

        name, unstripped_args = dsl_str[:loc], dsl_str[loc:]
        args = unstripped_args.strip() # whitespace
        args = args.strip('(')
        args = args.strip(')')

        if len(args) == len(unstripped_args):
            raise SettingsError(f'Action "{dsl_str}" incorrectly formatted.')

        # a version of eval that won't do anything algorithmic
        return self._create_action(name, ast.literal_eval(f'[{args}]'))

    def _parse_action(self, action):
        if type(action) is str:
            return self._parse_dsl(action)

        if type(action) is dict:
            if 'name' not in action or 'args' not in action:
                raise SettingsError(f'Action "{action}" missing "name" or "args" key.')
            return self._create_action(action['name'], action['args'])

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
        # todo: don't immediately create task, instead see if we need to make a task generator wrapper
        action_list = [self._parse_action(a) for a in self.actions]
        if self.generator:
            task = TaskGenerator(*action_list)
            return Plan(*[t for t in task])
        else:
            return Plan(Task(*action_list))


    def __str__(self):
        return f'JobSpec[{self.path}]'
