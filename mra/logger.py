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
_Level = LOG_LEVEL_SYSTEM


class Logger(object):
    _depth_character = "  "
    _logger_name = ""

    _l0 = LOG_LEVEL_SPEW
    _l1 = LOG_LEVEL_SYSTEM
    _l2 = LOG_LEVEL_DEBUG
    _l3 = LOG_LEVEL_WARN
    _l4 = LOG_LEVEL_ERROR

    _tags = {
        LOG_LEVEL_SPEW: 'P',
        LOG_LEVEL_SYSTEM: 'S',
        LOG_LEVEL_DEBUG: 'D',
        LOG_LEVEL_WARN: 'W',
        LOG_LEVEL_ERROR: 'E',
        # reports
        LOG_LEVEL_REPORT: 'R'
    }

    _r = LOG_LEVEL_REPORT

    def __init__(self):
        self._depth = 0
        self._logger = getLogger(self._logger_name)
        self._parent = None
        self._children = []
        # error logs
        self._logs = []
        # reports to be printed in all cases
        self._reports = []

    @staticmethod
    def _dict_to_str(d:dict):
        l = []
        for key, value in d.items():
            if type(value) is dict:
                value = Logger._dict_to_str(value)
            if value is None:
                # note: ths space after the 🇳 is a half space " "
                value = '🇳 '
            l.append(f'{key}:{value}')
        return ','.join(l)

    def _build_final_string(self, level:int, now: datetime, log_str:any, *args) -> str:
        time_string = now.strftime('%H:%M:%S.%f')
        if len(args) > 0:
            log_str = log_str.format(*args)
        else:
            log_str = str(log_str)
        return f'{self._tags[level]}|{self._depth * self._depth_character}[{time_string}] {self}::{log_str}'

    def _log(self, level:int, log_str:any, *args):
        now = datetime.utcnow()
        log_str = self._build_final_string(level, now, log_str, *args)

        log = {
                'time': now,
                'log': log_str,
                'level': level
        }

        if level in [self._l0, self._l1, self._l2, self._l3, self._l4]:
            if type(log['log']) is not str:
                print(f'non-str log: {log["log"]}')
            self._logs.append(log)
        if level in [self._r]:
            self._reports.append(log)

        # if we have a parent, logs will be collected
        if not self._parent:
            print(log_str)
            if level == self._l0:
                self._logger.debug(log_str)
            if level == self._l1:
                self._logger.warning(log_str)
            if level == self._l2:
                self._logger.error(log_str)

    def _spew(self, log_str:any, *args):
        self._log(self._l0, log_str, *args)

    def _system(self, log_str:any, *args):
        self._log(self._l1, log_str, *args)

    def _debug(self, log_str:any, *args):
        self._log(self._l2, log_str, *args)

    def _warn(self, log_str:any, *args):
        self._log(self._l3, log_str, *args)

    def _error(self, log_str:any, *args):
        self._log(self._l4, log_str, *args)

    def _report(self, log_str:any, *args):
        self._log(self._r, log_str, *args)

    def _up(self):
        self._depth += 1

    def _down(self):
        self._depth += 1

    def _adopt(self, other_logger):
        if not is_instance(other_logger, Logger):
            # instead, let's silently NOP for now
            # this ineraction always happens within mra so it's less likely to be abused
            # raise TypeError(f'{other_logger} is not a logger!')
            return

        # if other_logger._parent is not None:
        #     raise ValueError(f'{other_logger} already adopted!')


        other_logger._parent = self
        self._children.append(other_logger)

    @staticmethod
    def _log_sort(a):
        return a['time']

    def _get_logs(self):
        global _Level

        all_logs = list(self._logs)
        for child in self._children:
            all_logs.extend(child._get_logs())

        all_logs.sort(key=self._log_sort)
        # remove logs "below" the level we care about
        return filter(lambda log: log['level'] >= _Level, all_logs)

    def _get_reports(self):
        all_reports = list(self._reports)
        for child in self._children:
            all_reports.extend(child._get_reports())

        all_reports.sort(key=self._log_sort)
        return all_reports

    def __str__(self):
        return "logger"

    def __repr__(self):
        return f'{self.__class__}:{self.__str__()}'
