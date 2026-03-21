# Exceptions & Errors

> [!CAUTION]
> The List of Exceptions will be updated soon.

## List of Exceptions:
- `WebUntisAPIError`: Base class of all untis-exceptions.
- `NotAuthenticatedError`: `Session.log_in()` was not called before retrieving data from the API. By default,
`Session._rpc_request` will retry the request once if `log_in` was not called before. However, that is not optimal,
because it will cause a lot of unnecessary `log_in()` and `log_out()`.

Read [exceptions.py](../untis/exceptions.py) for more info.
