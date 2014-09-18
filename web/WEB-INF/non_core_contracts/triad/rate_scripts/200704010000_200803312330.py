from datetime import datetime
from pytz import utc

def triad_dates():
    return [datetime(2007, 12, 17, 17, 0, tzinfo=utc), datetime(2008, 1, 3, 17, 0, tzinfo=utc), datetime(2007, 11, 26, 17, 0, tzinfo=utc)]