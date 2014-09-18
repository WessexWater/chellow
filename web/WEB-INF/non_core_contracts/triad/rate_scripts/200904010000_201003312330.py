from datetime import datetime
from pytz import utc

def triad_dates():
    return [datetime(2010, 1, 7, 17, 0, tzinfo=utc), datetime(2010, 1, 25, 17, 0, tzinfo=utc), datetime(2009, 12, 15, 17, 0, tzinfo=utc)]