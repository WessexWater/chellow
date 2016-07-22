from datetime import datetime as Datetime
from pytz import utc


def triad_dates():
    return [
        Datetime(2009, 1, 6, 17, 0, tzinfo=utc),
        Datetime(2008, 12, 1, 17, 0, tzinfo=utc),
        Datetime(2008, 12, 15, 17, 0, tzinfo=utc)]
