import asyncio
import traceback
import itertools

from mra.dynamic_module import DynamicModule
from mra.durable_state import DurableState
from mra.logger import Logger
from mra.util import is_instance

class ArgStandin(DynamicModule):
    PATH = 'GeneratedArg'

    def generate(self):
        return None


class TestException(Exception):
    pass


class EarlyExit(Exception):
    def __init__(self, result: any=False, completed: bool=False):
        # by default, we're going to consider this a success
        super().__init__()
        self.result = result
        self.completed = completed

class GeneratorArg(object):
    _arg = 'arg'
    _kwarg = 'kwarg'


    class GenResult(object):
        __slots__ = ['generator', 'args', 'kwargs', 'gens']
        def __init__(self, generator, args, kwargs, gens):
            self.generator = generator
            self.args = args
            self.kwargs = kwargs
            self. gens = gens


    @classmethod
    def from_args_kwargs(cls, *args, **kwargs):
        result = cls.GenResult(False, list(args), dict(kwargs), [])
        for idx, arg in enumerate(args):
            if is_instance(arg, ArgStandin):
                result.gens.append(GeneratorArg(arg, arg_pos=idx))
                result.generator = True

        for key, arg in kwargs.items():
            if is_instance(arg, ArgStandin):
                result.gens.append(GeneratorArg(arg, kwarg_key=key))
                result.generator = True

        return result

    @classmethod
    def arg_loop(cls, info: GenResult):
        # lul
        generators = [gen.gen for gen in info.gens]

        for combo in itertools.product(*generators):
            args = list(info.args)
            kwargs = list(info.kwargs)
            for idx, value in enumerate(combo):
                # position info
                pos_info = info.gens[idx]

                if pos_info.type == cls._arg:
                    # pop this standin
                    args.pop(pos_info.pos)
                    # insert this index
                    args.insert(pos_info.pos, value)
                if pos_info.type == cls._kwarg:
                    # in this case .pos stores the key
                    kwargs[pos_info.pos] = value

            yield args, kwargs

    def __init__(self, gen, arg_pos=None, kwarg_key=None):
        if arg_pos is None and kwarg_key is None or \
            arg_pos is not None and kwarg_key is not None:
            raise ValueError("GeneratorArg must have either an arg position or kwarg_key, but not both.")

        self.gen = gen
        if arg_pos is not None:
            self.type = self._arg
            self.pos = arg_pos
        if kwarg_key is not None:
            self.type = self._kwarg
            self.pos = kwarg_key



class Action(DurableState):
    PATH = "Action"

    def __init__(self, *args, **kwargs):
        super().__init__(0)
        self._info = GeneratorArg.from_args_kwargs(*args, **kwargs)

        self.registry = {}
        if not self.generator:
            self._create(*args, **kwargs)

    @property
    def generator(self):
        return self._info.generator

    def _create(self, *args, **kwargs):
        pass

    def __iter__(self):
        for args, kwargs in GeneratorArg.arg_loop(self._info):
            # will NOT contain generator classes
            yield self.__class__(*args, *kwargs)

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
        self.log_spew('run_segment({}, {})', label, func)
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

        if is_instance(result, Logger):
            self._adopt(result)

        state_update = {label: {
            'duration': task.cputime if hasattr(task, 'cputime') else 0,
            'result': result,
            'trace': trace,
            # Could save the exception in the state, but I don't think they can be pickled reliably
            # 'exception': exception
        }}
        self.log_system(state_update)
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
                self.log_error(f"Segment {seg[0]} raised an exception: {self.exception}")
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