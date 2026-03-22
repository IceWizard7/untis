from __future__ import annotations
import datetime
import dataclasses
import typing
import functools
import pickle
import playwright.async_api
import io
import re
import threading
import sys
import time as time_module
import uuid
import pathlib
import asyncio
import requests

from .exceptions import NotAuthenticatedError, NoRightForMethod, MethodNotFound
from .logging import Logger
from .config import Config


@dataclasses.dataclass(frozen=True)
class BaseEntity:
    name: str
    long_name: str
    entity_id: int  # Generic id for any entity

    @classmethod
    def from_tuple(cls: type[typing.Self], raw_obj: tuple[str, str, int]) -> typing.Self:
        return cls(
            name=raw_obj[0],
            long_name=raw_obj[1],
            entity_id=raw_obj[2]
        )

    @classmethod
    def from_dict(cls, data: dict[str, str | int]) -> typing.Self:
        """
        Construct from a dict with keys: name, long_name, entity_id
        """
        return cls(
            name=typing.cast(str, data["name"]),
            long_name=typing.cast(str, data["longName"]),
            entity_id=typing.cast(int, data["id"])
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(name={self.name}, long_name={self.long_name}, entity_id={self.entity_id})'

    def __str__(self) -> str:
        return repr(self)


class Subject(BaseEntity):
    @property
    def color(self) -> tuple[int, int, int]:
        if (self.name, self.long_name, self.entity_id) in my_config.timetable_mapping_config.subject_to_color.keys():
            return my_config.timetable_mapping_config.subject_to_color[(self.name, self.long_name, self.entity_id)]
        return 255, 255, 255


class Class(BaseEntity):
    pass


class Room(BaseEntity):
    pass


class Teacher(BaseEntity):
    @property
    def subjects(self) -> tuple[str, ...] | str:
        if self.entity_id in my_config.timetable_mapping_config.teacher_mapping.keys():
            return my_config.timetable_mapping_config.teacher_mapping[self.entity_id][2]
        return str(self.entity_id)

    @staticmethod
    def _get_name(raw_teacher_id: int) -> str:
        if raw_teacher_id in my_config.timetable_mapping_config.teacher_mapping.keys():
            return my_config.timetable_mapping_config.teacher_mapping[raw_teacher_id][1]
        return str(raw_teacher_id)

    @staticmethod
    def _get_long_name(raw_teacher_id: int) -> str:
        if raw_teacher_id in my_config.timetable_mapping_config.teacher_mapping.keys():
            return my_config.timetable_mapping_config.teacher_mapping[raw_teacher_id][0]
        return str(raw_teacher_id)

    @classmethod
    def from_teacher_id(
            cls: type[typing.Self],
            raw_teacher_id: int
    ) -> typing.Self:
        return cls(
            Teacher._get_name(raw_teacher_id),
            Teacher._get_long_name(raw_teacher_id),
            raw_teacher_id
        )

    @classmethod
    def from_teacher_name(
            cls: type[typing.Self],
            raw_teacher_name: str
    ) -> typing.Self:
        raw_teacher_id: int = 0
        for tid in my_config.timetable_mapping_config.teacher_mapping.keys():
            if my_config.timetable_mapping_config.teacher_mapping[tid][1] == raw_teacher_name:
                raw_teacher_id = tid
                break

        return cls(
            Teacher._get_name(raw_teacher_id),
            Teacher._get_long_name(raw_teacher_id),
            raw_teacher_id
        )

    @classmethod
    def from_teacher_long_name(
            cls: type[typing.Self],
            raw_teacher_long_name: str
    ) -> typing.Self:
        raw_teacher_id: int = 0
        for tid in my_config.timetable_mapping_config.teacher_mapping.keys():
            if my_config.timetable_mapping_config.teacher_mapping[tid][0] == raw_teacher_long_name:
                raw_teacher_id = tid
                break

        return cls(
            Teacher._get_name(raw_teacher_id),
            Teacher._get_long_name(raw_teacher_id),
            raw_teacher_id
        )


class Department(BaseEntity):
    pass


@dataclasses.dataclass(frozen=True)
class BaseDateEntity:
    name: str
    long_name: str
    entity_id: int
    start_date: datetime.date
    end_date: datetime.date

    @classmethod
    def from_tuple(
            cls: type[typing.Self], raw_obj: tuple[str, str, int, datetime.date, datetime.datetime]
    ) -> typing.Self:
        return cls(
            name=raw_obj[0],
            long_name=raw_obj[1],
            entity_id=raw_obj[2],
            start_date=raw_obj[3],
            end_date=raw_obj[4],
        )

    @classmethod
    def from_dict(cls, data: dict[str, str | int]) -> typing.Self:
        """
        Construct from a dict with keys: name, long_name, entity_id
        """
        def parse_date(value: typing.Optional[int]) -> typing.Optional[datetime.date]:
            if value is None:
                return None
            return datetime.datetime.strptime(str(value), "%Y%m%d").date()

        return cls(
            name=typing.cast(str, data["name"]),
            long_name=typing.cast(str, data["longName"]),
            entity_id=typing.cast(int, data["id"]),
            start_date=parse_date(data.get("startDate")),
            end_date=parse_date(data.get("endDate"))
        )

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}(name={self.name}, long_name={self.long_name},'
            f' entity_id={self.entity_id}, start_date={self.start_date}, end_date={self.end_date})'
        )

    def __str__(self) -> str:
        return repr(self)


class Holiday(BaseDateEntity):
    pass


class SchoolYear(BaseDateEntity):
    pass


