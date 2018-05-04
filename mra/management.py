import asyncio
import itertools
import os
import time
from copy import deepcopy
from typing import List

from mra.display.display_layer import DisplayLayer
from mra.dynamic_module import DynamicModuleManager
from mra.helpers.logger import Logger
from mra.helpers.parser import ArgParser
from mra.helpers.util import load_json_file
from mra.settings import Settings, SettingsError
from mra.task import TaskMeta, Task

_default_directory = './'

class TimedTask(asyncio.Task):

    cputime = 0.0

    def _step(self, *args, **kwargs):
        start = time.time()
        result = super()._step(*args, **kwargs)
        self.cputime += time.time() - start
        return result


class MRAManager(Logger):
    def __init__(self, args):
        super().__init__()
        self.args = args
        self.settings = Settings.load_from_file()
        self.loop = asyncio.get_event_loop()
        self.display_layer = DisplayLayer(self.settings)
        self._setup()

    @staticmethod
    def _task_factory(loop, coro):
        return TimedTask(coro, loop=loop)

    def _setup(self):
        self.loop.set_task_factory(self._task_factory)

    def run(self):

        DynamicModuleManager.gather(self.settings)
        js = JobSpec.load_directory(self.settings, self.display_layer, os.getcwd())

        jobs = [job for job in js]

        plans = [job.create_plan() for job in jobs]

        self.loop.run_until_complete(asyncio.gather(
            *[plan.run(self.display_layer) for plan in plans]
        ))

        self.display_layer.print_reports()

class Plan(object):
    PATH = "Plan"
    def __init__(self, *tasks, setup_task=None):
        self.tasks = list(tasks)
        self.setup = []
        if setup_task is not None:
            self.setup = list(setup_task)
        self.registry = {}

    async def run(self, display_layer: DisplayLayer) -> List[TaskMeta]:
        for t in self.setup:
            await t.run(registry=self.registry)

        result =  await asyncio.gather(
            *[t.run(registry=self.registry) for t in self.tasks]
        )
        return result


class JobSpec(Settings):
    _title_key = 'title'
    _actions_key = 'actions'
    _setup_key = 'setup'

    @staticmethod
    def load_directory(settings, display_layer, path=None):
        if path is None:
            path = _default_directory

        for entry in os.listdir(path):
            # todo: skip settings file
            name, ext = os.path.splitext(entry)
            if '.json' in ext and name.startswith('job_'):
                job = load_json_file(entry)
                if job is not None:
                    yield JobSpec(settings, display_layer, job, entry)

    def __init__(self, settings, display_layer, job_data, filename):
        # todo: put data into settings?
        super().__init__(job_data, filename)
        self.settings = settings
        self.display_layer = display_layer
        self.generator = False

    @property
    def actions(self):
        return self.get(self._actions_key, [])

    @property
    def setup(self):
        return self.get(self._setup_key, [])

    def _process_actions(self, action_strings: list, setup: bool=False):
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

            tasks.append(
                Task(*actions, tracker=self.display_layer.task_tracker(setup))
            )

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
        setup = self._process_actions(self.setup, True)
        if len(setup) > 1:
            raise Exception("Cannot have more than one task in setup!")

        tasks = self._process_actions(self.actions, False)

        return Plan(*tasks, setup_task=setup)


    def __str__(self):
        return f'JobSpec[{self.path}]'
