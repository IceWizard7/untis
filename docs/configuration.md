# Configuration

> [!CAUTION]
> More documentation will follow soon.

## 1. Editing `my_config`

### 1.1 Setting the language

Set the language using:

- `untis.my_config.set_lang('en')`
- `untis.my_config.set_lang('de')`

Note: Currently only german (`'de'`) and english (`en`) is supported.

### 1.2 Understanding the objects

`units.my_config` is split into 3 subclasses:
- `timetable_mapping_config (TimeTableMappingConfig)`
- `self.language_config (LanguageConfig)`
- `self.html_style_config (HTMLStyleConfig)`

### 1.3 Modifying specific values

Modify the Configuration using `untis.my_config.* = ...`

For example:
- `untis.my_config.html_style_config.timetable_html_footer = ...`
- `untis.my_config.language_config.two_week_abbreviation = ...`
- `untis.my_config.timetable_mapping_config.teacher_mapping = ...`
- ...


## 2. Timetable mappings

Example `personal_timetable_entries`
```python
untis.my_config.timetable_mapping_config.personal_timetable_entries: dict[str, tuple[set[str], set[str]]] = {
    'child1': (
        # Set of teacher abbreviations
        {'T1', 'T2', 'T3', ...},
        # Set of subject abbreviations
        {'M', 'G', 'E', ...}),
    'child2': (
        {'T1', 'T2', 'T3', ...},
        {'M', 'G', 'E', ...}),
}
```
This allows using `TimeTable.filter_hours_by_personal('child1')` on an existing TimeTable, which only returns the
lessons with certain teachers or subjects connected to it. Useful if your child is in a class, where some pupils attend
lessons that your child doesn't.

Example `teacher_mapping`
```python
untis.my_config.timetable_mapping_config.teacher_mapping: dict[int, tuple[str, str, tuple[str, ...]]] = {
      0: ('Unknown', 'N/A', ('/',)),  # Always means no teacher, never assign a real name here
    # Teacher ID: (full name,       abbreviated Name, (Subject abbreviation 1, ...)
      3:          ('Tom Mister',   'AB',              ('M', 'G', 'E')),
      8:          ('Benjamin Bob', 'CD',              ('PS', 'PE', 'FR')),
}
```

This allows the TimeTable to format the name of the teachers correctly. The API technically does have a
`Session.teachers()` function which uses the webuntis `getTeachers` endpoint. However, most student accounts don't have
access to that endpoint. I'm working on a way integrate with the getTeachers endpoint directly for the accounts that
support it.

> [!CAUTION]
> More documentation will follow soon.

Generating this mapping is rather tedious, but the first step is getting the IDs.
See [2.1 Generating element IDs](#21-generating-element-ids) for help.

Example `subject_to_color`
```python
untis.my_config.timetable_mapping_config.subject_to_color: dict[tuple[str, str, int], tuple[int, int, int]] = {
    # Subjet abbreviation, full subject name, subject id: RGB Value
      ('M',              'Math',              107):       (83, 103, 220),
      ('E',              'English',           193):       (45, 26, 136),
      ('FR',             'French',            981):       (122, 112, 212)
}
```
This allows the TimeTable to display corresponding colours along with the subject names.
The API technically delivers this, but I'm still uncertain whether this is safe to use.

Generating this mapping is rather tedious, but the first step is getting the IDs.
See [2.1 Generating element IDs](#21-generating-element-ids) for help.

Also see [config.py](../untis/config.py) for more info on `TimeTableMappingConfig`.

### 2.1 Generating element IDs

In the following you will see the code I used to generate teacher & subject IDs.

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


def return_all_subjects(
        session: untis.Session
) -> tuple[list[untis.objects.Subject], dict[untis.objects.Subject, list[str]]]:
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


def return_all_teacher_ids(
        session: untis.Session
) -> tuple[list[untis.objects.Teacher], dict[untis.objects.Teacher, list[str]]]:
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

In this section, `Teacher` and `Subject` is interchangeable. Use `return_all_subjects` for receiving `Subject`s,
and `return_all_teacher_ids` for `Teacher`s. The concept is the same for both.

These functions will return a `tuple[list[untis.objects.Teacher], dict[untis.objects.Teacher, list[str]]]`:
- First element: `teachers: list[Teacher]`, the `name` and `long_name` fields will be set to `unknown` initially. 

- Second element: `teacher_info: dict[untis.objects.Teacher, list[str]]`, this will help you fill up the teacher
mapping. Each teacher will have a few lessons associated with it, so you can create the mapping `ID -> name`.
In the Untis app the names of the teachers will be displayed, so open the Untis app and manually find the lessons
and transfer the names of the teachers. I am aware that this is very tedious to do, especially if your school has
hundreds of teachers.

> [!CAUTION]
> More documentation will follow soon.

## 3. Language specific configuration

Also see [Setting the language](#11-setting-the-language) for more info on setting the language.

You can also manipulate values manually, for example:
- `untis.my_config.language_config.two_week_abbreviation = ...`
- `untis.my_config.language_config.two_week_abbreviation = ...`
- ...

Also see [config.py](../untis/config.py) for more info on `LanguageConfig`.

## 4. HTML style configuration

Also see [Setting the language](#11-setting-the-language) for more info on setting the language.

You can also manipulate values manually, for example:
- `my_config.html_style_config.timetable_html_footer = ...`
- `my_config.html_style_config.html_style_config.lesson_time_ranges = ...`
- `my_config.html_style_config.html_style_config.table_header_base_rgb = ...`
- ...

Also see [config.py](../untis/config.py) for more info on `HTMLStyleConfig`.
