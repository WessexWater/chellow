from datetime import datetime as Datetime
from pytz import utc


def triad_dates():
    return [
        Datetime(2010, 1, 7, 17, 0, tzinfo=utc),
        Datetime(2010, 1, 25, 17, 0, tzinfo=utc),
        Datetime(2009, 12, 15, 17, 0, tzinfo=utc)]
