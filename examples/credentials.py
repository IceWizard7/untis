import untis

# Expose Globals
my_logger = untis.logging.Logger()

my_logger.log_levels([untis.logging.LogLevels.ERROR])

global_session = untis.objects.Session(
    'global_session', False, None, my_logger,

    username='insert_your_username',
    password='insert_your_password',
    server='insert-your-school.webuntis.com/WebUntis',
    school='insert-your-school',
    client='WebUntis Test'
)

# Save under concurrency (multiple requests at the same time)
# call_id = global_session.get_unique_uuid()
# global_session.log_in(call_id)
