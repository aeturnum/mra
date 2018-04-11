from mra.actions.action import Action
from mra.http_pool import HTTPPool

class Get(Action):
    PATH = "Action.Get"

    def __init__(self, url):
        super().__init__()
        self.url = url

    async def actions(self, previous):
        with await HTTPPool().acquire() as pool:
            result = await pool.get(self.url)
            if result.content_type == 'application/json':
                return await result.json()

            return await result.text()
