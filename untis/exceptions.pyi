import typing


class WebUntisAPIError(Exception):
    def __init__(self, *args: typing.Any) -> None:
        pass


class NotAuthenticatedError(WebUntisAPIError):
    def __init__(self, error: typing.Any, *args: typing.Any) -> None:
        pass


class NoRightForMethod(WebUntisAPIError):
    def __init__(self, error: typing.Any, method_name: str, *args: typing.Any) -> None:
        pass

class MethodNotFound(WebUntisAPIError):
    def __init__(self, error: typing.Any, method_name: str, *args: typing.Any) -> None:
        pass
