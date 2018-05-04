from mra.helpers.util import UpdatableDict
from typing import List

class TaskMeta(UpdatableDict):

    title = UpdatableDict._variable_property('title', '')
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