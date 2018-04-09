from datetime import datetime
from logging import getLogger

# Levels
LOG_LEVEL_DEBUG = 0
LOG_LEVEL_WARN = 1
LOG_LEVEL_ERROR = 2

# global log level
_Level = 4


class Logger(object):
    _depth_character = "  "
    _logger_name = ""

    _l0 = LOG_LEVEL_DEBUG
    _l1 = LOG_LEVEL_WARN
    _l2 = LOG_LEVEL_ERROR

    def __init__(self):
        self._depth = 0
        self._logger = getLogger(self._logger_name)

    @staticmethod
    def _dict_to_str(d:dict):
        l = []
        for key, value in d.items():
            if type(value) is dict:
                value = Logger._dict_to_str(d)
            if value is None:
                # note: ths space after the 🇳 is a half space
                value = '🇳 '
            l.append(f'{key}:{value}')
        return ','.join(l)

    def _build_final_string(self, log_str:str, *args):
        time_string = datetime.utcnow().strftime('%H:%M:%S.%f')
        log_str = log_str.format(*args)
        return f'{self._depth * self._depth_character}[{time_string}] {self}::{log_str}'

    def _log(self, level:int, log_str:str, *args):
        log_str = self._build_final_string(log_str, *args)
        print(log_str)
        if level == self._l0:
            self._logger.debug(log_str)
        if level == self._l1:
            self._logger.warning(log_str)
        if level == self._l2:
            self._logger.error(log_str)

    def _debug(self, log_str:str, *args):
        self._log(self._l0, log_str, *args)

    def _warn(self, log_str:str, *args):
        self._log(self._l1, log_str, *args)

    def _error(self, log_str:str, *args):
        self._log(self._l2, log_str, *args)

    def _up(self):
        self._depth += 1

    def _down(self):
        self._depth += 1


