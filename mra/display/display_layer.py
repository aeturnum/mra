from tqdm import tqdm
from mra.display.meta import TaskMeta

class TaskProgressTracker(object):
    def __init__(self, parent, index: int):
        self._parent = parent
        self.index = index
        self.total = -1
        self.bar = None
        self.action_count = 1
        self._task = None
        self.title = f'{self.index}'
        self.status = ''

    def _create_bar(self):
        self.bar = tqdm(total=self.total, position=self.index)
        self.set_desc('Waiting to be setup...')

    def register_task(self, task):
        # base count is 1 (setup) + 1 (cleanup) + action count
        self.total =  1 + len(task.actions) + 1
        self._task = task
        self.refresh()
        self._create_bar()

    async def start_setup(self):
        self.set_desc("setup")

    async def finish_setup(self):
        if self.bar:
            self.bar.update()

    async def start_action(self):
        self.set_desc(f'Action {self.action_count}')
        self.action_count += 1

    async def finish_action(self):
        if self.bar:
            self.bar.update()

    async def start_cleanup(self):
        self.set_desc("cleanup")

    async def finish_cleanup(self):
        if self.bar:
            self.bar.update()
            self.bar.close()

    def refresh(self):
        if self._task.meta.title:
            self.title = self._task.meta.title
        self.set_desc()

    def set_desc(self, status = None):
        if status is not None:
            self.status = status
        if self.bar:
            self.bar.set_description(f'{self.title} [{self.status}]')

    def submit_final_meta(self, meta:TaskMeta):
        self._parent.submit_report(self.index, meta.report())

    @property
    def should_print(self):
        return self._parent.should_print

class SetupTaskProgressTracker(TaskProgressTracker):
    def _create_bar(self):
        pass

    def submit_final_meta(self, meta:TaskMeta):
        if not meta.completed:
            # if this failed, we need to log why, otherwise be silent
            self._parent.submit_report(self.index, meta.report())

    @property
    def should_print(self):
        return False

class DisplayLayer(object):
    def __init__(self, settings):
        self.settings = settings
        self._tasks_tracked = []
        self._reports = []
        self.should_print = True

    def task_tracker(self, setup_tracker=False):
        if setup_tracker:
            tt = SetupTaskProgressTracker(self, 0)
        else:
            tt = TaskProgressTracker(self, len(self._tasks_tracked))
            self._tasks_tracked.append(tt)
        return tt

    def submit_report(self, index, report):
        self._reports.append({
            'index': index,
            'report': report
        })

    @staticmethod
    def sort_index(report_dict):
        return report_dict['index']

    def print_reports(self):
        self._reports.sort(key=self.sort_index)
        for r in self._reports:
            print(r['report'])


