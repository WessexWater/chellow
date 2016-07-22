from datetime import datetime as Datetime
from pytz import utc


def triad_dates():
    return [
        Datetime(2005, 11, 28, 17, 0, tzinfo=utc),
        Datetime(2006, 1, 5, 17, 0, tzinfo=utc),
        Datetime(2006, 2, 3, 17, 30, tzinfo=utc)]
