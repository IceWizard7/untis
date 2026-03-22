import typing


class LogLevels:
    DEBUG: typing.Final[int] = ...
    INFO: typing.Final[int] = ...
    WARNING: typing.Final[int] = ...
    ERROR: typing.Final[int] = ...


class Logger:
    def __init__(self) -> None:
        self.log_messages: dict[int, list[typing.Any]] = ...
        self.only_log_levels: list[int] = ...

    def log_debug(self, message: typing.Any) -> None:
        pass

    def log_info(self, message: typing.Any) -> None:
        pass

    def log_warning(self, message: typing.Any) -> None:
        pass

    def log_error(self, message: typing.Any) -> None:
        pass

    def _log(self, message: typing.Any, level: int) -> None:
        pass

    def log_levels(self, levels: list[int]) -> None:
        pass
