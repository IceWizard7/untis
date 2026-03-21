class Config:
    def __init__(self) -> None:
        # region Timetable mapping

        self.personal_timetable_entries: dict[str, tuple[set[str], set[str]]] = {}
        # Example:
        # {
        #     'child1': (
        #         Set of teacher abbreviations
        #         {'T1', 'T2', 'T3', ...},
        #         Set of subject abbreviations
        #         {'M', 'G', 'E', ...}),
        #     'child2': (
        #         {'T1', 'T2', 'T3', ...},
        #         {'M', 'G', 'E', ...}),
        # }
        #
        # This allows using:
        # TimeTable.filter_hours_by_personal('child') on an existing TimeTable
        # Which only returns the lessons with certain teachers or subjects attached to it.
        # Useful if your child is in a class, where some pupils attend lessons that your child doesn't.

        self.teacher_mapping: dict[int, tuple[str, str, tuple[str, ...]]] = {}
        # Example:
        # {
        #     0: ('Unknown', 'N/A', ('/',)),  # Always means no teacher, never assign a real name here
        #     Teacher ID: (full name,       abbreviated Name, (Subject abbreviation 1, ...)
        #     3:          ('Tom Mister',   'AB',              ('M', 'G', 'E')),
        #     8:          ('Benjamin Bob', 'CD',              ('PS', 'PE', 'FR')),
        # }
        # This allows the TimeTable to format the name of the teachers correctly.
        # The API technically does have a Session.teachers() function
        # which uses the webuntis getTeachers endpoint. However, most student accounts don't
        # have access to that endpoint. More documentation on this will follow soon.
        # Additionally, I'm working on a way integrate with the getTeachers endpoint directly
        # for the accounts that support it.

        # Hint: Generating this is rather tedious, but the first step is getting the IDs.
        # Read docs/element_ids.md for help.

        self.subject_to_color: dict[tuple[str, str, int], tuple[int, int, int]] = {}
        # Example:
        # {
        #     Subjet abbreviation, full subject name, subject id: RGB Value
        #     ('M',              'Math',               107): (83, 103, 220),
        #     ('E',              'English',            193): (45, 26, 136),
        #     ('FR',             'French',             981): (122, 112, 212)
        # }
        # This allows the TimeTable to display corresponding colors along with subjects.
        # The API technically delivers this, but I'm still uncertain whether this is safe to use.

        # Hint: Generating this is rather tedious, but the first step is getting the IDs.
        # Read docs/element_ids.md for help.

        # endregion Timetable mapping

        # region Language specific configuration

        # The following configuration variables are used for various to_html functions
        # For more clarity, examples are provided in both english and german.
        self.weekday_name_mapping: dict[str, str] = {
            'Monday': 'Monday',  # 'Monday': 'Montag',
            'Tuesday': 'Tuesday',  # 'Tuesday': 'Dienstag',
            'Wednesday': 'Wednesday',  # 'Wednesday': 'Mittwoch',
            'Thursday': 'Thursday',  # 'Thursday': 'Donnerstag',
            'Friday': 'Friday',  # 'Friday': 'Freitag',
            'Saturday': 'Saturday',  # 'Saturday': 'Samstag',
            'Sunday': 'Sunday'  # 'Sunday': 'Sonntag'
        }
        self.tomorrow: str = 'Tomorrow'  # 'Morgen'
        self.today: str = 'Today'  # 'Heute'
        self.yesterday: str = 'Yesterday'  # 'Gestern'
        self.last_week: str = 'Last Week'  # 'Letzte Woche'
        self.next_week: str = 'Next Week'  # 'Nächste Woche'
        self.two_week_abbreviation: str = '(2W)'  # '(2W)'
        self.two_week_abbreviation_legend: str = '(2W) = Every 2 weeks'  # '(2W) = Alle 2 Wochen'

        self.class_timetable: str = 'Class Timetable'  # 'Stundenplan'
        self.room_timetable: str = 'Room Timetable'  # 'Raumplan'
        self.teacher_timetable: str = 'Teacher Timetable'  # 'Lehrerplan'
        self.personal_timetable: str = 'Timetable'  # 'Stundenplan'

        self.unknown_element_extended_text: str = 'Unknown'  # 'Unbekannt'
        self.some_hour: str = 'Some Hour'  # 'Eine Stunde'
        self.is_cancelled: str = 'is cancelled'  # 'entfällt'
        self.are_cancelled: str = 'are cancelled'  # 'entfallen'
        self.is_irregular: str = 'is irregular'  # 'ist irregulär'
        self.are_irregular: str = 'are irregular'  # 'sind irregulär'
        self.instead: str = 'Instead of'  # 'Statt'

        self.multiple_lessons_cancelled: str = 'Multiple lessons are cancelled'  # 'Mehrere Stunden entfallen'
        self.multiple_lessons_irregular: str = 'Multiple lessons are irregular'  # 'Mehrere Stunden sind irregulär'

        self.back: str = 'Back'  # 'Zurück'
        self.time: str = 'Time'  # 'Zeit'

        self.unexpected_error: str = 'Error! Contact the Administrator of the Bot! Time of the error'
        # 'Fehler! Kontaktiere den Administrator des Bots! Zeit des Fehlers'

        # endregion Language specific configuration

        # region HTML style configuration
        # The following configuration variables are used for various to_html functions

        self.table_header_base_rgb: tuple[int, int, int] = (32, 16, 102)  # RGB value of headers
        self.today_personal_rgb_value: tuple[int, int, int] = (21, 8, 79)  # RGB value of 'today" header (personal_html)

        # Various HTML functions
        self.timetable_html_header: str = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>Timetable</title>
          <style>
                @page {
                    size: 140mm 200mm; /* slightly smaller than A5 */
                    margin: 100mm;       /* adjust margin to taste */
                }

                p {
                    font-family: monospace;
                    text-align: center;
                    font-size: 13px;
                    margin-top: 10px;
                }

                table {
                    border-collapse: separate;
                    border-spacing: 0;
                    width: 100%;
                    table-layout: fixed;
                    font-size: 9pt; /* slightly smaller font to fit portrait */
                    font-family: monospace;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }

                th, td {
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: center;
                }

                td {
                    text-align: center;
                    vertical-align: middle;
                    position: relative;
                    /*background: linear-gradient(to right,
                        var(--stripe-color, transparent) 0 6%,
                        transparent 6% 100%);*/
                    overflow: hidden;
                    height: 40px;
                    z-index: 0; /* stacking context */
                }

                tr:nth-child(even) {
                    background-color: #f9f9f9;
                }

                th {
                    color: white;
                    font-size: 11pt;
                }

                /* Create a triangle in the bottom-right corner */
                td::after {
                    content: "";
                    position: absolute;
                    right: 0;
                    bottom: 0;
                    width: 0;
                    height: 0;
                    border-style: solid;
                    border-width: 0 0 20px 20px; /* size of the triangle */
                    border-color: transparent transparent var(--stripe-color, transparent) transparent;
                    z-index: 0; /* behind text */
                }

                td > * {
                    position: relative;
                    z-index: 1; /* above triangle */
                }
            </style>
        </head>
        <body>
        """

        # Change this to your personal name if you want to flex :-)
        self.timetable_html_footer: str = f"""
        <p style="text-align:center; font-size:20px; margin-top:10px;">
          powered by: IceWizard7
        </p>
        """

        self.timetable_html_footer_two_week: str = f"""
        <p style="text-align:center; font-size:15px; margin-top:10px;">
          {self.two_week_abbreviation_legend}
        </p>
        """

        # Personal HTML
        self.personal_timetable_html_header: str = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>Timetable</title>
          <style>
                @page {
                    size: 140mm 200mm;
                    margin: 20mm;
                }

                body {
                    font-family: monospace;
                }

                p {
                    text-align: center;
                    font-size: 13px;
                    margin-top: 10px;
                }

                table {
                    border-collapse: separate;
                    border-spacing: 0;
                    margin: 30px auto;
                    table-layout: fixed;
                    font-size: 10pt;
                    width: auto;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }

                th, td {
                    border: 1px solid #ddd;
                    padding: 8px 14px;
                    text-align: center;
                }

                th {
                    color: white;
                    font-size: 10pt;
                }

                td {
                    vertical-align: middle;
                    position: relative;
                    overflow: hidden;
                    height: 30px;
                    z-index: 0;
                }

                td::after {
                    content: "";
                    position: absolute;
                    right: 0;
                    bottom: 0;
                    width: 0;
                    height: 0;
                    border-style: solid;
                    border-width: 0 0 16px 16px;
                    border-color: transparent transparent var(--stripe-color, transparent) transparent;
                    z-index: 0;
                }

                td > * {
                    position: relative;
                    z-index: 1;
                }
          </style>
        </head>
        <body>
        """
        self.personal_timetable_html_footer: str = f"""
        """

        self.unknown_element_symbol: str = '?'
        # This is shown when no info is applicable
        # For example, the untis API does not deliver data for the "subject" field, then the
        # TimeTable.to_html function will show the unknown_element_symbol instead of leaving the cell blank.

        self.lesson_time_ranges_format: str = '%H:%M'
        self.lesson_time_ranges: list[str] = [
            '07:50 - 08:40', '08:45 - 09:35',
            '09:40 - 10:30', '10:45 - 11:35',
            '11:40 - 12:30', '12:35 - 13:25',
            '13:30 - 14:20', '14:25 - 15:15',
            '15:20 - 16:10', '16:15 - 17:05',
            '17:10 - 18:00'
        ]
        # Important for HTML generation:
        # Adapt this to your actual time ranges at your school.
        # Otherwise, the lessons won't be displayed in a correct grid.
        # All time ranges need to use config.lesson_time_ranges_format format.

        # endregion HTML style configuration
