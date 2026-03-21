import typing
import datetime
import colorama


class LogLevels:
    DEBUG: typing.Final[int] = 0
    INFO: typing.Final[int] = 1
    WARNING: typing.Final[int] = 2
    ERROR: typing.Final[int] = 3


class Logger:
    def __init__(self) -> None:
        self.log_messages: dict[int, list[typing.Any]] = {
            LogLevels.DEBUG: [],
            LogLevels.INFO: [],
            LogLevels.WARNING: [],
            LogLevels.ERROR: []
        }
        self.only_log_levels: list[int] = [
            LogLevels.INFO, LogLevels.WARNING, LogLevels.ERROR
        ]

    def log_debug(self, message: typing.Any) -> None:
        self._log(message, LogLevels.DEBUG)

    def log_info(self, message: typing.Any) -> None:
        self._log(message, LogLevels.INFO)

    def log_warning(self, message: typing.Any) -> None:
        self._log(message, LogLevels.WARNING)

    def log_error(self, message: typing.Any) -> None:
        self._log(message, LogLevels.ERROR)

    def _log(self, message: typing.Any, level: int) -> None:
        self.log_messages[level].append(message)
        if level == 0:
            print(
                f'{colorama.Fore.GREEN}[{level}] {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}:'
                f' {message}{colorama.Style.RESET_ALL}'
            )
        elif level == 1:
            print(
                f'{colorama.Fore.CYAN}[{level}] {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}:'
                f' {message}{colorama.Style.RESET_ALL}'
            )
        elif level == 2:
            print(
                f'{colorama.Fore.YELLOW}[{level}] {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}:'
                f' {message}{colorama.Style.RESET_ALL}'
            )
        elif level == 3:
            print(
                f'{colorama.Fore.RED}[{level}] {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}:'
                f' {message}{colorama.Style.RESET_ALL}'
            )

    def log_levels(self, levels: list[int]) -> None:
        self.only_log_levels = levels