class Period:
    def __init__(
            self,
            raw_period_code: str | None,
            start: datetime.datetime,
            end: datetime.datetime,
            subjects: list[Subject],
            klassen: list[Class],
            rooms: list[Room],
            original_rooms: list[Room],
            teachers: list[Teacher],
            original_teachers: list[Teacher],
            student_group: str,
            activity_type: str,
            bk_remark: str,
            bk_text: str,
            flags: str,
            ls_number: int,
            ls_text: str,
            subst_text: str,
            period_type: str,
            period_id: int,
    ) -> None:
        self.start: datetime.datetime = start
        self.end: datetime.datetime = end
        self.subjects: list[Subject] = subjects
        self.raw_period_code: str | None = raw_period_code
        self.klassen: list[Class] = sorted(klassen, key=lambda k: k.name or '')
        self.rooms: list[Room] = sorted(rooms, key=lambda r: r.name or '')
        self.original_rooms: list[Room] = sorted(original_rooms, key=lambda r: r.name or '')
        self.teachers: list[Teacher] = sorted(teachers, key=lambda t: t.name or '')
        self.original_teachers: list[Teacher] = sorted(original_teachers, key=lambda t: t.name or '')
        self.student_group: str = student_group
        self.activity_type: str = activity_type
        self.bk_remark: str = bk_remark
        self.bk_text: str = bk_text
        self.flags: str = flags
        self.ls_number: int = ls_number
        self.ls_text: str = ls_text
        self.subst_text: str = subst_text
        self.period_type: str = period_type
        self.period_id: int = period_id

    def get_period_code(self, featuring_object: Class | Room | Teacher) -> tuple[str, tuple[bool, bool]]:
        # 'regular' / 'missed' / 'extra'
        period_code: str = 'regular'
        rows_changed: tuple[bool, bool] = (False, False)
        klasse_changed: bool = any(
            self.period_code_class(k) != 'regular' for k in self.klassen
        )
        room_changed: bool = any(
            self.period_code_room(r) != 'regular' for r in self.rooms + self.original_rooms
        )
        teacher_changed: bool = any(
            self.period_code_teacher(t) != 'regular' for t in self.teachers + self.original_teachers
        )

        if isinstance(featuring_object, Class):
            period_code = self.period_code_class(featuring_object)
            rows_changed = (teacher_changed, room_changed)
        elif isinstance(featuring_object, Room):
            period_code = self.period_code_room(featuring_object)
            rows_changed = (teacher_changed, klasse_changed)
        elif isinstance(featuring_object, Teacher):
            period_code = self.period_code_teacher(featuring_object)
            rows_changed = (room_changed, klasse_changed)

        return period_code, rows_changed

    def period_code_class(self, _klassen_object: Class) -> str:
        # Base it on the raw_period_code

        if self.raw_period_code is None or self.raw_period_code == 'regular':
            return 'regular'
        elif self.raw_period_code == 'cancelled':
            return 'missed'
        elif self.raw_period_code == 'irregular':
            return 'extra'
        return 'regular'

    def period_code_room(self, room_object: Room) -> str:
        # Regular: period.original_rooms = []
        # Missed: room_object in period.original_rooms and room_object not in period.rooms
        # Extra: room_object not in period.original_rooms and room_object in period.rooms

        if self.raw_period_code == 'cancelled':
            return 'missed'
        elif self.original_rooms == [] and room_object in self.rooms:
            if self.raw_period_code == 'irregular':
                return 'extra'
            else:
                return 'regular'
        elif room_object in self.original_rooms and room_object in self.rooms:
            return 'regular'
        elif room_object in self.original_rooms and room_object not in self.rooms:
            return 'missed'
        elif room_object not in self.original_rooms and room_object in self.rooms:
            return 'extra'
        return 'regular'

    def period_code_teacher(self, teacher_object: Teacher) -> str:
        # Regular: period.original_teachers = []
        # Missed: teacher_object in period.original_teachers and teacher_object not in period.teachers
        # Extra: teacher_object not in period.original_teachers and teacher_object in period.teachers

        if self.raw_period_code == 'cancelled':
            return 'missed'
        elif self.original_teachers == [] and teacher_object in self.teachers:
            if self.raw_period_code == 'irregular':
                return 'extra'
            else:
                return 'regular'
        elif teacher_object in self.original_teachers and teacher_object in self.teachers:
            return 'regular'
        elif teacher_object in self.original_teachers and teacher_object not in self.teachers:
            return 'missed'
        elif teacher_object not in self.original_teachers and teacher_object in self.teachers:
            return 'extra'
        return 'regular'

    def _subjects_str(self) -> str:
        subjects_str: str = ', '.join(subject.name for subject in self.subjects)
        if subjects_str == '':
            return my_config.html_style_config.unknown_element_symbol
        return subjects_str

    def _rooms_str(self, regular_plan: bool) -> str:
        rooms_str: str = ', '.join(room.name for room in self.rooms)
        original_rooms_str: str = ', '.join(room.name for room in self.original_rooms)

        if regular_plan and original_rooms_str:
            rooms_str = original_rooms_str

        if rooms_str == '':
            return my_config.html_style_config.unknown_element_symbol

        return rooms_str

    def _teachers_str(self, regular_plan: bool) -> str:
        teachers_str: str = ', '.join(map(lambda t: t.name, self.teachers))
        original_teachers_str: str = ', '.join(map(lambda t: t.name, self.original_teachers))

        if regular_plan and original_teachers_str:
            teachers_str = original_teachers_str

        if teachers_str == '':
            return my_config.html_style_config.unknown_element_symbol

        return teachers_str

    def _klassen_str(self) -> str:
        klassen_level_to_letter: dict[str, set[str]] = {}

        # Ex. 7a, 7b, 7c -> 7abc
        for klasse in self.klassen:
            klassen_level = klasse.name[0]
            klassen_letter = klasse.name[1:]
            if klassen_level not in klassen_level_to_letter:
                klassen_level_to_letter[klassen_level] = set(klassen_letter)
            klassen_level_to_letter[klassen_level].add(klassen_letter)

        klassen_str: str = ', '.join(sorted(
            f'{klassen_level}{"".join(sorted(klassen_level_to_letter[klassen_level]))}'
            for klassen_level in klassen_level_to_letter.keys()
        ))

        if klassen_str == '':
            return my_config.html_style_config.unknown_element_symbol

        return klassen_str

    def _formatted_list_class(self, regular_plan: bool) -> tuple[str, str, str, datetime.datetime, datetime.datetime]:
        return (
            self._subjects_str(),
            self._teachers_str(regular_plan),
            self._rooms_str(regular_plan),
            self.start,
            self.end
        )

    def _formatted_list_room(self, regular_plan: bool) -> tuple[str, str, str, datetime.datetime, datetime.datetime]:
        return (
            self._subjects_str(),
            self._teachers_str(regular_plan),
            self._klassen_str(),
            self.start,
            self.end
        )

    def _formatted_list_teacher(self, regular_plan: bool) -> tuple[str, str, str, datetime.datetime, datetime.datetime]:
        return (
            self._subjects_str(),
            self._rooms_str(regular_plan),
            self._klassen_str(),
            self.start,
            self.end
        )

    def formatted_list(
            self, featuring_object: Class | Room | Teacher, regular_plan: bool
    ) -> tuple[str, str, str, datetime.datetime, datetime.datetime]:
        if isinstance(featuring_object, Class):
            return self._formatted_list_class(regular_plan)
        elif isinstance(featuring_object, Room):
            return self._formatted_list_room(regular_plan)
        elif isinstance(featuring_object, Teacher):
            return self._formatted_list_teacher(regular_plan)
        return '', '', '', self.start, self.end

    def formatted_string(self, featuring_object: Class | Room | Teacher, regular_plan: bool) -> str:
        list_formatted: tuple[str, str, str, datetime.datetime, datetime.datetime] = (
            self.formatted_list(featuring_object, regular_plan)
        )
        return (
            f'{list_formatted[0]} {list_formatted[1]} {list_formatted[2]}'
        )

    def formatted_string_with_date_part(
            self,
            featuring_object: Class | Room | Teacher, regular_plan: bool
    ) -> str:
        list_formatted: tuple[str, str, str, datetime.datetime, datetime.datetime] = (
            self.formatted_list(featuring_object, regular_plan)
        )
        return (
            f'{list_formatted[0]} {list_formatted[1]} {list_formatted[2]}: '
            f'{list_formatted[3]} - {list_formatted[4]}'
        )

    def regular_plan_identifier(self) -> tuple[
        int, datetime.time, datetime.time, list[Subject], list[Class], list[Room], list[Teacher]
    ]:
        weekday: int = self.start.weekday()  # 0-indexed
        start_time: datetime.time = self.start.time()
        end_time: datetime.time = self.end.time()

        regular_rooms: list[Room] = self.rooms
        regular_teachers: list[Teacher] = self.teachers

        if self.original_rooms:
            regular_rooms = self.original_rooms

        if self.original_teachers:
            regular_teachers = self.original_teachers

        return weekday, start_time, end_time, self.subjects, self.klassen, regular_rooms, regular_teachers

    def __repr__(self) -> str:
        return (f'Period(start={self.start}, end={self.end}, subjects={self.subjects}, klassen={self.klassen},'
                f' rooms={self.rooms}, original_rooms={self.original_rooms}, teachers={self.teachers},'
                f' original_teachers={self.original_teachers})')

    def __str__(self) -> str:
        return repr(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Period):
            return NotImplemented
        return (
            self.start == other.start and
            self.end == other.end and
            self.subjects == other.subjects and
            self.raw_period_code == other.raw_period_code and
            self.klassen == other.klassen and
            self.rooms == other.rooms and
            self.original_rooms == other.original_rooms and
            self.teachers == other.teachers and
            self.original_teachers == other.original_teachers and
            self.student_group == other.student_group and
            self.activity_type == other.activity_type and
            self.bk_remark == other.bk_remark and
            self.bk_text == other.bk_text and
            self.flags == other.flags and
            self.ls_number == other.ls_number and
            self.ls_text == other.ls_text and
            self.subst_text == other.subst_text and
            self.period_type == other.period_type and
            self.period_id == other.period_id
        )

    def __hash__(self) -> int:
        return hash((
            self.start, self.end, self.subjects, self.raw_period_code, self.klassen, self.rooms, self.original_rooms,
            self.teachers, self.original_teachers, self.student_group, self.activity_type, self.bk_remark, self.bk_text,
            self.flags, self.ls_number, self.ls_text, self.subst_text, self.period_type, self.period_id
        ))

    @classmethod
    def from_dict(cls, data: dict[str, typing.Any]) -> typing.Self:
        """
        Construct a Period from a dictionary.
        Expected keys:
        raw_period_code, start, end, subjects, klassen, rooms, original_rooms,
        teachers, original_teachers, student_group, activity_type, bk_remark,
        bk_text, flags, ls_number, ls_text, subst_text, period_type, period_id
        """
        subjects = [Subject.from_dict(s) for s in data.get("subjects", [])]
        klassen = [Class.from_dict(k) for k in data.get("klassen", [])]
        rooms = [Room.from_dict(r) for r in data.get("rooms", [])]
        original_rooms = [Room.from_dict(r) for r in data.get("original_rooms", [])]
        teachers = [Teacher.from_dict(t) for t in data.get("teachers", [])]
        original_teachers = [Teacher.from_dict(t) for t in data.get("original_teachers", [])]

        return cls(
            raw_period_code=data.get("raw_period_code"),
            start=data["start"],
            end=data["end"],
            subjects=subjects,
            klassen=klassen,
            rooms=rooms,
            original_rooms=original_rooms,
            teachers=teachers,
            original_teachers=original_teachers,
            student_group=data.get("student_group", ""),
            activity_type=data.get("activity_type", ""),
            bk_remark=data.get("bk_remark", ""),
            bk_text=data.get("bk_text", ""),
            flags=data.get("flags", ""),
            ls_number=data.get("ls_number", 0),
            ls_text=data.get("ls_text", ""),
            subst_text=data.get("subst_text", ""),
            period_type=data.get("period_type", ""),
            period_id=data.get("period_id", 0)
        )


