from datetime import datetime as Datetime
from pytz import utc


def triad_dates():
    return [
        Datetime(2007, 12, 17, 17, 0, tzinfo=utc),
        Datetime(2008, 1, 3, 17, 0, tzinfo=utc),
        Datetime(2007, 11, 26, 17, 0, tzinfo=utc)]
