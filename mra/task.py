from mra.dynamic_module import DynamicModule

class Task(DynamicModule):
    PATH = "Task"

    def __init__(self, *actions):
        self.actions = list(actions)

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
        await self.current.execute()
        old_action = self.actions.pop(0)

        await old_action.is_done()

        await self.current.is_next()

    async def run(self):
        while not self.done():
            await self.advance()

        return True

    def __str__(self):
        return f"Task:\n\tcurrent: {self.current}\n\tnext: {self.next}"