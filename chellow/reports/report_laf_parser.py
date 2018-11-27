import traceback
import chellow.dloads
import os
import threading
from flask import g, request
from chellow.views import chellow_redirect
from chellow.models import Session
from zish import dumps
from io import StringIO
from collections import OrderedDict
import csv
from datetime import datetime as Datetime, timedelta as Timedelta
from chellow.utils import to_ct, to_utc
from decimal import Decimal


def content(user, file_name, file_like):
    f = sess = None
    try:
        sess = Session()
        tps = {}
        llfc_tp = {}
        block = {
            'llfc_tp': llfc_tp,
            'tps': tps
        }
        llfc_code = line_dt = start_date_str = None
        tp_cand = {}
        llfc_data = OrderedDict()
        for vals in csv.reader(file_like, delimiter='|'):
            code = vals[0]

            if code in ('LLF', 'ZPT'):
                if llfc_code is not None:

                    # Compress days
                    days = OrderedDict()
                    for dt, slots in llfc_data.items():
                        day = days[dt] = []
                        prev_laf = None
                        for slot, laf in slots.items():
                            if laf == prev_laf:
                                day[-1]['slot_finish'] = slot
                            else:
                                day.append(
                                    {
                                        'slot_start': slot,
                                        'slot_finish': slot,
                                        'laf': laf
                                    }
                                )
                            prev_laf = laf

                    prev_day = last_block = None
                    for dt, day in days.items():
                        if day == prev_day:
                            last_block['finish_date'] = dt
                        else:
                            last_block = tp_cand[dt] = {
                                'start_date': dt,
                                'finish_date': dt,
                                'slots': day
                            }
                        prev_day = day

                    for tp_id, tp in tps.items():
                        if tp_cand == tp:
                            llfc_tp[llfc_code] = tp_id
                            tp_cand = {}
                            break

                    if tp_cand != {}:
                        tp_id = len(tps)
                        tps[tp_id] = tp_cand
                        llfc_tp[llfc_code] = tp_id

                    tp_cand = {}
                if code == 'LLF':
                    llfc_code = vals[1]

            elif code == 'SDT':
                line_dt = vals[1]
                if start_date_str is None:
                    start_date_str = line_dt
                llfc_data[line_dt] = OrderedDict()

            elif code == 'SPL':
                slot, laf = vals[1:]
                llfc_data[line_dt][slot] = laf

        start_date_raw = Datetime.strptime(start_date_str, "%Y%m%d")
        start_date_ct = to_ct(start_date_raw)
        start_date = to_utc(start_date_ct)

        finish_date_raw = Datetime.strptime(line_dt, "%Y%m%d")
        finish_date_ct = to_ct(finish_date_raw)
        finish_date_ct += Timedelta(minutes=30*(int(slot) - 1))
        finish_date = to_utc(finish_date_ct)

        running_name, finished_name = chellow.dloads.make_names(
            start_date.strftime('%Y%m%d%H%M') + '_' +
            finish_date.strftime('%Y%m%d%H%M') + '.zish', user)
        f = open(running_name, mode='w')

        llfc_tp = dict((k.zfill(3), v) for k, v in block['llfc_tp'].items())
        block['llfc_tp'] = llfc_tp

        for tp in block['tps'].values():
            for date_block in tp.values():
                for slot in date_block['slots']:
                    slot['laf'] = Decimal(slot['laf'])
                    slot['slot_start'] = int(slot['slot_start'])
                    slot['slot_finish'] = int(slot['slot_finish'])

        f.write(dumps(block))
    except BaseException:
        f.write(traceback.format_exc())
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_post(session):
    user = g.user
    file_item = request.files["laf_file"]

    args = user, file_item.filename, StringIO(file_item.read().decode('utf-8'))
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
