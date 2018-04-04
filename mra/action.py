from mra.dynamic_module import DynamicModule

class Action(DynamicModule):
  async def execute(self):
    await self.before(driver)
    await self.actions(driver)
    await self.after(driver)

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