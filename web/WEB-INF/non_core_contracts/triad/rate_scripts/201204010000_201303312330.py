from datetime import datetime
from pytz import utc

def triad_dates():
    return [datetime(2012, 11, 29, 17, 0, tzinfo=utc), datetime(2012, 12, 12, 17, 0, tzinfo=utc), datetime(2013, 1, 16, 17, 0, tzinfo=utc)]