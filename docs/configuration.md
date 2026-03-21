# Configuration

> [!CAUTION]
> More documentation will follow soon.

## 1. Editing `my_config`

Modify the Configuration using `untis.my_config.* = ...`

For example:
- `untis.my_config.timetable_html_footer = ...`
- `untis.my_config.two_week_abbreviation = ...`
- `untis.my_config.teacher_mapping = ...`
- ...

## 2. Timetable mappings

See [config.py](../untis/config.py) for more info.

### 2.1 Generating element IDs

```python
import typing
import uuid
import untis.objects
import datetime

def _return_data_whole_school_year(
        session: untis.Session,
        call_id: uuid.UUID,
        function_name: str
) -> untis.objects.TimeTable:
    session.log_in(call_id)

    sleep_time: float = 0.2
    max_threads: int = 3
    max_attempts: int = 3
    
    start_of_school_year_normal_timetable: datetime.date = datetime.date(2025, 9, 11)  # 4th day
    end_of_school_year_normal_timetable: datetime.date = datetime.date(2026, 6, 26)  # Second last week, last day

    raw_result: dict[str, str | Exception | dict[str,  untis.objects.TimeTable]] = session.multithreading_result(
        sleep_time, max_threads, 'dummy', start_of_school_year_normal_timetable, end_of_school_year_normal_timetable,
        function_name, False, call_id, True, max_attempts
    )

    if 'exception' in raw_result:
        exception = typing.cast(Exception, raw_result['exception'])
        raise exception

    raw_result_no_error: dict[str, dict[str,  untis.objects.TimeTable]] = typing.cast(
        dict[str, dict[str,  untis.objects.TimeTable]], raw_result
    )

    result_table: untis.objects.TimeTable = untis.objects.TimeTable([])

    for klasse in raw_result_no_error.keys():
        result_table += raw_result_no_error[klasse]['table']

    return result_table


def return_all_subjects(session: untis.Session) -> tuple[list[untis.objects.Subject], dict[untis.objects.Subject, list[str]]]:
    subjects: list[untis.objects.Subject] = []
    subject_info: dict[untis.objects.Subject, list[str]] = {}

    call_id: uuid.UUID = session.get_unique_uuid()

    result_table: untis.objects.TimeTable = _return_data_whole_school_year(session, call_id, 'return_all_subjects')

    for period in result_table.unsorted_table():
        for subject in period.subjects:
            subject_info_string: str = (
                f'{period.klassen[0]}'
                f'|{period.formatted_string(period.klassen[0], False).ljust(55, " ")}'
                f'|{str(period.student_group).ljust(55, " ")}'
                f'|{str(period.start).ljust(10, " ")} - {str(period.end).ljust(10, " ")}'
            )

            if subject not in subjects:
                subjects.append(subject)
            if subject in subject_info.keys():
                subject_info[subject].append(subject_info_string)
            else:
                subject_info[subject] = [subject_info_string]

    subjects.sort(key=lambda item: item.name)

    return subjects, subject_info


def return_all_teacher_ids(session: untis.Session) -> tuple[list[untis.objects.Teacher], dict[untis.objects.Teacher, list[str]]]:
    teachers: list[untis.objects.Teacher] = []
    teacher_info: dict[untis.objects.Teacher, list[str]] = {}

    call_id: uuid.UUID = session.get_unique_uuid()

    result_table: untis.objects.TimeTable = _return_data_whole_school_year(session, call_id, 'return_all_teacher_ids')

    for period in result_table.unsorted_table():
        for teacher in period.teachers + period.original_teachers:
            teacher_info_string: str = (
                f'{period.klassen[0]}'
                f'|{period.formatted_string(period.klassen[0], False).ljust(55, " ")}'
                f'|{str(teacher.entity_id).ljust(4, " ")}'
                f'|{str(period.start).ljust(10, " ")} - {str(period.end).ljust(10, " ")}'
            )

            if teacher not in teachers:
                teachers.append(teacher)
            if teacher in teacher_info.keys():
                teacher_info[teacher].append(teacher_info_string)
            else:
                teacher_info[teacher] = [teacher_info_string]

    teachers.sort(key=lambda item: item.name)

    return teachers, teacher_info
```

## 3. Language specific configuration

See [config.py](../untis/config.py) for more info.

## 4. HTML style configuration

See [config.py](../untis/config.py) for more info.
