from datetime import datetime
from pytz import utc

def triad_dates():
    return [datetime(2005, 11, 28, 17, 0, tzinfo=utc), datetime(2006, 1, 5, 17, 0, tzinfo=utc), datetime(2006, 2, 3, 17, 30, tzinfo=utc)]