class TimeTable:
    def __init__(self, periods: list[Period]) -> None:
        self._periods: list[Period] = periods

    def copy_by_date_range(self, start_date: datetime.date, end_date: datetime.date) -> TimeTable:
        """Store any period that falls between start_date and end_date (return new TimeTable)"""
        new_periods: list[Period] = [
            p for p in self._periods if
            start_date <= p.start.date() <= end_date and start_date <= p.end.date() <= end_date
        ]
        return TimeTable(new_periods)

    def filter_hours_by_subject(self, subject: Subject) -> None:
        """Keep any period that stores that subject in the period (modify TimeTable in place)"""
        self._periods = [p for p in self._periods if subject in p.subjects]

    def filter_hours_by_class(self, klasse: Class) -> None:
        """Keep any period that stores that class in the period (modify TimeTable in place)"""
        self._periods = [p for p in self._periods if klasse in p.klassen]

    def filter_hours_by_room(self, room: Room) -> None:
        """Keep any period that stores that room in the period (modify TimeTable in place)"""
        self._periods = [p for p in self._periods if room in p.rooms + p.original_rooms]

    def filter_hours_by_teacher(self, teacher: Teacher) -> None:
        """Keep any period that stores that teacher in the period (modify TimeTable in place)"""
        self._periods = [p for p in self._periods if teacher in p.teachers + p.original_teachers]

    def filter_hours_by_personal(self, name: str) -> None:
        """Keep any period that personal attends (modify TimeTable in place)"""
        personal_teachers: set[str]
        personal_subjects: set[str]
        personal_teachers, personal_subjects = my_config.timetable_mapping_config.personal_timetable_entries.get(
            name, (set(), set())
        )
        self._periods = [
            p for p in self._periods
            if personal_teachers & {t.name for t in p.teachers + p.original_teachers}
            and personal_subjects & {s.name for s in p.subjects}
        ]

    @staticmethod
    def format_value(value: float, percent: bool, val_int: bool) -> str:
        base_string: str = f'{value:.2f}'.replace('.', ',')
        base_string_whole_number: str = f'{int(value)}'.replace('.', ',')

        if percent and val_int:
            return f'{base_string_whole_number}%'
        elif percent and not val_int:
            return f'{base_string}%'
        elif not percent and val_int:
            return base_string_whole_number
        return base_string

    def get_statistics(
            self,
            start_date: datetime.date,
            end_date: datetime.date,
            featuring_object: Class | Room | Teacher,
            filtered_class_objects: list[Class],
            filter_classes: bool,
            filtered_room_objects: list[Room],
            filter_rooms: bool,
            filtered_teacher_objects: list[Teacher],
            filter_teachers: bool
    ) -> tuple[int, int, int, int]:
        raw_hours_taught: dict[datetime.datetime, bool] = {}
        raw_hours_missed: dict[datetime.datetime, bool] = {}
        raw_hours_extra: dict[datetime.datetime, bool] = {}
        raw_hours_special_cases: dict[datetime.datetime, bool] = {}

        for period in self._periods:
            # In every filtered_..._object SOMETHING needs to match with that period for it to get counted

            if filter_classes:
                for klasse_object in period.klassen:
                    if klasse_object in filtered_class_objects:
                        break
                else:
                    continue  # Loop completes without a break; no klasse matches

            if filter_rooms:
                for room_object in period.rooms + period.original_rooms:
                    if room_object in filtered_room_objects:
                        break
                else:
                    continue

            if filter_teachers:
                for teacher_object in period.teachers + period.original_teachers:
                    if teacher_object in filtered_teacher_objects:
                        break
                else:
                    continue

            if (period.start.time() == datetime.time(hour=0, minute=0)
                    or period.end.time() == datetime.time(hour=23, minute=59)):
                raw_hours_special_cases[period.start] = True
            else:
                custom_period_code = period.get_period_code(featuring_object)
                if custom_period_code[0] == 'regular':
                    raw_hours_taught[period.start] = True
                elif custom_period_code[0] == 'extra':
                    raw_hours_extra[period.start] = True
                elif custom_period_code[0] == 'missed':
                    raw_hours_missed[period.start] = True

        dates_special_cases: list[datetime.date] = [
            dt.date()
            for dt, value in raw_hours_special_cases.items()
            if value and start_date <= dt.date() <= end_date
        ]

        hours_special_cases: int = sum(
            1
            for _ in dates_special_cases
        )

        hours_taught: int = sum(
            1
            for dt, value in raw_hours_taught.items()
            if value and start_date <= dt.date() <= end_date
            and dt.date() not in dates_special_cases
        )

        hours_missed: int = sum(
            1
            for dt, value in raw_hours_missed.items()
            if value and start_date <= dt.date() <= end_date
            and dt.date() not in dates_special_cases
        )

        hours_extra: int = sum(
            1
            for dt, value in raw_hours_extra.items()
            if value and start_date <= dt.date() <= end_date
            and dt.date() not in dates_special_cases
        )

        return hours_special_cases, hours_taught, hours_missed, hours_extra

    def get_separate_hours(
            self,
            start_date: datetime.date,
            end_date: datetime.date,
            featuring_object: Class | Room | Teacher,
            total_periods: int,
            filtered_class_objects: list[Class],
            filter_classes: bool,
            filtered_room_objects: list[Room],
            filter_rooms: bool,
            filtered_teacher_objects: list[Teacher],
            filter_teachers: bool,
            filter_unused_objects: bool
    ) -> list[str]:
        hours_special_cases, hours_taught, hours_missed, hours_extra = self.get_statistics(
            start_date, end_date, featuring_object, filtered_class_objects, filter_classes, filtered_room_objects,
            filter_rooms, filtered_teacher_objects, filter_teachers
        )

        hours_regular: int = hours_taught + hours_missed

        hours_taught_percent: str = '0,00%'
        hours_taught_extra_percent: str = '0,00%'
        hours_extra_per_regular: str = '0,00%'

        if hours_regular > 0:
            hours_taught_percent = self.format_value(
                hours_taught / hours_regular * 100, percent=True, val_int=False
            )
            hours_taught_extra_percent = self.format_value(
                (hours_taught + hours_extra) / hours_regular * 100, percent=True, val_int=False
            )
            hours_extra_per_regular = self.format_value(
                hours_extra / hours_regular * 100, percent=True, val_int=False
            )

        if (hours_taught + hours_missed + hours_extra + hours_special_cases + hours_regular) == 0:
            if filter_unused_objects:
                return []

        taught_all_percent: str = '0,00%'

        if total_periods > 0:
            taught_all_percent = self.format_value(
                ((hours_taught + hours_extra) / float(total_periods)) * 100, percent=True, val_int=False
            )

        return [
            str(hours_taught),
            str(hours_missed),
            str(hours_extra),
            str(hours_special_cases),
            str(taught_all_percent),
            hours_taught_percent,
            hours_taught_extra_percent,
            hours_extra_per_regular
        ]

    @staticmethod
    def get_table_name(
            featuring_object: Class | Room | Teacher,
            start_date: datetime.date,
            end_date: datetime.date
    ) -> tuple[str, str]:
        if isinstance(featuring_object, Class):
            return (
                f'{my_config.language_config.class_timetable} {featuring_object.name}',
                f'({start_date.strftime("%d.%m.%Y")} - {end_date.strftime("%d.%m.%Y")})'
            )
        elif isinstance(featuring_object, Room):
            return (
                f'{my_config.language_config.room_timetable} {featuring_object.name}',
                f'({start_date.strftime("%d.%m.%Y")} - {end_date.strftime("%d.%m.%Y")})'
            )
        elif isinstance(featuring_object, Teacher):
            return (
                f'{my_config.language_config.teacher_timetable} {featuring_object.name} ({featuring_object.long_name})',
                f'({start_date.strftime("%d.%m.%Y")} - {end_date.strftime("%d.%m.%Y")})'
            )
        return '', ''

    def unsorted_table(self) -> list[Period]:
        return self._periods

    def _to_table(self) -> list[tuple[datetime.time, list[tuple[datetime.date, list[Period]]]]]:
        """
        Heavily inspired by
        https://github.com/python-webuntis/python-webuntis/blob/master/webuntis/utils/timetable_utils.py
        """

        if not len(self._periods):
            return []

        times: set[datetime.time] = set(period.start.time() for period in self._periods)
        dates: set[datetime.date] = set(period.start.date() for period in self._periods)
        date_times: set[datetime.datetime] = set(datetime.datetime.combine(d, t) for d in dates for t in times)

        # Create an empty table from all possible combinations of dates and times
        time_table: dict[datetime.time, dict[datetime.date, list[Period]]] = (
            dict((t, dict((d, []) for d in dates)) for t in times)
        )

        # Add the periods to the table
        # Periods may be added twice if they are longer than one hour
        for period in self._periods:
            for dt in date_times:
                if period.start <= dt < period.end:
                    time_table[dt.time()][dt.date()].append(period)

        # Convert the hashtable to the output format by sorting each dictionary's .items() by key
        return sorted((time, sorted(row.items())) for time, row in time_table.items())

    def to_class_cancelled_hours(self) -> list[str]:
        cancelled_hours_one_time: dict[tuple[datetime.datetime, datetime.datetime], list[list[str]]] = {}

        for time, row in self._to_table():
            for _date, cell in row:
                for period in cell:
                    try:
                        long_subject_name: str = ', '.join(subject.long_name for subject in period.subjects)
                        room_name: str = ', '.join([room.name for room in period.rooms])
                        original_room_name: str = ', '.join([room.name for room in period.original_rooms])
                        teachers: str = ', '.join([teacher.name for teacher in period.teachers])
                        original_teachers: str = ', '.join([teacher.name for teacher in period.original_teachers])

                        if teachers == '':
                            teachers = f'[{my_config.language_config.unknown_element_extended_text}]'

                        if original_teachers == '':
                            original_teachers = teachers

                        if long_subject_name == '':
                            long_subject_name = my_config.language_config.some_hour

                        if room_name == '':
                            room_name = my_config.language_config.unknown_element_extended_text

                        if original_room_name == '':
                            original_room_name = room_name

                        times: tuple[datetime.datetime, datetime.datetime] = (period.start, period.end)

                        base_info: tuple[str, str] = (
                            f'{long_subject_name} ({room_name}, {teachers})', str(period.raw_period_code)
                        )
                        cancelled_info: str = (f'{long_subject_name} ({room_name}, {teachers})'
                                               f' {my_config.language_config.is_cancelled}: {period.start}')
                        irregular_info: str = (
                            f'{long_subject_name} ({original_room_name}, {original_teachers})'
                            f' -> {long_subject_name} ({room_name}, {teachers}) : {period.start}'
                        )

                        if period.raw_period_code in ['cancelled', 'irregular']:
                            if times in cancelled_hours_one_time:
                                cancelled_hours_one_time[times].append([*base_info, cancelled_info])
                            else:
                                cancelled_hours_one_time[times] = [[*base_info, cancelled_info]]
                        elif original_teachers != teachers or original_room_name != room_name:
                            if times in cancelled_hours_one_time:
                                cancelled_hours_one_time[times].append([*base_info, irregular_info])
                            else:
                                cancelled_hours_one_time[times] = [[*base_info, irregular_info]]
                    except Exception:
                        pass

        special_hours: list[str] = []

        for dates in cancelled_hours_one_time.keys():
            lesson_1_string: str = cancelled_hours_one_time[dates][0][0]
            lesson_1_code: str = cancelled_hours_one_time[dates][0][1]
            lesson_1_special_string: str = cancelled_hours_one_time[dates][0][2]
            lesson_2_string: str = ''
            lesson_2_code: str = ''
            if len(cancelled_hours_one_time[dates]) > 1:
                lesson_2_string = cancelled_hours_one_time[dates][1][0]
                lesson_2_code = cancelled_hours_one_time[dates][1][1]

            if len(cancelled_hours_one_time[dates]) == 1:  # 1 Hour / date
                if lesson_1_code == 'irregular':
                    special_hours.append(f'{lesson_1_string} {my_config.language_config.is_irregular}: {dates[0]}')
                else:
                    special_hours.append(lesson_1_special_string)

            elif len(cancelled_hours_one_time[dates]) == 2:  # 2 Hours / date
                if lesson_1_code == 'cancelled' and lesson_2_code == 'irregular':
                    special_hours.append(
                        f'{my_config.language_config.instead} {lesson_1_string}: {lesson_2_string}: {dates[0]}'
                    )
                elif lesson_2_code == 'cancelled' and lesson_1_code == 'irregular':
                    special_hours.append(
                        f'{my_config.language_config.instead} {lesson_2_string}: {lesson_1_string}: {dates[0]}'
                    )
                elif lesson_1_code == 'cancelled' and lesson_2_code == 'cancelled':
                    special_hours.append(
                        f'{lesson_1_string} & {lesson_2_string} {my_config.language_config.are_cancelled}: {dates[0]}'
                    )
                else:
                    special_hours.append(
                        f'{lesson_1_string} & {lesson_2_string} {my_config.language_config.are_irregular}: {dates[0]}'
                    )
            else:  # > 2 Hours / date
                all_cancelled: bool = all(
                    entry[1] != 'irregular'
                    for entry in cancelled_hours_one_time[dates]
                )

                if all_cancelled:
                    special_hours.append(
                        f'{my_config.language_config.multiple_lessons_cancelled}: {dates[0]}'
                    )
                else:
                    special_hours.append(
                        f'{my_config.language_config.multiple_lessons_irregular}: {dates[0]}'
                    )

        return special_hours

    def _html_setup(
            self,
            user_id: int,
            website: bool,
            table_name: tuple[str, str],
            start_date: datetime.date | None,
            end_date: datetime.date | None
    ) -> tuple[list[str], list[str], dict[str, dict[str, list[Period]]]]:
        """
        HTML header and final_hours

        :param user_id: User ID of the person who generated the picture (Needed for watermark, use sRGB to decode)
        :param website: Whether the image will be served to a website (-> Week buttons)
        :param table_name: Name of the table
        :param start_date: Date for start of timetable
        :param end_date: Date for end of timetable
        :return: HTML of the timetable
        """

        final_hours: dict[str, dict[str, list[Period]]] = {}

        for weekday in my_config.language_config.weekday_name_mapping.keys():
            if weekday in ['Saturday', 'Sunday']:
                continue
            if my_config.language_config.weekday_name_mapping[weekday] not in final_hours.keys():
                final_hours[my_config.language_config.weekday_name_mapping[weekday]] = {}
            for period in self._periods:
                if period.start.strftime('%A') != weekday:
                    continue

                # Actual start & end time, ex. 08:40 & 09:35, or irregular times: 00:00 & 23:59 (in one lesson)
                period_start_time: datetime.time = period.start.time()
                period_end_time: datetime.time = period.end.time()

                # Convert lesson time ranges to datetime ranges in tuple form
                time_lesson_ranges: list[tuple[datetime.time, datetime.time]] = [
                    (
                        datetime.datetime.strptime(
                            time_range.split(' - ')[0],
                            my_config.html_style_config.lesson_time_ranges_format
                        ).time(),
                        datetime.datetime.strptime(
                            time_range.split(' - ')[1],
                            my_config.html_style_config.lesson_time_ranges_format
                        ).time()
                    )
                    for time_range in my_config.html_style_config.lesson_time_ranges
                ]

                for i_start_time, i_end_time in time_lesson_ranges:
                    if period_start_time <= i_start_time <= period_end_time:
                        if period_start_time <= i_end_time <= period_end_time:
                            time: str = (
                                f'{i_start_time.strftime(
                                    my_config.html_style_config.lesson_time_ranges_format)} - {i_end_time.strftime(
                                        my_config.html_style_config.lesson_time_ranges_format)}'
                            )

                            if time in final_hours[my_config.language_config.weekday_name_mapping[weekday]].keys():
                                final_hours[my_config.language_config.weekday_name_mapping[weekday]][time].append(
                                    period
                                )
                            else:
                                final_hours[my_config.language_config.weekday_name_mapping[weekday]][time] = [period]

        weekdays: list[str] = [
            my_config.language_config.weekday_name_mapping[weekday]
            for weekday in my_config.language_config.weekday_name_mapping.keys()
            if weekday not in ['Saturday', 'Sunday']
        ]

        def bits4_to_signed_int(bits: str) -> int:
            """
            Convert a 4 char long string "bits" to signed integers

            :param bits: 4 char long string, ex. "1101" or "0101"
            :return Signed int
            """
            n: int = int(bits, 2)
            if bits[0] == '1':  # if sign bit is 1 → negative number
                n -= 1 << 4  # subtract 16 (2^4)
            return n

        water_mark_bits: str = bin(int(user_id))[2:].rjust(64, '0')
        base_rgb_value: tuple[int, int, int] = my_config.html_style_config.table_header_base_rgb

        # RGB changes:
        # Interpret as 4 bit signed int [-8; +7]
        # For better reading with rgb colour picker, *2 -> [-16; +14]

        water_mark_rgb_value: list[tuple[int, int, int]] = []

        # Handle the first 5 full RGB triplets
        for num_header in range(5):
            offset = num_header * 12
            rgb_red: int = bits4_to_signed_int(water_mark_bits[offset:offset + 4]) * 2 + base_rgb_value[0]
            rgb_green: int = bits4_to_signed_int(water_mark_bits[offset + 4:offset + 8]) * 2 + base_rgb_value[1]
            rgb_blue: int = bits4_to_signed_int(water_mark_bits[offset + 8:offset + 12]) * 2 + base_rgb_value[2]
            water_mark_rgb_value.append((rgb_red, rgb_green, rgb_blue))

        # Handle the last, special tuple
        rgb_red = bits4_to_signed_int(water_mark_bits[60:64]) * 2 + base_rgb_value[0]
        water_mark_rgb_value.append((rgb_red, base_rgb_value[1], base_rgb_value[2]))

        if website and start_date and end_date:
            html: list[str] = [
                my_config.html_style_config.timetable_html_header,
                '<p>',

                f'<a href="?date=0">'
                f'<button>{my_config.language_config.back}</button></a>',
                f'<br>',

                f'<a href="?date={(start_date - datetime.timedelta(weeks=1)).strftime("%d-%m-%Y")}">'
                f'<button>{my_config.language_config.last_week}</button></a>',

                f'{" ".join(table_name)}',

                f'<a href="?date={(start_date + datetime.timedelta(weeks=1)).strftime("%d-%m-%Y")}">'
                f'<button>{my_config.language_config.next_week}</button></a>',

                '</p>',
                '<table border="1" cellspacing="0" cellpadding="5">',
                f'<tr><th style="background-color: rgb{my_config.html_style_config.table_header_base_rgb};">'
                f'{my_config.language_config.time}</th>'
            ]

            for day in weekdays:
                html.append(f'<th style="background-color: rgb{my_config.html_style_config.table_header_base_rgb};">'
                            f'{day[:2]}</th>')
            html.append('</tr>')
        else:
            html = [
                my_config.html_style_config.timetable_html_header,
                f'<p>{" ".join(table_name)}</p>',
                '<table border="1" cellspacing="0" cellpadding="5">',
                f'<tr><th style="background-color: rgb{water_mark_rgb_value[0]};">{my_config.language_config.time}</th>'
            ]

            for count, day in enumerate(weekdays):
                html.append(f'<th style="background-color: rgb{water_mark_rgb_value[count + 1]};">{day[:2]}</th>')
            html.append('</tr>')

        return html, weekdays, final_hours

    @staticmethod
    def html_line_too_long(
        distinct_lessons_list_formatted: set[tuple[str, str, str, datetime.datetime, datetime.datetime]]
    ) -> bool:
        max_html_chars_per_row: int = 10

        chars_rows: list[int] = [0, 0, 0]

        # Maximum number of characters per row (3 total)
        for lesson in distinct_lessons_list_formatted:
            chars_rows[0] += len(lesson[0])
            chars_rows[1] += len('(') + len(lesson[1]) + len(')')
            chars_rows[2] += len('[') + len(lesson[2]) + len(']')

        # Do not use num lessons; len('NWP [PAM] (RBU1)') >> len('E [SU] [R6B]')

        if any(num_chars > max_html_chars_per_row for num_chars in chars_rows):
            return True
        return False

    @staticmethod
    def html_add_lesson_time_range(html: list[str], lesson_count_index: int, lesson_time_range: str) -> None:
        html.append(f"""
        <tr>
        <td style="padding: 0; margin: 0;">
            <div style="display: flex; align-items: center;">
                <!-- Big number spanning two lines -->
                <div style="font-size: 18pt; font-weight: bold; padding-right: 0pt; width: 30pt;">
                    {lesson_count_index + 1}
                </div>
                <!-- Time block -->
                <div style="line-height: 9pt;">
                    <div style="margin-bottom: 2pt;">{lesson_time_range.split(' - ')[0]}</div>
                    <div>{lesson_time_range.split(' - ')[1]}</div>
                </div>
            </div>
        </td>
        """)

    def to_html(
            self,
            featuring_object: Class | Room | Teacher,
            user_id: int,
            website: bool,
            table_name: tuple[str, str],
            start_date: datetime.date | None,
            end_date: datetime.date | None
    ) -> str:
        html: list[str]
        weekdays: list[str]
        final_hours: dict[str, dict[str, list[Period]]]
        html, weekdays, final_hours = self._html_setup(user_id, website, table_name, start_date, end_date)

        for count, time_range in enumerate(my_config.html_style_config.lesson_time_ranges):
            self.html_add_lesson_time_range(html, count, time_range)

            for day in weekdays:
                lessons: list[Period] = final_hours.get(day, {}).get(time_range, [])
                if not lessons:
                    html.append('<td></td>')
                    continue

                distinct_lessons_list_formatted: set[tuple[str, str, str, datetime.datetime, datetime.datetime]] = set()

                for lesson in lessons:
                    list_formatted: tuple[str, str, str, datetime.datetime, datetime.datetime] = (
                        lesson.formatted_list(featuring_object, False)
                    )
                    if list_formatted not in distinct_lessons_list_formatted:
                        distinct_lessons_list_formatted.add(list_formatted)

                formatted_lessons: list[str] = []
                seen_lesson_strings: set[str] = set()
                character_limit_before_line_break: int = 8
                total_character: int = 0

                for lesson in lessons:
                    lesson_code: str
                    rows_changed: tuple[bool, bool]
                    lesson_code, rows_changed = lesson.get_period_code(featuring_object)

                    list_formatted = lesson.formatted_list(featuring_object, False)
                    string_formatted = lesson.formatted_string(featuring_object, False)

                    text_color: str = ''

                    if lesson_code == 'missed':
                        text_color = 'color: #D32F2F;'
                    elif lesson_code == 'extra':
                        text_color = 'color: #2E7D32;'

                    short_subject_name_text_color: str = text_color
                    if rows_changed[0] or rows_changed[1]:
                        if text_color == '':
                            short_subject_name_text_color = 'color: #F9A825;'

                    formatted_lesson: str = '<br>'.join([
                        f'<span>{list_formatted[0]}</span>',

                        f'<span{" style= \"color: #F9A825;\" " if rows_changed[0] and lesson_code == 'regular' else ""}'
                        f'>[{list_formatted[1]}]</span>',

                        f'<span{" style= \"color: #F9A825;\" " if rows_changed[1] and lesson_code == 'regular' else ""}'
                        f'>({list_formatted[2]})</span>'
                    ])

                    # Render lesson
                    if len(lessons) == 1:
                        formatted_lessons.append(
                            f'<span style="display:inline-block; margin-right:5px; vertical-align: top;'
                            f' margin-left:5px; {text_color}">{formatted_lesson}</span>'
                        )
                    else:
                        if string_formatted in seen_lesson_strings:
                            continue
                        seen_lesson_strings.add(string_formatted)

                        if website:
                            if len(distinct_lessons_list_formatted) < 5:  # Num lessons
                                formatted_lessons.append(
                                    f'<span style="display:inline-block; margin-right:1px; vertical-align: top;'
                                    f' margin-left:1px; {text_color}">{formatted_lesson}</span>'
                                )
                            else:
                                formatted_lessons.append(
                                    f'<span style="display:inline-block; margin-right:5px; vertical-align: top;'
                                    f' margin-left:5px; {text_color}">{list_formatted[0]}</span>'
                                )
                        else:
                            if not self.html_line_too_long(distinct_lessons_list_formatted):
                                formatted_lessons.append(
                                    f'<span style="display:inline-block; margin-right:1px; vertical-align: top;'
                                    f' margin-left:1px; {text_color}">{formatted_lesson}</span>'
                                )
                            else:
                                # Display only subject name
                                # Make sure they don't go out of border

                                total_character += len(list_formatted[0]) + len(' ')
                                remainder: int = total_character % character_limit_before_line_break

                                # If after those characters, it would be too long -> <br>
                                if total_character >= character_limit_before_line_break and remainder:
                                    formatted_lessons.append('<br>')

                                formatted_lessons.append(
                                    f'<span style="display:inline-block; margin-right:5px; vertical-align: top;'
                                    f' margin-left:5px; {short_subject_name_text_color}">{list_formatted[0]}</span>'
                                )
                # Stripe colour (based on first eligible subject / fallback to first subject)
                rgba_value: tuple[int, int, int] = (255, 255, 255)

                # Collect eligible subjects (None or irregular)
                eligible_subjects: list[Subject] = []

                for lesson in lessons:
                    if lesson.get_period_code(featuring_object)[0] not in ('regular', 'extra'):
                        continue
                    if not lesson.subjects:
                        continue
                    subject_object: Subject = lesson.subjects[0]
                    eligible_subjects.append(subject_object)

                # Pick first alphabetical eligible subject
                if eligible_subjects:
                    eligible_subjects.sort(key=lambda item: item.name)
                    chosen_subject: Subject | None = eligible_subjects[0]
                else:
                    try:
                        chosen_subject = lessons[0].subjects[0]
                    except IndexError:
                        chosen_subject = None

                if chosen_subject:
                    rgba_value = chosen_subject.color

                html.append(
                    f'<td style="--stripe-color: rgba{rgba_value}; white-space: nowrap;">'
                    f'{"".join(formatted_lessons)}</td>'
                )
            html.append('</tr>')

        html.append('</table>')

        html.append(my_config.html_style_config.timetable_html_footer)

        html_content = '\n'.join(html)

        return html_content

    def to_untis_html(
            self,
            featuring_object: Class | Room | Teacher,
            user_id: int,
            table_name: tuple[str, str],
            start_date: datetime.date,
            end_date: datetime.date
    ) -> str:
        return self.to_html(featuring_object, user_id, False, table_name, start_date, end_date)

    def to_website_html(
            self,
            featuring_object: Class | Room | Teacher,
            start_date: datetime.date,
            end_date: datetime.date
    ) -> str:
        table_name: tuple[str, str] = self.get_table_name(featuring_object, start_date, end_date)
        return self.to_html(featuring_object, 0, True, table_name, start_date, end_date)

    def to_personal_html(
            self,
            featuring_object: Class | Room | Teacher,
            target_date: datetime.date,
            person_name: str
    ) -> str:
        english_weekday: str = target_date.strftime("%A")
        german_weekday: str = my_config.language_config.weekday_name_mapping[english_weekday]

        # Initialise final_hours with german_weekday key!
        final_hours: dict[str, dict[str, list[Period]]] = {german_weekday: {}}

        for period in self._periods:
            if period.start.strftime('%A') != english_weekday:
                continue

            # Actual start & end time, ex. 08:40 & 09:35, or irregular times: 00:00 & 23:59 (in one lesson)
            period_start_time: datetime.time = period.start.time()
            period_end_time: datetime.time = period.end.time()

            # Convert lesson time ranges to datetime ranges in tuple form
            time_lesson_ranges: list[tuple[datetime.time, datetime.time]] = [
                (
                    datetime.datetime.strptime(time_range.split(' - ')[0],
                                               my_config.html_style_config.lesson_time_ranges_format).time(),
                    datetime.datetime.strptime(time_range.split(' - ')[1],
                                               my_config.html_style_config.lesson_time_ranges_format).time()
                )
                for time_range in my_config.html_style_config.lesson_time_ranges
            ]

            for i_start_time, i_end_time in time_lesson_ranges:
                if period_start_time <= i_start_time <= period_end_time:
                    if period_start_time <= i_end_time <= period_end_time:
                        time: str = (
                            f'{i_start_time.strftime(my_config.html_style_config.lesson_time_ranges_format)} - '
                            f'{i_end_time.strftime(my_config.html_style_config.lesson_time_ranges_format)}'
                        )

                        if time in final_hours[german_weekday].keys():
                            final_hours[german_weekday][time].append(period)
                        else:
                            final_hours[german_weekday][time] = [period]

        rgb_value: tuple[int, int, int] = my_config.html_style_config.table_header_base_rgb

        if target_date == datetime.date.today():
            rgb_value = my_config.html_style_config.today_personal_rgb_value

        html: list[str] = [
            my_config.html_style_config.personal_timetable_html_header,
            '<p>',

            f'<a href="?date={(target_date - datetime.timedelta(days=1)).strftime("%d-%m-%Y")}">'
            f'<button>{my_config.language_config.yesterday}</button></a>',

            f'{my_config.language_config.personal_timetable} {person_name} ({target_date.strftime("%d.%m.%Y")})',

            f'<a href="?date={(target_date + datetime.timedelta(days=1)).strftime("%d-%m-%Y")}">'
            f'<button>{my_config.language_config.tomorrow}</button></a>',

            '</p>',
            '<p>',

            f'<a href="?date={(datetime.datetime.today()).strftime("%d-%m-%Y")}">'
            f'<button>{my_config.language_config.today}</button></a>',

            '</p>',
            '<table border="1" cellspacing="0" cellpadding="5">',
            f'<tr><th style="background-color: rgb{my_config.html_style_config.table_header_base_rgb};">'
            f'{my_config.language_config.time}</th>',
            f'<th style="background-color: rgb{rgb_value};">{german_weekday[:2]}</th>',
            '<tr>'
        ]

        for count, time_range in enumerate(my_config.html_style_config.lesson_time_ranges):
            self.html_add_lesson_time_range(html, count, time_range)

            lessons: list[Period] = final_hours.get(german_weekday, {}).get(time_range, [])
            if not lessons:
                html.append('<td></td>')
                continue

            distinct_lessons_list_formatted: set[tuple[str, str, str, datetime.datetime, datetime.datetime]] = set()

            for lesson in lessons:
                list_formatted: tuple[str, str, str, datetime.datetime, datetime.datetime] = (
                    lesson.formatted_list(featuring_object, False)
                )
                if list_formatted not in distinct_lessons_list_formatted:
                    distinct_lessons_list_formatted.add(list_formatted)

            formatted_lessons: list[str] = []
            seen_lesson_strings: set[str] = set()

            for lesson in lessons:
                lesson_code: str
                rows_changed: tuple[bool, bool]
                lesson_code, rows_changed = lesson.get_period_code(featuring_object)

                list_formatted = lesson.formatted_list(featuring_object, False)
                string_formatted = lesson.formatted_string(featuring_object, False)

                text_color: str = ''

                if lesson_code == 'missed':
                    text_color = 'color: #D32F2F;'
                elif lesson_code == 'extra':
                    text_color = 'color: #2E7D32;'

                short_subject_name_text_color: str = text_color
                if rows_changed[0] or rows_changed[1]:
                    if text_color == '':
                        short_subject_name_text_color = 'color: #F9A825;'

                formatted_lesson: str = '<br>'.join([
                    f'<span>{list_formatted[0]}</span>',

                    f'<span{" style= \"color: #F9A825;\" " if rows_changed[0] and lesson_code == 'regular' else ""}'
                    f'>[{list_formatted[1]}]</span>',

                    f'<span{" style= \"color: #F9A825;\" " if rows_changed[1] and lesson_code == 'regular' else ""}'
                    f'>({list_formatted[2]})</span>'
                ])

                # Render lesson
                if len(lessons) == 1:
                    formatted_lessons.append(
                        f'<span style="display:inline-block; margin-right:5px; vertical-align: top;'
                        f' margin-left:5px; {text_color}">{formatted_lesson}</span>'
                    )
                else:
                    if string_formatted in seen_lesson_strings:
                        continue
                    seen_lesson_strings.add(string_formatted)

                    if len(distinct_lessons_list_formatted) < 5:  # Num lessons
                        formatted_lessons.append(
                            f'<span style="display:inline-block; margin-right:1px; vertical-align: top;'
                            f' margin-left:1px; {text_color}">{formatted_lesson}</span>'
                        )
                    else:
                        formatted_lessons.append(
                            f'<span style="display:inline-block; margin-right:5px; vertical-align: top;'
                            f' margin-left:5px; {short_subject_name_text_color}">{list_formatted[0]}</span>'
                        )

            # Stripe colour (based on first eligible subject / fallback to first subject)
            rgba_value: tuple[int, int, int] = (255, 255, 255)

            # Collect eligible subjects (None or irregular)
            eligible_subjects: list[Subject] = []

            for lesson in lessons:
                if lesson.get_period_code(featuring_object)[0] not in ('regular', 'extra'):
                    continue
                if not lesson.subjects:
                    continue
                subject_object: Subject = lesson.subjects[0]
                eligible_subjects.append(subject_object)

            # Pick first alphabetical eligible subject
            if eligible_subjects:
                eligible_subjects.sort(key=lambda item: item.name)
                chosen_subject: Subject | None = eligible_subjects[0]
            else:
                try:
                    chosen_subject = lessons[0].subjects[0]
                except IndexError:
                    chosen_subject = None

            if chosen_subject:
                rgba_value = chosen_subject.color

            html.append(
                f'<td style="--stripe-color: rgba{rgba_value}; white-space: nowrap;">'
                f'{"".join(formatted_lessons)}</td>'
            )
            html.append('</tr>')

        html.append('</table>')

        html.append(my_config.html_style_config.personal_timetable_html_footer)

        html_content = '\n'.join(html)

        return html_content

    def to_regular_html(
            self,
            featuring_object: Class | Room | Teacher,
            user_id: int,
            table_name: tuple[str, str]
    ) -> str:
        html: list[str]
        weekdays: list[str]
        final_hours: dict[str, dict[str, list[Period]]]
        html, weekdays, final_hours = self._html_setup(user_id, False, table_name, None, None)

        any_two_week_lesson: bool = False

        for count, time_range in enumerate(my_config.html_style_config.lesson_time_ranges):
            self.html_add_lesson_time_range(html, count, time_range)

            for day in weekdays:
                raw_lessons: list[Period] = final_hours.get(day, {}).get(time_range, [])

                filtered_lessons: list[Period] = [
                    lesson for lesson in raw_lessons if lesson.get_period_code(featuring_object)[0] != 'extra'
                ]

                if not filtered_lessons:
                    html.append('<td></td>')
                    continue

                distinct_lessons_list_formatted: set[tuple[str, str, str, datetime.datetime, datetime.datetime]] = set()
                distinct_lessons_string: set[str] = set()

                for lesson in filtered_lessons:
                    list_formatted: tuple[str, str, str, datetime.datetime, datetime.datetime] = (
                        lesson.formatted_list(featuring_object, False)
                    )
                    formatted_lesson: str = '<br>'.join([
                        f'<span>{list_formatted[0]}</span>',
                        f'<span>[{list_formatted[1]}]</span>',
                        f'<span>({list_formatted[2]})</span>'
                    ])

                    if formatted_lesson not in distinct_lessons_string:
                        distinct_lessons_list_formatted.add(list_formatted)
                        distinct_lessons_string.add(formatted_lesson)

                formatted_lessons: list[str] = []
                seen_formatted_lessons: set[str] = set()
                character_limit_before_line_break: int = 8
                total_character: int = 0

                for lesson in filtered_lessons:
                    lesson_code: str
                    lesson_code, _ = lesson.get_period_code(featuring_object)

                    list_formatted = lesson.formatted_list(featuring_object, True)

                    if lesson_code == 'extra':
                        continue

                    formatted_lesson = '<br>'.join([
                        f'<span>{list_formatted[0]}</span>',
                        f'<span>[{list_formatted[1]}]</span>',
                        f'<span>({list_formatted[2]})</span>'
                    ])

                    this_lesson_bi_weekly: str = ''

                    # Bi-weekly check
                    if self.count_appearances(lesson) == 1:
                        this_lesson_bi_weekly = f'{my_config.language_config.two_week_abbreviation}<br>'
                        any_two_week_lesson = True

                    # Render lesson
                    if len(filtered_lessons) == 1:  # 1 Lesson / block (-> bi-weekly, but irrelevant)
                        formatted_lessons.append(
                            f'<span style="display:inline-block; margin-right:5px; vertical-align: top;'
                            f' margin-left:5px;">{this_lesson_bi_weekly}{formatted_lesson}</span>'
                        )
                    else:
                        # Could still contain bi-weekly lessons; If multiple lessons are in the same block

                        if formatted_lesson in seen_formatted_lessons:
                            continue
                        seen_formatted_lessons.add(formatted_lesson)

                        if not self.html_line_too_long(distinct_lessons_list_formatted):
                            formatted_lessons.append(
                                f'<span style="display:inline-block; margin-right:1px; vertical-align: top;'
                                f' margin-left:1px;">{this_lesson_bi_weekly}{formatted_lesson}</span>'
                            )
                        else:
                            # Display only subject name
                            # Make sure they don't go out of border

                            total_character += len(list_formatted[0]) + len(' ')
                            remainder: int = total_character % character_limit_before_line_break

                            # If after those characters, it would be too long -> <br>
                            if total_character >= character_limit_before_line_break and remainder:
                                formatted_lessons.append('<br>')

                            formatted_lessons.append(
                                f'<span style="display:inline-block; margin-right:5px; vertical-align: top;'
                                f' margin-left:5px;">{this_lesson_bi_weekly}{list_formatted[0]}</span>'
                            )

                # Stripe colour (based on first eligible subject / fallback to first subject)
                rgba_value: tuple[int, int, int] = (255, 255, 255)

                # Collect eligible subjects (None or irregular)
                eligible_subjects: list[Subject] = []

                for lesson in filtered_lessons:
                    if lesson.get_period_code(featuring_object)[0] == 'extra':
                        continue

                    if not lesson.subjects:
                        continue

                    subject_object: Subject = lesson.subjects[0]
                    eligible_subjects.append(subject_object)

                # Pick first alphabetical eligible subject
                if eligible_subjects:
                    eligible_subjects.sort(key=lambda item: item.name)
                    chosen_subject: Subject | None = eligible_subjects[0]
                else:
                    try:
                        chosen_subject = filtered_lessons[0].subjects[0]
                    except IndexError:
                        chosen_subject = None

                if chosen_subject:
                    rgba_value = chosen_subject.color

                html.append(
                    f'<td style="--stripe-color: rgba{rgba_value}; white-space: nowrap;">'
                    f'{"".join(formatted_lessons)}</td>'
                )
            html.append('</tr>')

        html.append('</table>')

        if any_two_week_lesson:
            html.append(my_config.html_style_config.timetable_html_footer_two_week)

        html.append(my_config.html_style_config.timetable_html_footer)

        html_content = '\n'.join(html)

        return html_content

    @staticmethod
    async def _render_one_image_by_html(
            semaphore: asyncio.Semaphore,
            browser: playwright.async_api.Browser,
            results: dict[str, bytes],
            table_name: tuple[str, str],
            html_content: str
    ) -> None:
        async with semaphore:
            # Convert mm to pixels (96dpi)
            width_mm: int
            height_mm: int
            margin_mm: int
            px_per_mm: float

            width_mm, height_mm, margin_mm, px_per_mm = 140, 200, 100, 3.78
            width_px: int = round(int(width_mm * px_per_mm) * 1)
            height_px: int = round(int(height_mm * px_per_mm) * 1)

            page = await browser.new_page(
                viewport=playwright.async_api.ViewportSize(width=width_px, height=height_px),
                device_scale_factor=3
            )

            await page.set_content(html_content)
            img_bytes: bytes = await page.screenshot(full_page=True)
            await page.close()

            sanitized_file_name: str = re.sub(
                r'[^A-Za-z0-9\-_. ]+',
                '_',
                f'{" ".join(table_name)}.png'
            )

            results[sanitized_file_name] = img_bytes

    @staticmethod
    async def capture_image_by_html(
            concurrency_website_capture: int, table_name: tuple[str, str], html_content: str
    ) -> io.BytesIO:
        semaphore: asyncio.Semaphore = asyncio.Semaphore(concurrency_website_capture)
        results: dict[str, bytes] = {}

        async with playwright.async_api.async_playwright() as p:
            browser: playwright.async_api.Browser = await p.chromium.launch()

            await TimeTable._render_one_image_by_html(semaphore, browser, results, table_name, html_content)

            await browser.close()

        image_stream: io.BytesIO = io.BytesIO(list(results.values())[0])
        image_stream.name = ' '.join(table_name)
        return image_stream

    @staticmethod
    async def capture_all_images(
            concurrency_website_capture: int, pages: list[tuple[tuple[str, str], str]]
    ) -> dict[str, bytes]:
        semaphore: asyncio.Semaphore = asyncio.Semaphore(concurrency_website_capture)
        results: dict[str, bytes] = {}

        async with playwright.async_api.async_playwright() as p:
            browser: playwright.async_api.Browser = await p.chromium.launch()

            await asyncio.gather(*[
                TimeTable._render_one_image_by_html(semaphore, browser, results, table_name, html_content)
                for table_name, html_content in pages
            ])

            await browser.close()

        return results

    async def table_to_image(
            self,
            concurrency_website_capture: int,
            featuring_object: Class | Room | Teacher,
            user_id: int,
            start_date: datetime.date,
            end_date: datetime.date
    ) -> io.BytesIO:
        table_name: tuple[str, str] = self.get_table_name(featuring_object, start_date, end_date)
        html_content: str = self.to_untis_html(featuring_object, user_id, table_name, start_date, end_date)

        return await self.capture_image_by_html(concurrency_website_capture, table_name, html_content)

    def count_appearances(self, period_to_count: Period) -> int:
        appearances: int = 0
        distinct_periods: list[Period] = []

        for period in self._periods:
            # If it's an **exact match**, the date hour etc. match -> continue
            if period in distinct_periods:
                continue
            distinct_periods.append(period)

            # If the regular identifier is the same, appearances += 1
            if period_to_count.regular_plan_identifier() == period.regular_plan_identifier():
                appearances += 1

        return appearances

    def __len__(self) -> int:
        return len(self._periods)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TimeTable):
            return NotImplemented
        return self._periods == other._periods

    def __add__(self, other: 'TimeTable') -> 'TimeTable':
        if not isinstance(other, TimeTable):
            return NotImplemented
        return TimeTable(self._periods + other._periods)

    def __repr__(self) -> str:
        return '\n'.join(str(period) for period in self._periods)

    def __str__(self) -> str:
        return repr(self)


