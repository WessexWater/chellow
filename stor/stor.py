import sys
import os
import datetime
import pytz

sys.path.append(os.getcwd())

import stor_data

hh_start = datetime.datetime(stor_data.year, stor_data.month, 1, 0, 0)
hh = datetime.timedelta(minutes=30)

total_availability_gbp = 0

clock_tz = pytz.timezone('Europe/London')

def clock_to_utc(clock_timestamp):
    return clock_tz.localize(clock_timestamp).astimezone(pytz.utc).replace(tzinfo=None)


with open('out.csv', 'w') as f:
    f.write('hh-start,day-code,declared-mw,rate,window,gbp\n')
    f.flush()
    while hh_start.month == stor_data.month:
        hh_start_date = hh_start.date()
        season = None
        for sn in stor_data.seasons:
            if sn['start-date'] <= hh_start <= sn['finish-date']:
                season = sn
                break
        if season is None:
            f.write(hh_start.isoformat(sep=' ') + ', out of season\n')
        else:
            if hh_start.weekday() == 6 or hh_start_date in stor_data.bank_holidays:
                day_code = 'NWD'
            else:
                day_code = 'WD'
    
            windows = season[day_code]
            window_name = 'optional'
    
            for win_name, win_times in windows.iteritems():
                win_start = clock_to_utc(datetime.datetime.combine(hh_start_date, win_times['start']))
                win_finish = clock_to_utc(datetime.datetime.combine(hh_start_date, win_times['finish']))

                if win_start <= hh_start <= win_finish:
                    window_name = win_name
                    break
    
            availability_rate = season['availability-price']
    
            declaration = stor_data.declarations[hh_start_date]
            declared_mw = declaration[window_name]
            if declared_mw is not None and window_name != 'optional':
                availability_gbp = declared_mw * availability_rate / 2
            else:
                availability_gbp = 0

            f.write(','.join(str(value) for value in [hh_start.isoformat(sep=' '), day_code, declared_mw, availability_rate, window_name, availability_gbp, '\n']))
            total_availability_gbp += availability_gbp
        f.flush()
        hh_start += hh
    f.write('\n\ntotal availability gbp,' + str(total_availability_gbp))
