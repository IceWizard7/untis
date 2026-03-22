import untis
from credentials import global_session
import datetime

untis.my_config.set_lang('en')

untis.my_config.timetable_html_footer = f"""
<p style="text-align:center; font-size:20px; margin-top:10px;">
  powered by: This is how to edit `my_config`!
</p>
"""

call_id = global_session.get_unique_uuid()
global_session.log_in(call_id)

klasse = global_session.get_klasse_by_name('1a')  # Try '1A' alternatively


today = datetime.date.today()
monday = today - datetime.timedelta(days=today.weekday())
friday = monday + datetime.timedelta(days=4)

table = global_session.timetable_extended(klasse=klasse, start=monday, end=friday)

# Images: (asynchronous)
# image_result = await table.table_to_image(3, klasse, 0, monday, friday)
# with open('result.png', 'wb') as f:
# f.write(image_result)

# HTML:
table_name: tuple[str, str] = table.get_table_name(klasse, monday, friday)
html_result = table.to_untis_html(klasse, 0, False, table_name, monday, friday)

print(html_result)
