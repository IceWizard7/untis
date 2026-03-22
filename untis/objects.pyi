from __future__ import annotations
import datetime
import dataclasses
import typing
import functools
import playwright.async_api
import io
import threading
import time as time_module
import uuid
import pathlib
import asyncio

from .logging import Logger
from .config import Config


@dataclasses.dataclass(frozen=True)
class BaseEntity:
    name: str
    long_name: str
    entity_id: int  # Generic id for any entity

    @classmethod
    def from_tuple(cls: type[typing.Self], raw_obj: tuple[str, str, int]) -> typing.Self:
        pass

    @classmethod
    def from_dict(cls, data: dict[str, str | int]) -> typing.Self:
        pass

    def __repr__(self) -> str:
        pass

    def __str__(self) -> str:
        pass


class Subject(BaseEntity):
    @property
    def color(self) -> tuple[int, int, int]:
        pass


class Class(BaseEntity):
    pass


class Room(BaseEntity):
    pass


class Teacher(BaseEntity):
    @property
    def subjects(self) -> tuple[str, ...] | str:
        pass

    @staticmethod
    def _get_name(raw_teacher_id: int) -> str:
        pass

    @staticmethod
    def _get_long_name(raw_teacher_id: int) -> str:
        pass

    @classmethod
    def from_teacher_id(
            cls: type[typing.Self],
            raw_teacher_id: int
    ) -> typing.Self:
        pass

    @classmethod
    def from_teacher_name(
            cls: type[typing.Self],
            raw_teacher_name: str
    ) -> typing.Self:
        pass

    @classmethod
    def from_teacher_long_name(
            cls: type[typing.Self],
            raw_teacher_long_name: str
    ) -> typing.Self:
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
        self.start: datetime.datetime = ...
        self.end: datetime.datetime = ...
        self.subjects: list[Subject] = ...
        self.raw_period_code: str | None = ...
        self.klassen: list[Class] = ...
        self.rooms: list[Room] = ...
        self.original_rooms: list[Room] = ...
        self.teachers: list[Teacher] = ...
        self.original_teachers: list[Teacher] = ...
        self.student_group: str = ...
        self.activity_type: str = ...
        self.bk_remark: str = ...
        self.bk_text: str = ...
        self.flags: str = ...
        self.ls_number: int = ...
        self.ls_text: str = ...
        self.subst_text: str = ...
        self.period_type: str = ...
        self.period_id: int = ...

    def get_period_code(self, featuring_object: Class | Room | Teacher) -> tuple[str, tuple[bool, bool]]:
        pass

    def period_code_class(self, _klassen_object: Class) -> str:
        pass

    def period_code_room(self, room_object: Room) -> str:
        pass

    def period_code_teacher(self, teacher_object: Teacher) -> str:
        pass

    def _subjects_str(self) -> str:
        pass

    def _rooms_str(self, regular_plan: bool) -> str:
        pass

    def _teachers_str(self, regular_plan: bool) -> str:
        pass

    def _klassen_str(self) -> str:
        pass

    def _formatted_list_class(self, regular_plan: bool) -> tuple[str, str, str, datetime.datetime, datetime.datetime]:
        pass

    def _formatted_list_room(self, regular_plan: bool) -> tuple[str, str, str, datetime.datetime, datetime.datetime]:
        pass

    def _formatted_list_teacher(self, regular_plan: bool) -> tuple[str, str, str, datetime.datetime, datetime.datetime]:
        pass

    def formatted_list(
            self, featuring_object: Class | Room | Teacher, regular_plan: bool
    ) -> tuple[str, str, str, datetime.datetime, datetime.datetime]:
        pass

    def formatted_string(self, featuring_object: Class | Room | Teacher, regular_plan: bool) -> str:
        pass

    def formatted_string_with_date_part(
            self,
            featuring_object: Class | Room | Teacher, regular_plan: bool
    ) -> str:
        pass

    def regular_plan_identifier(self) -> tuple[
        int, datetime.time, datetime.time, list[Subject], list[Class], list[Room], list[Teacher]
    ]:
        pass

    def __repr__(self) -> str:
        pass

    def __str__(self) -> str:
        pass

    def __eq__(self, other: object) -> bool:
        pass

    def __hash__(self) -> int:
        pass

    @classmethod
    def from_dict(cls, data: dict[str, typing.Any]) -> typing.Self:
        pass


