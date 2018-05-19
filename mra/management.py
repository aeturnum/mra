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
from mra.helpers.util import load_json_file, JobError
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
        super().__init__(reporter=True)
        self.args = args
        self.settings = Settings.load_from_file()
        self.loop = asyncio.get_event_loop()
        self.display_layer = DisplayLayer(self.settings)
        self.dmm = DynamicModuleManager()

    @staticmethod
    def _task_factory(loop, coro):
        return TimedTask(coro, loop=loop)

    def _setup(self):
        self.loop.set_task_factory(self._task_factory)
        self._adopt(self.settings)
        self._adopt(self.display_layer)
        self._adopt(self.dmm)

    def run(self):
        setup_failed = False
        exception = None
        try:
            self._setup()
            self.log_spew("Setup Done")
            self.log_spew("Beginning run!")

            self.dmm.gather(self.settings)
            self.log_spew("Finished gathering modules")

            js = JobSpec.load_directory(self.settings, self.display_layer, os.getcwd())
            self.log_spew("Jobs loaded")

            # adopt all the jobs
            jobs = [self._adopt(job) for job in js]
            self.log_spew("Jobs created")

            plans = [self._adopt(job.create_plan()) for job in jobs]
            self.log_spew("Running jobs")
        except Exception as e:
            setup_failed = True
            exception = e

        if not setup_failed:
            self.loop.run_until_complete(asyncio.gather(
                *[plan.run(self.display_layer) for plan in plans]
            ))
            self.log_spew("Jobs finished, printing reports")

            self.display_layer.print_reports()
            self.log_spew("Exiting")

        if exception:
            self.display_layer.report_error(
                exception,
                self._lh.get_logs()
            )

    def __str__(self):
        return "MRAManager"

class Plan(Logger):
    PATH = "Plan"
    def __init__(self, *tasks, setup_task=None):
        super().__init__()
        self.tasks = list(tasks)
        self.setup = []
        if setup_task is not None:
            self.setup = list(setup_task)
        self.registry = {}

    async def run(self, display_layer: DisplayLayer) -> List[TaskMeta]:
        for t in self.setup:
            self.log_spew("Running setup")
            await t.run(registry=self.registry)

        self.log_spew("Running tasks")
        result =  await asyncio.gather(
            *[t.run(registry=self.registry) for t in self.tasks]
        )
        self.log_spew("Tasks finished, returning results")
        return result

    def __str__(self):
        return f"Plan"


# TODO: Re-evaluate if it still makes sense for this to inherit from settings
class JobSpec(Settings):
    _title_key = 'title'
    _actions_key = 'actions'
    _setup_key = 'setup'

    @staticmethod
    def load_directory(settings, display_layer, path=None):
        # Todo: add logging code here
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
            self.log_spew(f"Converting '{astr}' into object.")
            try:
                ap = ArgParser(astr)
                self._adopt(ap)
                # should do better than this
                action = [a for a in ap]
                if len(action) > 1:
                    raise SettingsError(f'Action {action}({type(action)}) is malformed.')

                action = action[0]
                # logger chain
                self._adopt(action)

                if not hasattr(action, 'generator'):
                    raise Settings(f'Action {action}({type(action)}) was not transformed properly.')

                if action.generator:
                    self.log_system(f'Action {action} is a generator and will need processing.')
                    generators.append(action)
                    positions.append(idx)

                created_actions.append(action)
            except Exception as e:
                raise JobError(
                    f'Encountered Error parsing "{astr}" into an action',
                    e
                )
        self.log_spew("Created actions: {}", created_actions)
        tasks = []
        for combo in itertools.product(*generators):
            self.log_spew(f"Creating new task with this combination of generated actions: {combo}")
            try:
                # copy list
                actions = [deepcopy(action) for action in created_actions]
                for idx, pos in enumerate(positions):
                    # pop this standin
                    standin = actions.pop(pos)
                    # insert this index
                    actions.insert(pos, combo[idx])
                    self.log_spew(f"Replacing {standin} with {combo[idx]}")

                task = Task(*actions, tracker=self.display_layer.task_tracker(setup))
                self.log_system(f"Task created: {task}")
                tasks.append(task)
            except Exception as e:
                raise JobError(
                    f'Could not create Task with action combo: {combo}',
                    e
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
        self.log_spew("Creating Plan")
        setup = self._process_actions(self.setup, True)
        self.log_spew("Setup loaded")
        if len(setup) > 1:
            raise Exception("Cannot have more than one task in setup!")

        tasks = self._process_actions(self.actions, False)
        self.log_spew("Main task loaded")

        return Plan(*tasks, setup_task=setup)


    def __str__(self):
        return f'JobSpec[{self.path}]'
