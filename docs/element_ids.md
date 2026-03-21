## Examples:

> [!CAUTION]
> More documentation will follow soon.

```python
def return_all_subjects(session: MySession) -> tuple[list[MySubject], dict[MySubject, list[str]]]:
    subjects: list[MySubject] = []
    subject_info: dict[MySubject, list[str]] = {}

    call_id: uuid.UUID = session.get_unique_uuid()

    result_table: MyTimeTable = _return_data_whole_school_year(session, call_id, 'return_all_subjects')

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


def return_all_teacher_ids(session: MySession) -> tuple[list[MyTeacher], dict[MyTeacher, list[str]]]:
    teachers: list[MyTeacher] = []
    teacher_info: dict[MyTeacher, list[str]] = {}

    call_id: uuid.UUID = session.get_unique_uuid()

    result_table: MyTimeTable = _return_data_whole_school_year(session, call_id, 'return_all_teacher_ids')

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
