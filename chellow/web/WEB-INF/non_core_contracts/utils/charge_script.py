import sys
from dateutil.relativedelta import relativedelta
from net.sf.chellow.monad import Monad
import pytz
import decimal
import collections
import datetime
import traceback

clogs = collections.deque()


def clog(msg):
    clogs.appendleft(datetime.datetime.now(pytz.utc).strftime(
        "%Y-%m-%d %H:%M:%S") + " - " + str(msg))
    if len(clogs) > 1000:
        clogs.pop()


class UserException(Exception):
    pass


class NotFoundException(Exception):
    pass

HH = relativedelta(minutes=30)


def form_str(inv, name):
    s = inv.getRequest().getParameter(name)
    if s is None:
        raise UserException("The field " + name + " is required.")
    return s


def form_bool(inv, name):
    return inv.getRequest().getParameter(name) == 'true'


def form_int(inv, name):
    try:
        return int(form_str(inv, name))
    except ValueError, e:
        raise UserException(
            "Problem parsing the field " + name + " as an integer: " + str(e))


def form_date(inv, prefix):
    return datetime.datetime(
        form_int(inv, prefix + '_year'), form_int(inv, prefix + '_month'),
        form_int(inv, prefix + '_day'), form_int(inv, prefix + '_hour'),
        form_int(inv, prefix + '_minute'), tzinfo=pytz.utc)


def form_decimal(inv, name):
    return decimal.Decimal(inv.getString(name))


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


def get_lib(lib_name):
    return Monad.getContext().getAttribute("net.sf.chellow." + lib_name)


def impt(gbls, *libs):
    for lib_name in libs:
        lib = get_lib(lib_name)
        if lib is None:
            raise UserException("Can't find a library with name " + lib_name)
        gbls[lib_name] = lib


def get_contract_func(contract, func_name):
    gb = {}
    exec (contract.charge_script, gb)
    return gb.get(func_name)


def validate_hh_start(dt):
    if dt.minute not in [0, 30] or dt.second != 0 or dt.microsecond != 0:
        raise UserException(
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
            datetime.datetime(year, month, day, hour, minute, tzinfo=pytz.utc))
    except ValueError, e:
        raise UserException(
            "Can't parse the date: " + start_date_str +
            ". It needs to be of the form yyyy-mm-dd hh:MM. " + str(e))


def parse_mpan_core(mcore):
    mcore = mcore.strip().replace(' ', '')
    if len(mcore) != 13:
        raise UserException(
            "The MPAN core '" + mcore + "' must contain exactly 13 digits.")

    for char in mcore:
        if char not in '0123456789':
            raise UserException(
                "Each character of an MPAN must be a digit.")

    ps = [3, 5, 7, 13, 17, 19, 23, 29, 31, 37, 41, 43]
    cd = sum(p * int(d) for p, d in zip(ps, mcore[:-1])) % 11 % 10
    if cd != int(mcore[-1]):
        raise UserException(
            "The MPAN core " + mcore +
            " is not valid. It fails the checksum test.")

    return ' '.join([mcore[:2], mcore[2:6], mcore[6:10], mcore[10:]])


def parse_bool(bool_str):
    return bool_str.lower() == 'true'


def hh_format(dt):
    return 'ongoing' if dt is None else dt.strftime("%Y-%m-%d %H:%M")


def totalseconds(td):
    return td.seconds + td.days * 24 * 3600

CHANNEL_TYPES = 'ACTIVE', 'REACTIVE_IMP', 'REACTIVE_EXP'


def parse_channel_type(channel_type):
    tp = channel_type.upper()
    if tp not in CHANNEL_TYPES:
        raise UserException(
            "The given channel type is '" + str(channel_type) +
            "' but it should be one of " + str(CHANNEL_TYPES) + ".")
    return tp


def parse_pc_code(code):
    return str(int(code)).zfill(2)


def send_response(
        inv, content, status=200, mimetype='text/csv', file_name=None):

    if file_name is None:
        content_disposition = None
    else:
        content_disposition = 'attachment; filename="' + file_name + '"'

    if sys.platform.startswith('java'):
        res = inv.getResponse()
        res.setContentType(mimetype)
        if content_disposition is not None:
            res.addHeader('Content-Disposition', content_disposition)
        res.setStatus(status)
        pw = res.getWriter()
        try:
            for l in content():
                pw.write(l)
                pw.flush()
        except:
            pw.write(traceback.format_exc())
            raise
        finally:
            pw.close()
    else:
        from flask import Response
        if content_disposition is not None:
            headers = {'Content-Disposition': content_disposition}
        else:
            headers = {}
        inv.response = Response(
            content(), status=status, mimetype=mimetype, headers=headers)
