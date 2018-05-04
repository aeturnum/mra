from mra.actions.action import Action, TestException
from mra.helpers.util import load_json
from mra.http_pool import HTTPPool
from mra.task import TaskHandle


class SetTitle(Action):
    PREFIX = 'Action.Meta'
    PATH = "Action.Meta.SetTitle"

    def _create(self, title):
        self.title = title

    async def actions(self, task_handle: TaskHandle, previous):
        task_handle.set_title(self.title)

        return self.title

class Get(Action):
    PREFIX = 'Action.Simple'
    PATH = "Action.Simple.Get"

    def _create(self, url):
        self.url = url

    async def actions(self, task_handle, previous):
        with await HTTPPool().acquire() as pool:
            result = await pool.get(self.url)
            self.log_report('Sent a GET request to {} and received {}', self.url, result.content_type)
            if result.content_type == 'application/json':
                return await result.json()

            return await result.text()

class DictCheck(Action):
    PREFIX = 'Action.Simple.Checks'
    PATH = "Action.Simple.Checks.Dictionary"

    def _create(self, match_dict, partial=True):
        self.match_dict = match_dict
        self.partial = partial

    async def actions(self, task_handle, previous: any) -> any:
        if not isinstance(previous, dict):
            raise TestException(f'Previous product a {type(previous)} not a dict!')

        for key, item in self.match_dict.items():
            if key not in previous:
                raise TestException(f'key "{key}" not in {previous}!')

            if self.match_dict[key] != previous[key]:
                raise TestException(f'Value in key "{key}" does not match! {self.match_dict[key]} != {previous[key]}')

        # must be exact match
        if not self.partial:
            for key in previous.keys():
                if key not in self.match_dict:
                    raise TestException(f'Found unexpected key "{key}" in {previous}')

        self.log_report('Previous result as expected')
        return previous

class JsonCheck(DictCheck):
    PREFIX = 'Action.Simple.Checks'
    PATH = "Action.Simple.Checks.Json"

    def _create(self, match_dict: str or dict, partial=True):
        if type(match_dict) is str:
            match_dict = load_json(match_dict)

        super().__init__(match_dict, partial)


    async def actions(self, task_handle, previous: any) -> any:
        if type(previous) is str:
            previous = load_json(previous)

        if type(previous) is dict:
            return await super().actions(previous)
        else:
            raise TypeError(f'JsonCheck expects JSON, got {type(previous)}')