class Session:
    def __init__(
            self, session_name: str, use_cache: bool, cache_file: str | None, logger: 'Logger | None',
            username: str, password: str, server: str, school: str, client: str
    ) -> None:
        self._username: str = username
        self._password: str = password

        # Clean up the server URL
        if not server.startswith('http'):
            server = f'https://{server}'
        self._server: str = server.rstrip('/')

        self._school: str = school
        self._client: str = client

        # Internal session tracking
        self._jsessionid: str | None = None
        self._person_type: int | None = None
        self._person_id: int | None = None
        self._klasse_id: int | None = None

        self._active_session_uuids: set[typing.Any] = set()
        self._session_name: str = session_name
        self._cache: dict[typing.Any, typing.Any] = {}
        self._use_cache: bool = use_cache
        self._cache_file_path: pathlib.Path | None = None
        self._my_logger: 'Logger' = logger or Logger()

        if cache_file is not None:
            self._cache_file_path = pathlib.Path(cache_file)

    @staticmethod
    def get_unique_uuid() -> uuid.UUID:
        return uuid.uuid4()

    # ------------------------------------------------------------------
    # Core JSON-RPC Mechanism
    # ------------------------------------------------------------------

    def _rpc_request(
            self, method: str, params: dict[str, typing.Any] | None = None, retry_on_authentication_error: bool = True,
    ) -> typing.Any:
        if params is None:
            params = {}

        payload = {
            "id": str(uuid.uuid4()),
            "method": method,
            "params": params,
            "jsonrpc": "2.0"
        }

        url = f"{self._server}/jsonrpc.do?school={self._school}"
        cookies = {"JSESSIONID": self._jsessionid} if self._jsessionid else None

        r = requests.post(url, json=payload, cookies=cookies)
        r.raise_for_status()

        data = r.json()
        if "error" in data:
            if data["error"].get("message") == "not authenticated":
                self._my_logger.log_warning(f"WebUntis API NotAuthenticatedError ({method}): {data['error']}")
                if retry_on_authentication_error:
                    self._my_logger.log_debug("Logging in & retrying Authentication...")
                    call_id: uuid.UUID = self.get_unique_uuid()
                    self.log_in(call_id)
                    result = self._rpc_request(method, params, retry_on_authentication_error=False)
                    self.log_out(call_id)
                    return result
                else:
                    raise NotAuthenticatedError(data["error"])
            elif "no right for " in data["error"].get("message"):
                raise NoRightForMethod(data["error"], method)
            elif "Method not found" in data["error"].get("message"):
                raise MethodNotFound(data["error"], method)
            raise RuntimeError(f"WebUntis API Error ({method}): {data['error']}")

        return data.get("result")

    @staticmethod
    def _format_date(d: datetime.date) -> int:
        return int(d.strftime("%Y%m%d"))

    @staticmethod
    def _parse_date(d: int) -> datetime.date:
        d_str = str(d)
        return datetime.date(year=int(d_str[:4]), month=int(d_str[4:6]), day=int(d_str[6:]))

    @staticmethod
    def _parse_time(t: int) -> datetime.time:
        t_str = str(t).zfill(4)
        return datetime.time(hour=int(t_str[:2]), minute=int(t_str[2:]))

    def _create_date_param(
            self, start: datetime.date, end: datetime.date, **kwargs: typing.Any
    ) -> dict[str, typing.Any]:
        if start > end:
            raise ValueError("Start date cannot be later than end date.")
        params = {
            "startDate": self._format_date(start),
            "endDate": self._format_date(end)
        }
        params.update(kwargs)
        return params

    # ------------------------------------------------------------------
    # Authentication Lifecycle
    # ------------------------------------------------------------------

    def log_in(self, unique_uuid: uuid.UUID) -> None:
        if not self._active_session_uuids:
            params = {
                "user": self._username,
                "password": self._password,
                "client": self._client
            }

            # Use raw request for login to catch the session ID
            payload = {
                "id": str(uuid.uuid4()),
                "method": "authenticate",
                "params": params,
                "jsonrpc": "2.0"
            }
            url = f"{self._server}/jsonrpc.do?school={self._school}"

            r = requests.post(url, json=payload)
            r.raise_for_status()
            data = r.json()

            if "error" in data:
                raise RuntimeError(f"Login failed: {data['error']}")

            result = data["result"]
            self._jsessionid = result.get("sessionId")
            self._person_type = result.get("personType")
            self._person_id = result.get("personId")
            self._klasse_id = result.get("klasseId")

            self._my_logger.log_info(f"Logged in ({self._session_name})!")

        self._active_session_uuids.add(unique_uuid)

    def log_out(self, unique_uuid: uuid.UUID) -> None:
        self._active_session_uuids.discard(unique_uuid)
        if not self._active_session_uuids and self._jsessionid:
            try:
                self._rpc_request("logout")
            except Exception:
                pass
            self._jsessionid = None
            self._my_logger.log_info(f"Logged out ({self._session_name})!")

    # ------------------------------------------------------------------
    # Caching Mechanism
    # ------------------------------------------------------------------

    def cache_file_last_changed(self) -> float | None:
        if self._cache_file_path is None:
            return None
        try:
            return (datetime.datetime.now() - datetime.datetime.fromtimestamp(
                self._cache_file_path.stat().st_mtime
            )).total_seconds()
        except FileNotFoundError:
            return None

    def get_from_cache(self, cid: typing.Any) -> typing.Any:
        if not self._use_cache:
            return None
        return self._cache.get(cid)

    def update_cache(self, cid: typing.Any, result: typing.Any) -> None:
        if not self._use_cache:
            return
        self._cache[cid] = result

    def clear_cache(self) -> None:
        self._my_logger.log_debug("Clearing cache (from memory)")
        self._cache.clear()

    def read_cache_from_file(self) -> None:
        if not self._cache_file_path:
            return
        self._my_logger.log_debug(f'Reading cache from "{self._cache_file_path.resolve()}"')
        try:
            with open(self._cache_file_path, "rb") as f:
                self._cache = pickle.load(f)
        except (FileNotFoundError, IOError, EOFError):
            self._my_logger.log_error(f'File "{self._cache_file_path.resolve()}" not found.')
            self._cache = {}

    def write_cache_to_file(self) -> None:
        if not self._cache_file_path:
            return
        self._my_logger.log_debug(f'Writing cache to "{self._cache_file_path.resolve()}"')
        try:
            with open(self._cache_file_path, 'wb') as f:
                pickle.dump(self._cache, f, protocol=pickle.HIGHEST_PROTOCOL)
        except FileNotFoundError:
            self._my_logger.log_error(f'File "{self._cache_file_path.resolve()}" not found.')

    @staticmethod
    def cached_method(func: typing.Any) -> typing.Any:
        @functools.wraps(func)
        def wrapper(self: typing.Any, *args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            cid = (func.__qualname__, args, tuple(sorted(kwargs.items())))
            if self._use_cache and (cached := self._cache.get(cid)) is not None:
                return cached
            result = func(self, *args, **kwargs)
            if self._use_cache:
                self._cache[cid] = result
            return result

        return wrapper

    # ------------------------------------------------------------------
    # Custom Object Parsers
    # ------------------------------------------------------------------

    @cached_method
    def all_klassen(self) -> list[Class]:
        raw_json = self._rpc_request("getKlassen")
        return [Class.from_dict({
            'name': c.get('name', ''),
            'longName': c.get('longName', ''),
            'id': c.get('id', 0)
        }) for c in raw_json]

    @cached_method
    def all_rooms(self) -> list[Room]:
        raw_json = self._rpc_request("getRooms")
        return [Room.from_dict({
            'name': r.get('name', ''),
            'longName': r.get('longName', ''),
            'id': r.get('id', 0)
        }) for r in raw_json]

    @cached_method
    def all_subjects(self) -> list[Subject]:
        raw_json = self._rpc_request("getSubjects")
        # Technically we are destroying info here, "alternateName" & "active"
        return [Subject.from_dict({
            'name': s.get('name', ''),
            'longName': s.get('longName', ''),
            'id': s.get('id', 0)
        }) for s in raw_json]

    @cached_method
    def all_departments(self) -> list[Department]:
        raw_json = self._rpc_request("getDepartments")
        return [Department.from_dict({
            'name': d.get('name', ''),
            'longName': d.get('longName', ''),
            'id': d.get('id', 0)
        }) for d in raw_json]

    @cached_method
    def all_holidays(self) -> list[Holiday]:
        raw_json = self._rpc_request("getHolidays")
        return [Holiday.from_dict({
            'name': h.get('name', ''),
            'longName': h.get('longName', ''),
            'id': h.get('id', 0),
            'startDate': h.get('startDate', None),
            'endDate': h.get('endDate', None)
        }) for h in raw_json]

    @cached_method
    def all_schoolyears(self) -> list[SchoolYear]:
        raw_json = typing.cast(list[dict[str, typing.Any]], self._rpc_request("getSchoolyears"))
        return [SchoolYear.from_dict({
            'name': s.get('name', ''),
            'longName': s.get('name', ''),
            'id': s.get('id', 0),
            'startDate': s.get('startDate', None),
            'endDate': s.get('endDate', None)
        }) for s in raw_json]

    def return_current_year(self) -> SchoolYear:
        years: list[SchoolYear] = self.all_schoolyears()
        if not years:
            raise RuntimeError("No school years found")
        # Assuming the last year in the list or highest ID is current
        return sorted(years, key=lambda y: y.id)[-1]

    @cached_method
    def get_klasse_by_name(self, name: str) -> Class | None:
        for k in self.all_klassen():
            if k.name == name:
                return typing.cast(Class, k)
        return None

    @cached_method
    def get_room_by_name(self, name: str) -> Room | None:
        for r in self.all_rooms():
            if r.name == name:
                return typing.cast(Room, r)
        return None

    @cached_method
    def get_teacher_by_name(self, name: str) -> Teacher | None:
        try:
            return Teacher.from_teacher_name(name)
        except Exception:
            return None

    @cached_method
    def get_teacher_by_long_name(self, long_name: str) -> Teacher | None:
        try:
            return Teacher.from_teacher_long_name(long_name)
        except Exception:
            return None

    @cached_method
    def timetable_extended(
            self,
            klasse: Class,
            start: datetime.date,
            end: datetime.date
    ) -> TimeTable:
        options = {
            "startDate": self._format_date(start),
            "endDate": self._format_date(end),
            "element": {"id": klasse.entity_id, "type": 1},
            "showBooking": True,
            "showInfo": True,
            "showSubstText": True,
            "showLsText": True,
            "showLsNumber": True,
            "showStudentgroup": True
        }

        try:
            raw_result = self._rpc_request("getTimetable", {"options": options})
        except Exception:
            return TimeTable([])

        all_su: dict[typing.Any, typing.Any] = {s['id']: s for s in self._rpc_request("getSubjects", {})}
        all_kl: dict[typing.Any, typing.Any] = {k['id']: k for k in self._rpc_request("getKlassen", {})}
        all_ro: dict[typing.Any, typing.Any] = {r['id']: r for r in self._rpc_request("getRooms", {})}

        periods: list[Period] = []
        for raw_p in raw_result:
            try:
                start_dt = datetime.datetime.combine(self._parse_date(raw_p['date']),
                                                     self._parse_time(raw_p['startTime']))
                end_dt = datetime.datetime.combine(self._parse_date(raw_p['date']), self._parse_time(raw_p['endTime']))

                subjects = []
                for s in raw_p.get('su', []):
                    master_su = all_su.get(s['id'], {})
                    subjects.append(Subject.from_dict({
                        'name': master_su.get('name', ''),
                        'longName': master_su.get('longName', ''),
                        'id': s['id']
                    }))

                klassen = []
                for k in raw_p.get('kl', []):
                    master_kl = all_kl.get(k['id'], {})
                    klassen.append(Class.from_dict({
                        'name': master_kl.get('name', ''),
                        'longName': master_kl.get('longName', ''),
                        'id': k['id']
                    }))

                rooms = []
                for r in raw_p.get('ro', []):
                    rid = r.get('id', 0)
                    master_ro = all_ro.get(rid, {})
                    rooms.append(Room.from_dict({
                        'name': master_ro.get('name', ''),
                        'longName': master_ro.get('longName', ''),
                        'id': rid
                    }))

                original_rooms = []
                for r in raw_p.get('ro', []):
                    org_id = r.get('orgid')
                    if org_id:
                        master_ro = all_ro.get(org_id, {})
                        original_rooms.append(Room.from_dict({
                            'name': master_ro.get('name', ''),
                            'longName': master_ro.get('longName', ''),
                            'id': org_id
                        }))

                teachers = [Teacher.from_teacher_id(t['id']) for t in raw_p.get('te', []) if 'id' in t]
                original_teachers = [Teacher.from_teacher_id(t['orgid']) for t in raw_p.get('te', []) if 'orgid' in t]

                p = Period(
                    raw_period_code=raw_p.get('code'),
                    start=start_dt,
                    end=end_dt,
                    subjects=subjects,
                    klassen=klassen,
                    rooms=rooms,
                    original_rooms=original_rooms,
                    teachers=teachers,
                    original_teachers=original_teachers,
                    student_group=raw_p.get('sg', ''),
                    activity_type=raw_p.get('activityType', ''),
                    bk_remark=raw_p.get('bkRemark', ''),
                    bk_text=raw_p.get('bkText', ''),
                    flags=raw_p.get('flags', ''),
                    ls_number=raw_p.get('lsnumber', 0),
                    ls_text=raw_p.get('lstext', ''),
                    subst_text=raw_p.get('substText', ''),
                    period_type=raw_p.get('type', ''),
                    period_id=raw_p.get('id', 0)
                )
                periods.append(p)
            except Exception:
                continue

        return TimeTable(periods)

    # ------------------------------------------------------------------
    # Raw API Implementations
    # ------------------------------------------------------------------

    @cached_method
    def teachers(self) -> typing.Any:
        return self._rpc_request("getTeachers")

    @cached_method
    def statusdata(self) -> typing.Any:
        # TODO: Update this to use custom objects.
        return self._rpc_request("getStatusData")

    @cached_method
    def last_import_time(self) -> int:
        return typing.cast(int, self._rpc_request("getLatestImportTime"))

    @cached_method
    def substitutions(self, start: datetime.date, end: datetime.date, department_id: int = 0) -> typing.Any:
        params = self._create_date_param(start, end, departmentId=department_id)
        return self._rpc_request("getSubstitutions", params)

    @cached_method
    def timegrid_units(self) -> list[str]:
        raw_json = self._rpc_request("getTimegridUnits")

        def convert_time(value: typing.Optional[int]) -> str:
            if value is None:
                return ""
            datetime_obj: datetime.time = datetime.datetime.strptime(str(value), "%H%M").time()
            return datetime_obj.strftime(my_config.html_style_config.lesson_time_ranges_format)

        lesson_time_ranges: list[str] = [
            f'{convert_time(time_unit.get("startTime"))} - '
            f'{convert_time(time_unit.get("endTime"))}'
            for item in raw_json
            for time_unit_list in item.get('timeUnits')
            for time_unit in time_unit_list
        ]

        return lesson_time_ranges

    @cached_method
    def students(self) -> typing.Any:
        return self._rpc_request("getStudents")

    @cached_method
    def exam_types(self) -> typing.Any:
        return self._rpc_request("getExamTypes")

    @cached_method
    def exams(self, start: datetime.date, end: datetime.date, exam_type_id: int = 0) -> typing.Any:
        params = self._create_date_param(start, end, examTypeId=exam_type_id)
        return self._rpc_request("getExams", params)

    @cached_method
    def timetable_with_absences(self, start: datetime.date, end: datetime.date) -> typing.Any:
        params = {"options": self._create_date_param(start, end)}
        return self._rpc_request("getTimetableWithAbsences", params)

    @cached_method
    def class_reg_events(self, start: datetime.date, end: datetime.date) -> typing.Any:
        params = self._create_date_param(start, end)
        return self._rpc_request("getClassregEvents", params)

    @cached_method
    def class_reg_event_for_id(self, start: datetime.date, end: datetime.date, **type_and_id: typing.Any) -> typing.Any:
        element_type_table = {'klasse': 1, 'teacher': 2, 'subject': 3, 'room': 4, 'student': 5}
        element_type, element_id = list(type_and_id.items())[0]
        params = self._create_date_param(start, end, id=int(element_id), type=element_type_table[element_type])
        return self._rpc_request("getClassregEvents", params)

    @cached_method
    def class_reg_categories(self) -> typing.Any:
        return self._rpc_request("getClassregCategories")

    @cached_method
    def class_reg_category_groups(self) -> typing.Any:
        return self._rpc_request("getClassregCategoryGroups")

    @cached_method
    def my_timetable(self, start: datetime.date, end: datetime.date) -> TimeTable:
        if not self._person_id or not self._person_type:
            raise RuntimeError("Person ID or Type not available. Are you logged in?")

        options = {
            "startDate": self._format_date(start),
            "endDate": self._format_date(end),
            "element": {"id": self._person_id, "type": self._person_type},
            "showBooking": True,
            "showInfo": True,
            "showSubstText": True,
            "showLsText": True,
            "showLsNumber": True,
            "showStudentgroup": True
        }

        try:
            raw_result = self._rpc_request("getTimetable", {"options": options})
        except Exception:
            return TimeTable([])

        all_su: dict[typing.Any, typing.Any] = {s['id']: s for s in self._rpc_request("getSubjects", {})}
        all_kl: dict[typing.Any, typing.Any] = {k['id']: k for k in self._rpc_request("getKlassen", {})}
        all_ro: dict[typing.Any, typing.Any] = {r['id']: r for r in self._rpc_request("getRooms", {})}

        periods: list[Period] = []
        for raw_p in raw_result:
            try:
                start_dt = datetime.datetime.combine(self._parse_date(raw_p['date']),
                                                     self._parse_time(raw_p['startTime']))
                end_dt = datetime.datetime.combine(self._parse_date(raw_p['date']),
                                                   self._parse_time(raw_p['endTime']))

                subjects = []
                for s in raw_p.get('su', []):
                    master_su = all_su.get(s['id'], {})
                    subjects.append(Subject.from_dict({
                        'name': master_su.get('name', ''),
                        'longName': master_su.get('longName', ''),
                        'id': s['id']
                    }))

                klassen = []
                for k in raw_p.get('kl', []):
                    master_kl = all_kl.get(k['id'], {})
                    klassen.append(Class.from_dict({
                        'name': master_kl.get('name', ''),
                        'longName': master_kl.get('longName', ''),
                        'id': k['id']
                    }))

                rooms = []
                for r in raw_p.get('ro', []):
                    rid = r.get('id', 0)
                    master_ro = all_ro.get(rid, {})
                    rooms.append(Room.from_dict({
                        'name': master_ro.get('name', ''),
                        'longName': master_ro.get('longName', ''),
                        'id': rid
                    }))

                original_rooms = []
                for r in raw_p.get('ro', []):
                    org_id = r.get('orgid')
                    if org_id:
                        master_ro = all_ro.get(org_id, {})
                        original_rooms.append(Room.from_dict({
                            'name': master_ro.get('name', ''),
                            'longName': master_ro.get('longName', ''),
                            'id': org_id
                        }))

                teachers = [Teacher.from_teacher_id(t['id']) for t in raw_p.get('te', []) if 'id' in t]
                original_teachers = [Teacher.from_teacher_id(t['orgid']) for t in raw_p.get('te', []) if
                                     'orgid' in t]

                p = Period(
                    raw_period_code=raw_p.get('code'),
                    start=start_dt,
                    end=end_dt,
                    subjects=subjects,
                    klassen=klassen,
                    rooms=rooms,
                    original_rooms=original_rooms,
                    teachers=teachers,
                    original_teachers=original_teachers,
                    student_group=raw_p.get('sg', ''),
                    activity_type=raw_p.get('activityType', ''),
                    bk_remark=raw_p.get('bkRemark', ''),
                    bk_text=raw_p.get('bkText', ''),
                    flags=raw_p.get('flags', ''),
                    ls_number=raw_p.get('lsnumber', 0),
                    ls_text=raw_p.get('lstext', ''),
                    subst_text=raw_p.get('substText', ''),
                    period_type=raw_p.get('type', ''),
                    period_id=raw_p.get('id', 0)
                )
                periods.append(p)
            except Exception:
                continue

        return TimeTable(periods)

    @cached_method
    def _search(self, surname: str, fore_name: str, dob: int = 0, what: int = -1) -> typing.Any:
        params = {"sn": surname, "fn": fore_name, "dob": dob, "type": what}
        return self._rpc_request("getPersonId", params)

    def get_student(self, surname: str, fore_name: str, dob: int = 0) -> dict[str, str | int]:
        id_val = self._search(surname=surname, fore_name=fore_name, dob=dob, what=5)
        if not id_val:
            raise KeyError("Student not found")
        return {"id": id_val, "name": surname, "longName": surname, "foreName": fore_name}

    def get_teacher_from_search(self, surname: str, fore_name: str, dob: int = 0) -> dict[str, str | int]:
        id_val = self._search(surname=surname, fore_name=fore_name, dob=dob, what=2)
        if not id_val:
            raise KeyError("Teacher not found")
        return {"id": id_val, "name": surname, "longName": surname, "foreName": fore_name, "title": ""}

    # ------------------------------------------------------------------
    # Multithreading / Async Workers
    # ------------------------------------------------------------------

    def _multithread_worker(
            self,
            raw_result: dict[str, str | Exception | dict[str, TimeTable]],
            raw_result_lock: threading.Lock,
            klasse: Class,
            _raw_date: str,
            start: datetime.date,
            end: datetime.date,
            function_name: str,
            call_id: uuid.UUID,
            max_attempts: int
    ) -> None:
        max_attempts = max(max_attempts, 1)

        entry: dict[str, dict[str, TimeTable]] | None = None
        error_entry: dict[str, str | Exception] | None = None

        for attempt in range(max_attempts):
            try:
                self.log_in(call_id)
                table: TimeTable = self.timetable_extended(klasse=klasse, start=start, end=end)
                entry = {klasse.name: {'table': table}}
                error_entry = None
                break
            except Exception as e:
                # Basic check for date not allowed since we aren't using webuntis errors any more
                self._my_logger.log_warning(f"Attempt {attempt + 1} failed in {function_name}: {e}")

                if attempt == max_attempts - 1:
                    entry = None
                    error_entry = {
                        'error': f'{my_config.language_config.unexpected_error}: [{datetime.datetime.now()}]',
                        'exception': e
                    }
                else:
                    time_module.sleep(0.5 * (attempt + 1))
                    continue

        with raw_result_lock:
            if entry is not None:
                raw_result.update(entry)
            elif error_entry is not None:
                raw_result.update(error_entry)

    def multithreading_result(
            self,
            sleep_time: float | int,
            max_threads: int,
            raw_date: str,
            start: datetime.date,
            end: datetime.date,
            function_name: str,
            logging: bool,
            call_id: uuid.UUID,
            log_out_afterwards: bool,
            max_attempts: int
    ) -> dict[str, str | Exception | dict[str, TimeTable]]:
        raw_result: dict[str, str | Exception | dict[str, TimeTable]] = {}
        raw_result_lock: threading.Lock = threading.Lock()
        klassen_list: list[Class] = self.all_klassen()

        threads: list[threading.Thread] = [
            threading.Thread(target=self._multithread_worker, args=(
                raw_result, raw_result_lock, klasse, raw_date, start, end, function_name, call_id, max_attempts
            ))
            for klasse in klassen_list
            if len(klasse.name) == 2 and not klasse.name.startswith('M')
        ]

        if logging:
            current_batch_count: int = 0
            total_batch_count: int = (len(threads) + max_threads - 1) // max_threads

            for i in range(0, len(threads), max_threads):
                batch = threads[i:i + max_threads]
                current_batch_count += 1

                for thread in batch:
                    thread.start()

                for thread in batch:
                    thread.join()

                percent = f'{100 * (current_batch_count / total_batch_count):.1f}'
                filled_length = int(50 * current_batch_count // total_batch_count)
                bar = '█' * filled_length + '-' * (50 - filled_length)

                sys.stdout.write(f'\rProgress |{bar}| {percent}% complete'
                                 f' (Batch #{current_batch_count} / {total_batch_count})')
                sys.stdout.flush()

                if current_batch_count == total_batch_count:
                    print()

                if i + max_threads < len(threads):
                    time_module.sleep(sleep_time)

            if log_out_afterwards:
                self.log_out(call_id)

            return raw_result

        for index, thread in enumerate(threads):
            if (index + 1) % max_threads == 0:
                time_module.sleep(sleep_time)
            thread.start()

        for thread in threads:
            thread.join()

        if log_out_afterwards:
            self.log_out(call_id)

        return raw_result


# Configuration
my_config: Config = Config()
my_config.set_lang('en')  # Default
