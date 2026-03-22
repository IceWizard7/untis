# TimeTable

## 1. Receiving `TimeTable`

`Session.timetable_extended()` receives the timetable of a class for a certain time span (can be longer than a week).

## 2. Features

Exactly like `Session` objects, this module aims to serve as much functionality as possible.

### 2.1 Filtering
You can filter a `TimeTable` using:
- `copy_by_date_range(start_date: datetime.date, end_date: datetime.date) -> TimeTable`
- `filter_hours_by_subject(subject: Subject) -> None`
- `filter_hours_by_class(klasse: Class) -> None`
- `filter_hours_by_room(room: Room) -> None`
- `filter_hours_by_teacher(teacher: Teacher) -> None`
- `filter_hours_by_personal(name: str) -> None`
(Requires setting up `personal_timetable_entries` in `config`, also see the [Configuration Guide](configuration.md))

Note that most of these functions return None. These modify the `TimeTable` object in-place, similarly to how
`list.append()`modifies the `list` Object in-place.

### 2.2 Converting to HTML

You can convert a `TimeTable` to HTML using:
- `to_html(...) -> str` (General way to convert into HTML; Only used internally)
- `to_untis_html(...) -> str` (Usually the most elegant way to serve to users)
- `to_website_html(...) -> str` (Greater limit how many lessons will be displayed in 1 cell)
- `to_personal_html(...) -> str` (Only displays 1 day)

### 2.3 Displaying

You can display a `TimeTable` using:
- `table_to_image(...) -> io.BytesIO`
(Uses `to_untis_html()` to convert a timetable into HTML and then `playwright` to convert it into an image)
- `capture_all_images(...) -> dict[str, io.BytesIO]`
(Converts `pages` (mapping of `table_name` -> `html_content`) into multiple images)
