from datetime import datetime
from logging import getLogger
from mra.util import is_instance

# Levels
LOG_LEVEL_SPEW = 0
LOG_LEVEL_SYSTEM = 1
LOG_LEVEL_DEBUG = 2
LOG_LEVEL_WARN = 3
LOG_LEVEL_ERROR = 4

# non-log
LOG_LEVEL_REPORT = -1

# global log level
_Level = LOG_LEVEL_DEBUG

# Class exists to move a lot of constants out of the namespace of loggers
class LoggerHelper(object):
    depth_character = "  "

    l0 = LOG_LEVEL_SPEW
    l1 = LOG_LEVEL_SYSTEM
    l2 = LOG_LEVEL_DEBUG
    l3 = LOG_LEVEL_WARN
    l4 = LOG_LEVEL_ERROR

    tags = {
        LOG_LEVEL_SPEW: 'P',
        LOG_LEVEL_SYSTEM: 'S',
        LOG_LEVEL_DEBUG: 'D',
        LOG_LEVEL_WARN: 'W',
        LOG_LEVEL_ERROR: 'E',
        # reports
        LOG_LEVEL_REPORT: 'R'
    }

    r = LOG_LEVEL_REPORT

    def __init__(self):
        self._depth = 0
        self.parent = None
        self.children = []
        # log_error logs
        self.log_lines = []
        # reports to be printed in all cases
        self.report_lines = []

    @staticmethod
    def _dict_to_str(d: dict):
        l = []
        for key, value in d.items():
            if type(value) is dict:
                value = LoggerHelper._dict_to_str(value)
            if value is None:
                # note: ths space after the 🇳 is a half space " "
                value = '🇳 '
            l.append(f'{key}:{value}')
        return ','.join(l)

    @staticmethod
    def filter_args(args: tuple):
        new_args = []
        for arg in args:
            if type(arg) is dict:
                arg = LoggerHelper._dict_to_str(arg)
            new_args.append(arg)

        return new_args

    @property
    def logs(self):
        return [self.l0, self.l1, self.l2, self.l3, self.l4]

    @property
    def reports(self):
        return [self.r]

    def adopt(self, other_log_helper: 'LoggerHelper'):
        if other_log_helper.parent is not None:
            other_log_helper.parent.children.remove(other_log_helper)
        #     raise ValueError(f'{other_logger} already adopted!')

        other_log_helper.parent = self
        self.children.append(other_log_helper)

    @staticmethod
    def _log_sort(a):
        return a['time']

    def get_logs(self):
        global _Level

        all_logs = list(self.log_lines)
        for child in self.children:
            all_logs.extend(child.get_logs())

        all_logs.sort(key=self._log_sort)
        # remove logs "below" the level we care about
        return filter(lambda log: log['level'] >= _Level, all_logs)

    def get_reports(self):
        all_reports = list(self.report_lines)
        for child in self.children:
            all_reports.extend(child.get_reports())

        all_reports.sort(key=self._log_sort)
        return all_reports

class Logger(object):
    _logger_name = ""

    def __init__(self):
        self._lh = LoggerHelper()
        self._logger = getLogger(self._logger_name)

    def _build_final_string(self, level: int, now: datetime, log_str: any, *args) -> str:
        time_string = now.strftime('%H:%M:%S.%f')
        if len(args) > 0:
            log_str = log_str.format(*self._lh.filter_args(args))
        else:
            log_str = str(log_str)
        return f'{self._lh.tags[level]}|{self._lh._depth * self._lh.depth_character}[{time_string}] {self}::{log_str}'

    def _log(self, level:int, log_str:any, *args):
        now = datetime.utcnow()
        log_str = self._build_final_string(level, now, log_str, *args)

        log = {
                'time': now,
                'log': log_str,
                'level': level
        }

        if level in self._lh.logs:
            if type(log['log']) is not str:
                print(f'non-str log: {log["log"]}')
            self._lh.log_lines.append(log)
        if level in self._lh.reports:
            self._lh.report_lines.append(log)

        # if we have a parent, logs will be collected
        if not self._lh.parent:
            print(log_str)
            if level == self._lh.l2:
                self._logger.debug(log_str)
            if level == self._lh.l3:
                self._logger.warning(log_str)
            if level == self._lh.l4:
                self._logger.error(log_str)

    def log_spew(self, log_str: any, *args):
        self._log(self._lh.l0, log_str, *args)

    def log_system(self, log_str: any, *args):
        self._log(self._lh.l1, log_str, *args)

    def log_debug(self, log_str: any, *args):
        self._log(self._lh.l2, log_str, *args)

    def log_warn(self, log_str: any, *args):
        self._log(self._lh.l3, log_str, *args)

    def log_error(self, log_str: any, *args):
        self._log(self._lh.l4, log_str, *args)

    def log_report(self, log_str: any, *args):
        self._log(self._lh.r, log_str, *args)

    def _adopt(self, other_logger):
        if not is_instance(other_logger, Logger):
            # instead, let's silently NOP for now
            # this ineraction always happens within mra so it's less likely to be abused
            # raise TypeError(f'{other_logger} is not a logger!')
            return

        self._lh.adopt(other_logger._lh)

    def __str__(self):
        return "logger"

    def __repr__(self):
        return f'{self.__class__}:{self.__str__()}'
