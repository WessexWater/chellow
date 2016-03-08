from datetime import datetime
from pytz import utc


def triad_dates():
    return [
        datetime(2013, 11, 25, 17, 0, tzinfo=utc),
        datetime(2013, 12, 6, 17, 0, tzinfo=utc),
        datetime(2014, 1, 30, 17, 0, tzinfo=utc)]
