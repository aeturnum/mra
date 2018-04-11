from mra.dynamic_module import DynamicModule
from mra.durable_state import DurableState

class Task(DurableState):
    PATH = "Task"

    def __init__(self, *actions):
        super().__init__()
        self.actions = list(actions)
        self.completed = []
        self.result = None

    async def setup(self):
        await self.update({
           'done': [],
           'actions': [a.durable_id for a in self.actions]
        })
        for a in self.actions:
            await a.setup()
        self.result = None
        await self.current.is_next()

    async def cleanup(self):
        for a in self.actions:
            await a.cleanup()

        for a in self.completed:
            await a.cleanup()

    @property
    def current(self):
        return self.actions[0]

    @property
    def next(self):
        if len(self.actions) > 1:
            return self.actions[1]
        return None

    @property
    def done(self):
        return len(self.actions) == 0

    async def advance(self):
        await self.current.execute(self.result)
        self.result = self.current.result

        await self.current.is_done()

        if self.next:
            await self.next.is_next()

        self.completed.append(self.actions.pop(0))
        self['done'].append(self['actions'].pop(0))
        self.update(await self.read())

    async def run(self):
        await self.setup()
        while not self.done:
            await self.advance()

        await self.cleanup()
        return self.result

    def __str__(self):
        return f"Task:\n\tcurrent: {self.current}\n\tnext: {self.next}"