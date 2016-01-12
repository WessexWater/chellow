from datetime import datetime
from pytz import utc

def triad_dates():
    return [datetime(2011, 12, 5, 17, 0, tzinfo=utc), datetime(2012, 1, 16, 17, 0, tzinfo=utc), datetime(2012, 2, 2, 17, 30, tzinfo=utc)]