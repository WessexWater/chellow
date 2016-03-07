from datetime import datetime
from pytz import utc

def triad_dates():
    return [datetime(2009, 1, 6, 17, 0, tzinfo=utc), datetime(2008, 12, 1, 17, 0, tzinfo=utc), datetime(2008, 12, 15, 17, 0, tzinfo=utc)]