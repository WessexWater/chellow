from dateutil.relativedelta import relativedelta
from werkzeug.exceptions import BadRequest
import pytz
from decimal import Decimal
import collections
from datetime import datetime as Datetime
from flask import request, Response


clogs = collections.deque()


def clog(msg):
    clogs.appendleft(
        Datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S") + " - " +
        str(msg))
    if len(clogs) > 1000:
        clogs.pop()


HH = relativedelta(minutes=30)


def req_str(name):
    try:
        return request.values[name]
    except KeyError:
        raise BadRequest("The field " + name + " is required.")


def req_bool(name):
    try:
        return request.values[name] == 'true'
    except KeyError:
        return False


def req_int(name):
    try:
        return int(req_str(name))
    except ValueError as e:
        raise BadRequest(
            "Problem parsing the field " + name + " as an integer: " + str(e))


def req_date(prefix):
    return Datetime(
        req_int(prefix + '_year'), req_int(prefix + '_month'),
        req_int(prefix + '_day'), req_int(prefix + '_hour'),
        req_int(prefix + '_minute'), tzinfo=pytz.utc)


def req_decimal(name):
    return Decimal(req_str(name))


def prev_hh(dt):
    return None if dt is None else dt - HH


def next_hh(dt):
    return None if dt is None else dt + HH


def hh_after(dt1, dt2):
    if dt2 is None:
        return False
    else:
        return True if dt1 is None else dt1 > dt2


def hh_before(dt1, dt2):
    if dt1 is None:
        return False
    else:
        return True if dt2 is None else dt1 < dt2


def get_contract_func(contract, func_name):
    gb = {}
    exec(contract.charge_script, gb)
    return gb.get(func_name)


def req_hh_date(prefix):
    dt = req_date(prefix)
    validate_hh_start(dt)
    return dt


def validate_hh_start(dt):
    if dt.minute not in [0, 30] or dt.second != 0 or dt.microsecond != 0:
        raise BadRequest(
            "The half-hour must start exactly on the hour or half past "
            "the hour.")
    return dt


def parse_hh_start(start_date_str):
    if len(start_date_str) == 0:
        return None

    try:
        year = int(start_date_str[:4])
        month = int(start_date_str[5:7])
        day = int(start_date_str[8:10])
        hour = int(start_date_str[11:13])
        minute = int(start_date_str[14:])
        return validate_hh_start(
            Datetime(year, month, day, hour, minute, tzinfo=pytz.utc))
    except ValueError as e:
        raise BadRequest(
            "Can't parse the date: " + start_date_str +
            ". It needs to be of the form yyyy-mm-dd hh:MM. " + str(e))


def parse_mpan_core(mcore):
    mcore = mcore.strip().replace(' ', '')
    if len(mcore) != 13:
        raise BadRequest(
            "The MPAN core '" + mcore + "' must contain exactly 13 digits.")

    for char in mcore:
        if char not in '0123456789':
            raise BadRequest(
                "Each character of an MPAN must be a digit.")

    ps = [3, 5, 7, 13, 17, 19, 23, 29, 31, 37, 41, 43]
    cd = sum(p * int(d) for p, d in zip(ps, mcore[:-1])) % 11 % 10
    if cd != int(mcore[-1]):
        raise BadRequest(
            "The MPAN core " + mcore +
            " is not valid. It fails the checksum test.")

    return ' '.join([mcore[:2], mcore[2:6], mcore[6:10], mcore[10:]])


def parse_bool(bool_str):
    return bool_str.lower() == 'true'


def hh_format(dt):
    return 'ongoing' if dt is None else dt.strftime("%Y-%m-%d %H:%M")


CHANNEL_TYPES = 'ACTIVE', 'REACTIVE_IMP', 'REACTIVE_EXP'


def parse_channel_type(channel_type):
    tp = channel_type.upper()
    if tp not in CHANNEL_TYPES:
        raise BadRequest(
            "The given channel type is '" + str(channel_type) +
            "' but it should be one of " + str(CHANNEL_TYPES) + ".")
    return tp


def parse_pc_code(code):
    return str(int(code)).zfill(2)


def send_response(
        content, args=None, status=200, mimetype='text/csv', file_name=None):
    headers = {}
    if args is None:
        args = ()

    if file_name is not None:
        headers['Content-Disposition'] = 'attachment; filename="' + \
            file_name + '"'

    return Response(
        content(*args), status=status, mimetype=mimetype, headers=headers)
