import asyncio
from mra.durable_state import DurableState


class Action(DurableState):
    PATH = "Action"

    def __init__(self):
        super().__init__(0)

    async def setup(self):
        await super().setup()

    async def cleanup(self):
        pass

    @property
    def result(self):
        return self.get('actions', {}).get('result')

    @property
    def exception(self):
        # we do it this way because we don't want to override the default constructor and force all
        # the sub-classes to call super()
        # It's also correct, because if exception is never set, we can safely return None
        if hasattr(self, '_exception'):
            return self._exception
        return None

    @exception.setter
    def exception(self, value):
        # oldschool
        setattr(self, '_exception', value)

    async def run_segment(self, label, func):
        self._spew('run_segment({}, {})', label, func)
        loop = asyncio.get_event_loop()
        task = loop.create_task(func)
        await task

        result = task.result()
        if asyncio.coroutines.iscoroutine(result):
            self.exception = TypeError(
                f"Action returned coroutine object. Please add an await to your action's {label} function."
            )
            # cancel coro because we don't know how to deal with it
            loop.create_task(result).cancel()
            result = None

        await self.update({label:{
            'duration': task.cputime if hasattr(task, 'cputime') else 0,
            'result': result,
            # Could save the exception in the state, but I don't think they can be pickled reliably
            # 'exception': task.exception()
        }})
        if task.exception():
            self.exception = task.exception()

    async def execute(self, previous):
        segments = [
            ('before', self.before),
            ('actions', self.actions),
            ('after', self.after)
        ]

        for seg in segments:
            await self.run_segment(seg[0], seg[1](previous))
            if self.exception is not None:
                break

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
        return type(self).__name__