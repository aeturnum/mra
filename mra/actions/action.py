import asyncio
import traceback

from mra.durable_state import DurableState

class TestException(Exception):
    pass


class EarlyExit(Exception):
    def __init__(self, result:any=False, completed:bool=False):
        # by default, we're going to consider this a success
        super().__init__()
        self.result = result
        self.completed = completed

class Action(DurableState):
    PATH = "Action"

    def __init__(self):
        super().__init__(0)
        self.registry = {}

    async def setup(self, registry=None):
        await super().setup()
        if registry is not None:
            self.registry = registry

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

    @property
    def trace(self):
        # we do it this way because we don't want to override the default constructor and force all
        # the sub-classes to call super()
        # It's also correct, because if exception is never set, we can safely return None
        if hasattr(self, '_trace'):
            return self._trace
        return None

    @trace.setter
    def trace(self, value):
        setattr(self, '_trace', value)

    @exception.setter
    def exception(self, value):
        # oldschool
        setattr(self, '_exception', value)


    async def run_segment(self, label, func):
        self._spew('run_segment({}, {})', label, func)
        loop = asyncio.get_event_loop()

        task = loop.create_task(func)
        result = None
        exception = None
        trace = ''
        # await will raise task exceptions immediately
        try:
            result = await task
        except Exception as e:
            trace = traceback.format_exc()
            exception = e

        # result = task.result()
        if asyncio.coroutines.iscoroutine(result):
            self.exception = TypeError(
                f"Action returned coroutine object. Please add an await to your action's {label} function."
            )
            # cancel coro because we don't know how to deal with it
            loop.create_task(result).cancel()
            result = None
        state_update = {label: {
            'duration': task.cputime if hasattr(task, 'cputime') else 0,
            'result': result,
            'trace': trace,
            # Could save the exception in the state, but I don't think they can be pickled reliably
            # 'exception': exception
        }}
        self._system(state_update)
        await self.update(state_update)
        if exception:
            self.exception = exception
            self.trace = trace

    async def execute(self, previous):
        segments = [
            ('before', self.before),
            ('actions', self.actions),
            ('after', self.after)
        ]

        for seg in segments:
            await self.run_segment(seg[0], seg[1](previous))
            if self.exception is not None:
                self._error(f"Segment {seg[0]} raised an exception: {self.exception}")
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