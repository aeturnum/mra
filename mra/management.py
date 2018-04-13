import asyncio
import time
from typing import List

from mra.task import TaskMeta

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

