import asyncio
import time
import os
import re
import ast
from typing import List

from mra.task import TaskMeta, Task
from mra.settings import Settings, SettingsError
from mra.util import load_json
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
                yield JobSpec(job, settings)

    def __init__(self, job_data, settings):
        # todo: put data into settings?
        super().__init__(job_data)
        self.settings = settings

    @property
    def actions(self):
        return self.get(self._actions_key, [])

    def _create_action(self, name, args):
        DynamicModuleManager.CreateClass(name, args)

    def _parse_dsl(self, dsl_str:str):
        # ClassName(arg, arg, arg)
        match = re.match(self._dsl_re, dsl_str)
        if not match:
            raise SettingsError(f'Action "{dsl_str}" incorrectly formatted.')
        # a version of eval that won't do anything algorithmic
        return self._create_action(match.group(1), ast.literal_eval(f'[{match.group(2)}]'))

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
        t = Task(*[self._parse_action(a) for a in self.actions])

