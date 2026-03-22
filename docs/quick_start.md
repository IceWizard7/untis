# Quick Start

---

## 1. Credentials

```python
import untis

# Expose Globals
my_logger = untis.logging.Logger()

my_logger.log_levels([untis.logging.LogLevels.WARNING, untis.logging.LogLevels.ERROR])

global_session = untis.objects.Session(
    'global_session', False, None, my_logger,

    username='insert_your_username',
    password='insert_your_password',
    server='insert-your-school.webuntis.com/WebUntis',
    school='insert-your-school',
    client='WebUntis Test'
)
```

## 2. Example: HTML Timetable

```python
import datetime

global_session = ...

# Save under concurrency (multiple requests at the same time)
call_id = global_session.get_unique_uuid()
global_session.log_in(call_id)

klasse = global_session.get_klasse_by_name('1a')  # Try '1A' alternatively

today = datetime.date.today()
monday = today - datetime.timedelta(days=today.weekday())
friday = monday + datetime.timedelta(days=4)

table = global_session.timetable_extended(klasse=klasse, start=monday, end=friday)

table_name: tuple[str, str] = table.get_table_name(klasse, monday, friday)

# Generating the actual HTML
html_result = table.to_untis_html(klasse, 0, False, table_name, monday, friday)

print(html_result)
```
