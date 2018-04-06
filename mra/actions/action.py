from mra.dynamic_module import DynamicModule


class Action(DynamicModule):
    PATH = "Action"

    async def setup(self):
        pass

    async def cleanup(self):
        pass

    async def execute(self):
        await self.before()
        await self.actions()
        await self.after()

    async def is_next(self):
        pass

    async def before(self):
        pass

    async def actions(self):
        pass

    async def after(self):
        pass

    async def ready(self):
        return True

    async def is_done(self):
        pass

    def __str__(self):
        return "Action"