class TimeTable:
    def __init__(self, periods: list[Period]) -> None:
        self._periods: list[Period] = ...

    def copy_by_date_range(self, start_date: datetime.date, end_date: datetime.date) -> TimeTable:
        pass

    def filter_hours_by_subject(self, subject: Subject) -> None:
        pass

    def filter_hours_by_class(self, klasse: Class) -> None:
        pass

    def filter_hours_by_room(self, room: Room) -> None:
        pass

    def filter_hours_by_teacher(self, teacher: Teacher) -> None:
        pass

    def filter_hours_by_personal(self, name: str) -> None:
        pass

    @staticmethod
    def format_value(value: float, percent: bool, val_int: bool) -> str:
        pass

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
        pass

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
        pass

    @staticmethod
    def get_table_name(
            featuring_object: Class | Room | Teacher,
            start_date: datetime.date,
            end_date: datetime.date
    ) -> tuple[str, str]:
        pass

    def unsorted_table(self) -> list[Period]:
        pass

    def _to_table(self) -> list[tuple[datetime.time, list[tuple[datetime.date, list[Period]]]]]:
        pass

    def to_class_cancelled_hours(self) -> list[str]:
        pass

    def _html_setup(
            self,
            user_id: int,
            website: bool,
            table_name: tuple[str, str],
            start_date: datetime.date | None,
            end_date: datetime.date | None
    ) -> tuple[list[str], list[str], dict[str, dict[str, list[Period]]]]:
        pass

    @staticmethod
    def html_line_too_long(
        distinct_lessons_list_formatted: set[tuple[str, str, str, datetime.datetime, datetime.datetime]]
    ) -> bool:
        pass

    @staticmethod
    def html_add_lesson_time_range(html: list[str], lesson_count_index: int, lesson_time_range: str) -> None:
        pass

    def to_html(
            self,
            featuring_object: Class | Room | Teacher,
            user_id: int,
            website: bool,
            table_name: tuple[str, str],
            start_date: datetime.date | None,
            end_date: datetime.date | None
    ) -> str:
        pass

    def to_untis_html(
            self,
            featuring_object: Class | Room | Teacher,
            user_id: int,
            table_name: tuple[str, str],
            start_date: datetime.date,
            end_date: datetime.date
    ) -> str:
        pass

    def to_website_html(
            self,
            featuring_object: Class | Room | Teacher,
            start_date: datetime.date,
            end_date: datetime.date
    ) -> str:
        pass

    def to_personal_html(
            self,
            featuring_object: Class | Room | Teacher,
            target_date: datetime.date,
            person_name: str
    ) -> str:
        pass

    def to_regular_html(
            self,
            featuring_object: Class | Room | Teacher,
            user_id: int,
            table_name: tuple[str, str]
    ) -> str:
        pass

    @staticmethod
    async def _render_one_image_by_html(
            semaphore: asyncio.Semaphore,
            browser: playwright.async_api.Browser,
            results: dict[str, bytes],
            table_name: tuple[str, str],
            html_content: str
    ) -> None:
        pass

    @staticmethod
    async def capture_image_by_html(
            concurrency_website_capture: int, table_name: tuple[str, str], html_content: str
    ) -> io.BytesIO:
        pass

    @staticmethod
    async def capture_all_images(
            concurrency_website_capture: int, pages: list[tuple[tuple[str, str], str]]
    ) -> dict[str, bytes]:
        pass

    async def table_to_image(
            self,
            concurrency_website_capture: int,
            featuring_object: Class | Room | Teacher,
            user_id: int,
            start_date: datetime.date,
            end_date: datetime.date
    ) -> io.BytesIO:
        pass

    def count_appearances(self, period_to_count: Period) -> int:
        pass

    def __len__(self) -> int:
        pass

    def __eq__(self, other: object) -> bool:
        pass

    def __add__(self, other: 'TimeTable') -> 'TimeTable':
        pass

    def __repr__(self) -> str:
        pass

    def __str__(self) -> str:
        pass


