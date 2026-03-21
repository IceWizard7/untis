import typing


class WebUntisAPIError(Exception):
    """ Base class for untis-exceptions. Never gets raised directly. """
    def __init__(self, *args: typing.Any) -> None:
        super().__init__(*args)


class NotAuthenticatedError(WebUntisAPIError):
    """ Not authenticated. """
    def __init__(self, error: typing.Any, *args: typing.Any) -> None:
        super().__init__(error, *args)
