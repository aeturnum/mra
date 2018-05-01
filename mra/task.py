from typing import List
import traceback

from mra.durable_state import DurableState
from mra.util import UpdatableDict, is_instance
from mra.actions.action import EarlyExit

class TaskMeta(UpdatableDict):

    title = UpdatableDict._variable_property('title', 'Title Not Set')
    completed = UpdatableDict._variable_property('completed', False)
    still_running = UpdatableDict._variable_property('still_running', True)
    result = UpdatableDict._variable_property('result')
    exception = UpdatableDict._variable_property('exception')
    trace = UpdatableDict._variable_property('trace')
    last_action = UpdatableDict._variable_property('last_action')

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
            # for log in self.logs:
            #     print(log)
            log_lines = [
                '\n\tLogs:',
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

        if self.trace:
            trace = self.trace.split('\n')
            lines.extend([
                '\n\t' + '\n\t'.join(trace)
            ])

        return '\n'.join(lines)

class Task(DurableState):
    PATH = "Task"

    def __init__(self, *actions):
        super().__init__()
        self.registry = {}
        self.actions = list(actions)
        self.completed = []
        self.result = None
        self.failed = False
        self.meta = TaskMeta()

    @property
    def current(self):
        if len(self.actions) > 0:
            return self.actions[0]
        return None

    @property
    def next(self):
        if len(self.actions) > 1:
            return self.actions[1]
        return None

    @property
    def done(self):
        return not self.meta.still_running

    def __len__(self):
        return len(self.actions)

    def label(self, title):
        self.meta.title = title

    async def setup(self):
        # todo: create tooling around browsing and understanding history
        await self.update({
           'done': [],
           'actions': [a.durable_id for a in self.actions]
        })
        for a in self.actions:
            await a.setup(self.registry)
            # start managing the loggers of the actions
            self._adopt(a)
        self.result = None

    async def cleanup(self):
        for a in self.actions:
            await a.cleanup()

        for a in self.completed:
            await a.cleanup()

    async def advance(self) -> None:
        # execute current action
        print(f'advance(): {self.current}')
        await self.current.execute(self.result)
        print(f'advance(): {self.current} executed')
        # get result
        self.result = self.current.result
        # print(f'advance(): {self.current} -> {self.result}')
        # update meta fields
        self.meta.last_action = self.current
        self.meta.exception = self.current.exception
        self.meta.trace = self.current.trace

        # make sure action does any cleanup
        await self.current.is_done()
        # print(f'advance(): {self.current} done')
        # move to done categories
        self.completed.append(self.actions.pop(0))
        self['done'].append(self['actions'].pop(0))

        # check if we need to perform more actions
        if self.meta.exception is not None:
            # print(f'advance(): raised exception')
            # all exceptions mean we're done
            self.meta.still_running = False
            # assume this means it's failed
            self.meta.completed = False
            if is_instance(self.meta.exception, EarlyExit):
                # if it's an early exit, we need to get its values
                self.meta.completed = self.meta.exception.completed
                # return would be impossible
                self.result = self.meta.exception.result
                # blank exception, its job is done
                # todo: make this a special case for reporting
                self.meta.exception = None

        await self.update(await self.read())

        if len(self.actions) is 0:
            # we're done
            self.meta.still_running = False

    async def report(self, should_print) -> TaskMeta:
        self.meta.logs = self._lh.get_logs()
        self.meta.reports = self._lh.get_reports()
        if should_print:
            print(self.meta.report())

        return self.meta

    async def run(self, print_result=True, registry=None) -> TaskMeta:
        # note, this is why duck typing sucks.
        # If you use the 'pythonic' line if registry:
        # and registry is empty (but shared) than it won't trigger
        # because it has no keys and is considered 'falsey'
        if registry is not None:
            self.registry = registry
        try:
            await self.setup()
            while not self.done:
                await self.advance()

            await self.cleanup()
        except Exception as e:
            print("Exception log_report in task.run")
            traceback.print_exc()
        finally:
            return await self.report(print_result)


    def __str__(self):
        return f"Task[{self.current}]->{self.next}"