class Session:
    def __init__(
            self, session_name: str, use_cache: bool, cache_file: str | None, logger: 'Logger | None',
            username: str, password: str, server: str, school: str, client: str
    ) -> None:
        self._username: str = ...
        self._password: str = ...

        self._server: str = ...

        self._school: str = ...
        self._client: str = ...

        # Internal session tracking
        self._jsessionid: str | None = ...
        self._person_type: int | None = ...
        self._person_id: int | None = ...
        self._klasse_id: int | None = ...

        self._active_session_uuids: set[typing.Any] = ...
        self._session_name: str = ...
        self._cache: dict[typing.Any, typing.Any] = ...
        self._use_cache: bool = ...
        self._cache_file_path: pathlib.Path | None = ...
        self._my_logger: 'Logger' = ...

    @staticmethod
    def get_unique_uuid() -> uuid.UUID:
        pass

    # ------------------------------------------------------------------
    # Core JSON-RPC Mechanism
    # ------------------------------------------------------------------

    def _rpc_request(
            self, method: str, params: dict[str, typing.Any] | None = None, retry_on_authentication_error: bool = True,
    ) -> typing.Any:
        pass

    @staticmethod
    def _format_date(d: datetime.date) -> int:
        pass

    @staticmethod
    def _parse_date(d: int) -> datetime.date:
        pass

    @staticmethod
    def _parse_time(t: int) -> datetime.time:
        pass

    def _create_date_param(
            self, start: datetime.date, end: datetime.date, **kwargs: typing.Any
    ) -> dict[str, typing.Any]:
        pass

    # ------------------------------------------------------------------
    # Authentication Lifecycle
    # ------------------------------------------------------------------

    def log_in(self, unique_uuid: uuid.UUID) -> None:
        pass

    def log_out(self, unique_uuid: uuid.UUID) -> None:
        pass

    # ------------------------------------------------------------------
    # Caching Mechanism
    # ------------------------------------------------------------------

    def cache_file_last_changed(self) -> float | None:
        pass

    def get_from_cache(self, cid: typing.Any) -> typing.Any:
        pass

    def update_cache(self, cid: typing.Any, result: typing.Any) -> None:
        pass

    def clear_cache(self) -> None:
        pass

    def read_cache_from_file(self) -> None:
        pass

    def write_cache_to_file(self) -> None:
        pass

    @staticmethod
    def cached_method(func: typing.Any) -> typing.Any:
        @functools.wraps(func)
        def wrapper(self: typing.Any, *args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            pass

        pass

    # ------------------------------------------------------------------
    # Custom Object Parsers
    # ------------------------------------------------------------------

    @cached_method
    def all_klassen(self) -> list[Class]:
        pass

    @cached_method
    def all_rooms(self) -> list[Room]:
        pass

    @cached_method
    def get_klasse_by_name(self, name: str) -> Class | None:
        pass

    @cached_method
    def get_room_by_name(self, name: str) -> Room | None:
        pass

    @cached_method
    def get_teacher_by_name(self, name: str) -> Teacher | None:
        pass

    @cached_method
    def get_teacher_by_long_name(self, long_name: str) -> Teacher | None:
        pass

    @cached_method
    def timetable_extended(
            self,
            klasse: Class,
            start: datetime.date,
            end: datetime.date
    ) -> TimeTable:
        pass

    # ------------------------------------------------------------------
    # Raw API Implementations
    # ------------------------------------------------------------------

    @cached_method
    def departments(self) -> typing.Any:
        pass

    @cached_method
    def holidays(self) -> typing.Any:
        pass

    @cached_method
    def schoolyears(self) -> list[dict[str, typing.Any]]:
        pass

    def return_current_year(self) -> dict[str, typing.Any]:
        pass

    @cached_method
    def subjects(self) -> typing.Any:
        pass

    @cached_method
    def teachers(self) -> typing.Any:
        pass

    @cached_method
    def statusdata(self) -> typing.Any:
        pass

    @cached_method
    def last_import_time(self) -> typing.Any:
        pass

    @cached_method
    def substitutions(self, start: datetime.date, end: datetime.date, department_id: int = 0) -> typing.Any:
        pass

    @cached_method
    def timegrid_units(self) -> typing.Any:
        pass

    @cached_method
    def students(self) -> typing.Any:
        pass

    @cached_method
    def exam_types(self) -> typing.Any:
        pass

    @cached_method
    def exams(self, start: datetime.date, end: datetime.date, exam_type_id: int = 0) -> typing.Any:
        pass

    @cached_method
    def timetable_with_absences(self, start: datetime.date, end: datetime.date) -> typing.Any:
        pass

    @cached_method
    def class_reg_events(self, start: datetime.date, end: datetime.date) -> typing.Any:
        pass

    @cached_method
    def class_reg_event_for_id(self, start: datetime.date, end: datetime.date, **type_and_id: typing.Any) -> typing.Any:
        pass

    @cached_method
    def class_reg_categories(self) -> typing.Any:
        pass

    @cached_method
    def class_reg_category_groups(self) -> typing.Any:
        pass

    @cached_method
    def my_timetable(self, start: datetime.date, end: datetime.date) -> typing.Any:
        pass

    @cached_method
    def _search(self, surname: str, fore_name: str, dob: int = 0, what: int = -1) -> typing.Any:
        pass

    def get_student(self, surname: str, fore_name: str, dob: int = 0) -> dict[str, str | int]:
        pass

    def get_teacher_from_search(self, surname: str, fore_name: str, dob: int = 0) -> dict[str, str | int]:
        pass

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
        pass

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
        pass


my_config: Config = ...
