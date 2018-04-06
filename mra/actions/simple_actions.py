from mra.actions.action import Action
from mra.http_pool import HTTPPool

class Get(Action):
    PATH = "Action.Get"

    def __init__(self, url):
        super().__init__()
        self.url = url

    async def actions(self):
        with await HTTPPool().acquire() as pool:
            print(await pool.get(self.url))