import traceback
import chellow.dloads
import os
import threading
from flask import g, request
from chellow.views import chellow_redirect
from decimal import Decimal
import xlrd
from itertools import chain
from werkzeug.exceptions import BadRequest
from chellow.utils import dumps, req_int
from collections import OrderedDict
from chellow.models import Session, GspGroup


def get_value(row, idx):
    val = row[idx].value
    if isinstance(val, str):
        return val.strip()
    else:
        return val


def get_rate(row, idx):
    val = get_value(row, idx)
    if isinstance(val, str) and len(val) == 0:
        return Decimal('0.00000')
    else:
        return round(Decimal(val) / Decimal('100'), 5)


def get_decimal(row, idx):
    return round(Decimal(get_value(row, idx)), 5)


def to_llfcs(row, idx):
    val = get_value(row, idx)
    if isinstance(val, str):
        llfcs = []
        for v in val.split(','):
            val = v.strip()
            if len(val) == 0:
                continue
            if '-' in val:
                start, finish = val.split('-')
                for i in range(int(start), int(finish) + 1):
                    llfcs.append(str(i))
            else:
                llfcs.append(val)
    elif isinstance(val, Decimal):
        llfcs = [str(int(val))]
    elif isinstance(val, float):
        llfcs_str = str(int(val))
        llfcs = []
        for i in range(0, len(llfcs_str), 3):
            llfcs.append(llfcs_str[i:i+3])
    return [v.zfill(3) for v in llfcs]


VL_MAP = {
    'Low Voltage Network': 'lv-net',
    'Low Voltage Substation': 'lv-sub',
    'High Voltage Network': 'hv-net',
    'High Voltage Substation': 'hv-sub',
    '33kV Generic': '33kv',
    '132/33kV Generic': '132kv_33kv',
    '132kV Generic': '132kv'}


def content(user, file_name, file_contents, gsp_group_id, llfc_tab, laf_tab):
    f = sess = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            'dno_rates.ion', user)
        f = open(running_name, mode='w')
        gsp_group = GspGroup.get_by_id(sess, gsp_group_id)
        tariffs = {}
        if file_name.endswith('.xlsx'):
            book = xlrd.open_workbook(file_contents=file_contents)
            llfc_sheet = book.sheet_by_index(llfc_tab)
            in_tariffs = False
            for row_index in range(1, llfc_sheet.nrows):
                row = llfc_sheet.row(row_index)
                val_0 = get_value(row, 0)
                if in_tariffs:
                    if len(val_0) == 0:
                        continue

                    llfcs_str = ','.join(
                        chain(to_llfcs(row, 1), to_llfcs(row, 10)))
                    tariffs[llfcs_str] = OrderedDict(
                        (
                            ('description', val_0),
                            ('gbp-per-mpan-per-day', get_rate(row, 6)),
                            ('gbp-per-kva-per-day', get_rate(row, 7)),
                            (
                                'excess-gbp-per-kva-per-day',
                                get_rate(row, 9)),
                            ('red-gbp-per-kwh', get_rate(row, 3)),
                            ('amber-gbp-per-kwh', get_rate(row, 4)),
                            ('green-gbp-per-kwh', get_rate(row, 5)),
                            ('gbp-per-kvarh', get_rate(row, 8))))
                else:
                    if val_0 == 'Tariff name' or \
                            get_value(row, 1) == "Open LLFCs":
                        in_tariffs = True
            laf_sheet = book.sheet_by_index(laf_tab)
            lafs = OrderedDict()
            for row_index in range(1, laf_sheet.nrows):
                row = laf_sheet.row(row_index)
                val_0 = get_value(row, 0)
                if val_0 in VL_MAP:
                    lafs[VL_MAP[val_0]] = OrderedDict(
                        (
                            ('winter-weekday-peak', get_decimal(row, 1)),
                            ('winter-weekday-day', get_decimal(row, 2)),
                            ('other', get_decimal(row, 3)),
                            ('night', get_decimal(row, 4))))
        else:
            raise BadRequest(
                "The file extension for " + file_name + " isn't recognized.")
        rs = {
            gsp_group.code: OrderedDict(
                (
                    ('lafs', lafs),
                    ('tariffs', OrderedDict(sorted(tariffs.items())))))}
        f.write(dumps(rs))
    except:
        f.write(traceback.format_exc())
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_post(session):
    user = g.user
    file_item = request.files["dno_file"]
    gsp_group_id = req_int('gsp_group_id')
    llfc_tab = req_int('llfc_tab')
    laf_tab = req_int('laf_tab')

    args = (
        user, file_item.filename, file_item.read(), gsp_group_id, llfc_tab,
        laf_tab)
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
