from datetime import datetime as Datetime
from pytz import utc


def triad_dates():
    return [
        Datetime(2007, 1, 23, 17, 0, tzinfo=utc),
        Datetime(2006, 12, 20, 17, 0, tzinfo=utc),
        Datetime(2007, 2, 8, 17, 30, tzinfo=utc)]
