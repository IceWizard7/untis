# Session

## 1. Initializing a Session

```python
import untis

my_logger = untis.logging.Logger()

my_session = untis.Session(
    # Per-session configuration
    session_name='my_session',
    use_cache=True,  # See Section 2 for details
    cache_file='my_cache.pkl',
    logger=my_logger,
    
    # Credentials
    username='insert_your_username',
    password='insert_your_password',
    server='insert-your-school.webuntis.com/WebUntis',
    school='insert-your-school',
    client='WebUntis Test'
)
```

## 2. Logging in, out & retrieving data

```python
import untis
import datetime

my_session = untis.Session(
    ...
)

# Safe under concurrency
call_id = my_session.get_unique_uuid()

# Logging in
my_session.log_in(call_id)

# Retrieving data
klasse = my_session.get_klasse_by_name('1a')  # Try '1A' alternatively

today = datetime.date.today()
monday = today - datetime.timedelta(days=today.weekday())
friday = monday + datetime.timedelta(days=4)

table = my_session.timetable_extended(klasse=klasse, start=monday, end=friday)

# Log out
my_session.log_out(call_id)
```

## 3. Caching

Caching is supported: If you enable `use_cache` while initializing the Session, any method that is decorated with
`@cached_method` will first try to reserve the result from the cache (if it has already been received), before fetching
it from the API. Any method that makes reasonable sense to annotate with `@cached_method`, is. Additionally, there are
a few helper methods to interact with the cache:

- `clear_cache()`: Clear the current cache from the memory (For example, to refresh data).
- `read_cache_from_file()`: Reads the cache from the `cache_file` to memory.
- `write_cache_to_file()`: Writes the current cache to the `cache_file`.

## 4. Low Level vs. High Level API Calls
The `Session` object implements Low Level API Calls, as well as High level, abstracted convenience methods.

The webuntis jsonrpc API has a few simple endpoints, for example:
- `getKlassen`
- `getRooms`
- `getSubjects`
- `getHolidays`
- `getTimetable`
- ...

These are partially abstracted and converted into methods of `Session` objects, which don't just return raw JSON,
but instead python objects, for example (Low Level API Calls):
- `all_klassen() -> list[Class]`
- `all_rooms() -> list[Room]`
- `all_klassen() -> list[Class]`
- `timetable_extended() -> TimeTable`

Because student accounts normally don't have access to teacher or room timetables, there are no separate methods for
these operations. However, `multithreading_result()`
can be used to achieve this (High Level API Calls):
- This method will get the timetable for every single class at your school in a given time frame
- Using that, you can construct room and teacher timetables using the `filter_hours_by_room()` or
`filter_hours_by_teacher()` methods.

## 5. Concurrency

The `Session` objects are safe to use under concurrency (multiple threads using the same session)
if the following conditions are met:
- `call_id` is never re-used. When loging in, always use a new `call_id` which can be 
received from `Session.get_unique_uuid()`. Also, when loging out, always use the same `call_id` that was used to log in.
This way we can keep the connection to the webuntis API until the last thread finishes execution and logs out. Only then
a logout request is actually sent.
- Always use `Session.multithreading_result()` when using multithreading. This will summon multiple threads
(`_multithread_worker`) which are tested to always work together. This is achieved using a threading lock, so
race conditions are omitted.
