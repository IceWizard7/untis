import typing


class WebUntisAPIError(Exception):
    def __init__(self, *args: typing.Any) -> None:
        pass


class NotAuthenticatedError(WebUntisAPIError):
    def __init__(self, error: typing.Any, *args: typing.Any) -> None:
        pass
