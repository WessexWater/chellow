from datetime import datetime as Datetime
from pytz import utc


def triad_dates():
    return [
        Datetime(2010, 12, 7, 17, 0, tzinfo=utc),
        Datetime(2010, 12, 20, 17, 0, tzinfo=utc),
        Datetime(2011, 1, 6, 17, 0, tzinfo=utc)]
