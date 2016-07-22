from datetime import datetime as Datetime
from pytz import utc


def triad_dates():
    return [
        Datetime(2012, 11, 29, 17, 0, tzinfo=utc),
        Datetime(2012, 12, 12, 17, 0, tzinfo=utc),
        Datetime(2013, 1, 16, 17, 0, tzinfo=utc)]
