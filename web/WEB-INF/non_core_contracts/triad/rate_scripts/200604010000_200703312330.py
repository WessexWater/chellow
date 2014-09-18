from datetime import datetime
from pytz import utc

def triad_dates():
    return [datetime(2007, 1, 23, 17, 0, tzinfo=utc), datetime(2006, 12, 20, 17, 0, tzinfo=utc), datetime(2007, 2, 8, 17, 30, tzinfo=utc)]