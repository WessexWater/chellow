from datetime import datetime
from pytz import utc

def triad_dates():
    return [datetime(2010, 12 , 7, 17, 0, tzinfo=utc), datetime(2010, 12, 20, 17, 0, tzinfo=utc), datetime(2011, 1, 6, 17, 0, tzinfo=utc)]