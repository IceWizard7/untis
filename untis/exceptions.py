import typing


class WebUntisAPIError(Exception):
    """ Base class for untis-exceptions. Never gets raised directly. """
    def __init__(self, *args: typing.Any) -> None:
        super().__init__(*args)


class NotAuthenticatedError(WebUntisAPIError):
    """ Not authenticated. """
    def __init__(self, error: typing.Any, *args: typing.Any) -> None:
        super().__init__(error, *args)


class NoRightForMethod(WebUntisAPIError):
    """ No right for method. """
    def __init__(self, error: typing.Any, method_name: str, *args: typing.Any) -> None:
        super().__init__(error, method_name, *args)


class MethodNotFound(WebUntisAPIError):
    """ Method not found. """
    def __init__(self, error: typing.Any, method_name: str, *args: typing.Any) -> None:
        super().__init__(error, method_name, *args)
