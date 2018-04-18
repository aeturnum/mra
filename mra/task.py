from typing import List

from mra.durable_state import DurableState
from mra.actions.action import Action

class TaskMeta(dict):
    @property
    def title(self) -> str:
        return self.get('title', 'Title Not Set')

    @title.setter
    def title(self, value: str):
        self['title'] = value

    @property
    def completed(self) -> bool:
        return self.get('completed', False)

    @completed.setter
    def completed(self, value: bool):
        self['completed'] = value

    @property
    def result(self) -> any:
        return self.get('result', None)

    @result.setter
    def result(self, value: any):
        self['result'] = value

    @property
    def exception(self) -> Exception or None:
        return self.get('exception', None)

    @exception.setter
    def exception(self, value: Exception):
        self['exception'] = value

    @property
    def last_action(self):
        return self.get('last_action', None)

    @last_action.setter
    def last_action(self, value: Action):
        self['last_action'] = value

    @property
    def logs(self) -> List[str]:
        return self.get('logs', [])

    @logs.setter
    def logs(self, logs: List[dict]):
        self['logs'] = [log['log'] for log in logs]

    @property
    def reports(self):
        return self.get('reports', [])

    @reports.setter
    def reports(self, reports: List[dict]):
        self['reports'] = [log['log'] for log in reports]

    def report(self):
        completed = 'completed'
        result = self.result
        maybe_exception = ''
        if not self.completed:
            completed = 'incomplete'
            result = f'exception in {self.last_action}'
            maybe_exception = f'Exception: {self.exception}\n\t'

        report_lines = []
        if self.reports:
            report_lines = [
                '\tReports:',
                '\t{reports}'.format(reports='\n\t'.join(self.reports))
            ]

        log_lines = []
        if self.logs:
            log_lines = [
                '\tLogs:',
                '\t{logs}'.format(logs='\n\t'.join(self.logs))
            ]

        lines = [
            '\n\n{title}[{completed}] -> {result}'.format(title=self.title, completed=completed, result=result),
            '\t{maybe_exception}'.format(maybe_exception=maybe_exception),
        ]

        if report_lines:
            lines.extend(report_lines)

        if log_lines:
            lines.extend(log_lines)

        return '\n'.join(lines)

class Task(DurableState):
    PATH = "Task"

    def __init__(self, *actions):
        super().__init__()
        self.actions = list(actions)
        self.completed = []
        self.result = None
        self.failed = False
        self.meta = TaskMeta()

    def __len__(self):
        return len(self.actions)

    def label(self, title):
        self.meta.title = title

    async def setup(self):
        await self.update({
           'done': [],
           'actions': [a.durable_id for a in self.actions]
        })
        for a in self.actions:
            await a.setup()
            # start managing the loggers of the actions
            self._adopt(a)
        self.result = None

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
        return self.failed or len(self.actions) == 0

    async def advance(self) -> None:
        await self.current.execute(self.result)
        self.result = self.current.result
        if self.current.exception:
            self.failed = True
            self.meta.exception = self.current.exception
            self.meta.last_action = self.current
            self.meta.completed = False

        await self.current.is_done()

        self.completed.append(self.actions.pop(0))
        self['done'].append(self['actions'].pop(0))
        await self.update(await self.read())

    async def report(self, should_print) -> None:
        self.meta.logs = self._get_logs()
        self.meta.reports = self._get_reports()
        if should_print:
            print(self.meta.report())

    async def run(self, print=True) -> TaskMeta:
        await self.setup()
        while not self.done:
            await self.advance()

        if not self.failed:
            self.meta.completed = True

        await self.report(print)

        await self.cleanup()
        return self.meta

    def __str__(self):
        return f"Task[{self.current}]->{self.next}"