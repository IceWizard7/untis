# Exceptions & Errors

## List of Exceptions:
- `WebUntisAPIError`: Base class of all untis-exceptions. Never gets raised directly.
- `NotAuthenticatedError`: `Session.log_in()` was not called before retrieving data from the API. By default,
`Session._rpc_request` will retry the request once if `log_in` was not called before. However, that is not optimal,
because it will cause a lot of unnecessary `log_in()` and `log_out()`.
- `NoRightForMethodError`: Your webuntis account does not have rights to access that method. Common examples are teacher or room timetables if you use a student account.
- `MethodNotFoundError`: The webuntis server did not find that method (should never occur if you use the built-in low & high level APIs)
- `IllegalArgumentError`: There was an unexpected argument passed into a function.

Read [exceptions.py](../untis/exceptions.py) for more info.
