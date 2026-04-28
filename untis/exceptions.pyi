import typing


class WebUntisAPIError(Exception):
    def __init__(self, *args: typing.Any) -> None:
        pass


class NotAuthenticatedError(WebUntisAPIError):
    def __init__(self, error: typing.Any, *args: typing.Any) -> None:
        pass


class NoRightForMethodError(WebUntisAPIError):
    def __init__(self, error: typing.Any, method_name: str, *args: typing.Any) -> None:
        pass

class MethodNotFoundError(WebUntisAPIError):
    def __init__(self, error: typing.Any, method_name: str, *args: typing.Any) -> None:
        pass

class IllegalArgumentError(WebUntisAPIError):
    def __init__(self, error: typing.Any, method_name: str, *args: typing.Any) -> None:
        pass
