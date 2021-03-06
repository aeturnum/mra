import traceback

from mra.actions.action import EarlyExit
from mra.display.display_layer import TaskProgressTracker
from mra.durable_state import DurableState
from mra.helpers.util import is_instance
from mra.display.meta import TaskMeta

class TaskHandle(object):
    def __init__(self, task):
        self._task = task

    def set_title(self, title: str):
        self._task.meta.title = title
        if self._task.tracker:
            self._task.tracker.refresh()


class Task(DurableState):
    PATH = "Task"

    def __init__(self, *actions, tracker: TaskProgressTracker = None, title=None):
        super().__init__(reporter=True)
        self.registry = {}
        self.actions = list(actions)
        self.completed = []
        self.result = None
        self.meta = TaskMeta()
        if title is not None:
            self.meta.title = title

        if tracker is not None:
            tracker.register_task(self)
            self.tracker = tracker

    @property
    def current(self):
        if len(self.actions) > 0:
            return self.actions[0]
        return None

    @property
    def next(self):
        if len(self.actions) > 1:
            return self.actions[1]
        return None

    @property
    def done(self):
        return not self.meta.still_running

    def __len__(self):
        return len(self.actions)

    def label(self, title):
        self.meta.title = title

    async def setup(self):
        self.log_spew("Running setup")
        await self.tracker.start_setup()
        # todo: create tooling around browsing and understanding history
        await self.update({
           'done': [],
           'actions': [a.durable_id for a in self.actions]
        })
        self.log_spew("Setting up actions")
        for a in self.actions:
            # start managing the loggers of the actions
            self._adopt(a)
            await a.setup(self.registry)

        self.result = None
        await self.tracker.finish_setup()
        self.log_spew("Setup finished")

    async def cleanup(self):
        self.log_spew("Running cleanup")
        await self.tracker.start_cleanup()
        for a in self.actions:
            await a.cleanup()

        for a in self.completed:
            await a.cleanup()

        await self.tracker.finish_cleanup()
        self.log_spew("Cleanup finished")

    async def advance(self) -> None:
        # execute current action
        self.log_spew(f'advance(): {self.current}')
        await self.tracker.start_action()
        await self.current.execute(TaskHandle(self), self.result)
        self.log_spew(f'advance(): {self.current} executed')
        # get result
        self.result = self.current.result
        self.log_debug(f'advance(): {self.current} -> {self.result}')
        # update meta fields
        self.meta.last_action = self.current
        self.meta.exception = self.current.exception
        self.meta.trace = self.current.trace

        # make sure action does any cleanup
        await self.current.is_done()
        self.log_spew(f'advance(): {self.current} is done')
        # move to done categories
        self.completed.append(self.actions.pop(0))
        self['done'].append(self['actions'].pop(0))

        # check if we need to perform more actions
        if self.meta.exception is not None:
            self.log_system(f'advance(): exception was raised: {type(self.meta.exception)}')
            # all exceptions mean we're done
            self.meta.still_running = False
            # assume this means it's failed
            self.meta.completed = False
            if is_instance(self.meta.exception, EarlyExit):
                # if it's an early exit, we need to get its values
                self.meta.completed = self.meta.exception.completed
                # return would be impossible
                self.result = self.meta.exception.result
                # blank exception, its job is done
                # todo: make this a special case for reporting
                self.meta.exception = None
                self.log_system(
                    'advance(): exception was Early Exit. Completed: {}, result:',
                    self.meta.completed,
                    self.result
                )

        await self.update(await self.read())

        if len(self.actions) is 0:
            # we're done
            self.meta.still_running = False
            self.meta.completed = True
            self.log_system("Finished")

        await self.tracker.finish_action()

    async def report(self) -> TaskMeta:
        self.meta.logs = self._lh.get_logs()
        self.meta.reports = self._lh.get_reports()

        self.tracker.submit_final_meta(self.meta)

        return self.meta

    async def run(self, registry: dict=None) -> TaskMeta:
        # note, this is why duck typing sucks.
        # If you use the 'pythonic' line if registry:
        # and registry is empty (but shared) than it won't trigger
        # because it has no keys and is considered 'falsey'
        if registry is not None:
            self.registry = registry
        try:
            await self.setup()
            while not self.done:
                await self.advance()

            await self.cleanup()
        except Exception as e:
            self.meta.completed = False
            # return would be impossible
            self.result = None
            self.meta.exception = e
        finally:
            return await self.report()


    def __str__(self):
        return f"Task[{self.current}]->{self.next}"