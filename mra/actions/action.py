import asyncio
from mra.durable_state import DurableState


class Action(DurableState):
    PATH = "Action"

    async def setup(self):
        await super().setup()

    async def cleanup(self):
        pass

    @property
    def result(self):
        return self.get('actions', {}).get('result')

    async def run_segment(self, label, func):
        loop = asyncio.get_event_loop()
        task = loop.create_task(func)
        await task
        await self.update({label:{
            'duration': task.cputime if hasattr(task, 'cputime') else 0,
            'result': task.result(),
            'exception': task.exception()
        }})

    async def execute(self, previous):
        # todo figure out what to do with exceptions
        await self.run_segment('before', self.before(previous))
        await self.run_segment('actions', self.actions(previous))
        await self.run_segment('after', self.after(previous))

    async def before(self, previous):
        pass

    async def actions(self, previous):
        pass

    async def after(self, previous):
        pass

    async def ready(self):
        return True

    async def is_done(self):
        pass

    def __str__(self):
        return "Action"