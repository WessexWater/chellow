from dateutil.relativedelta import relativedelta
from werkzeug.exceptions import BadRequest
from pytz import timezone, utc
from decimal import Decimal
from collections import defaultdict, deque
from datetime import datetime as Datetime
from flask import request, Response
from jinja2 import Environment
import time
import traceback
from amazon.ion.simpleion import load, dump
from amazon.ion.exceptions import IonException
from io import StringIO
import os
from collections.abc import Mapping, Sequence
import zish

clogs = deque()


def clog(msg):
    clogs.appendleft(
        utc_datetime_now().strftime("%Y-%m-%d %H:%M:%S") + " - " +
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


def req_ion(name):
    try:
        return loads(req_str(name))
    except IonException as e:
        raise BadRequest(
            "Problem parsing the field " + name + " as ION " + str(e) + ".")


def req_date(prefix, resolution='minute'):
    if resolution == 'minute':
        return utc_datetime(
            req_int(prefix + '_year'), req_int(prefix + '_month'),
            req_int(prefix + '_day'), req_int(prefix + '_hour'),
            req_int(prefix + '_minute'))
    elif resolution == 'day':
        return utc_datetime(
            req_int(prefix + '_year'), req_int(prefix + '_month'),
            req_int(prefix + '_day'))


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
        return validate_hh_start(utc_datetime(year, month, day, hour, minute))
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


def hh_format(dt, ongoing_str='ongoing'):
    return ongoing_str if dt is None else dt.strftime("%Y-%m-%d %H:%M")


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
        content, args=None, status=200, content_type='text/csv; charset=utf-8',
        file_name=None):
    headers = {}
    if args is None:
        args = ()

    if file_name is not None:
        headers['Content-Disposition'] = 'attachment; filename="' + \
            file_name + '"'

    return Response(
        content(*args), status=status, content_type=content_type,
        headers=headers)


FORMATS = {
    'year': '%Y', 'month': '%m', 'day': '%d', 'hour': '%H',
    'minute': '%M', 'full': '%Y-%m-%d %H:%M', 'date': '%Y-%m-%d'}

prefix = '''
{%- macro input_date(prefix, initial=None, resolution='minute') -%}
  {% if prefix != None %}
    {% set year_field = prefix + '_year' %}
    {% set month_field = prefix + '_month' %}
    {% set day_field = prefix + '_day' %}
    {% set hour_field = prefix + '_hour' %}
    {% set minute_field = prefix + '_minute' %}
  {% else %}
    {% set year_field = 'year' %}
    {% set month_field = 'month' %}
    {% set day_field = 'day' %}
    {% set hour_field = 'hour' %}
    {% set minute_field = 'minute' %}
  {% endif %}

  {% set initial = initial|now_if_none %}

  <input name="{{ year_field }}" maxlength="4" size="4" value="
    {%- if request.values.year_field -%}
      {{ request.values.year_field }}
    {%- else -%}
      {{ initial|hh_format('year') }}
    {%- endif %}">

  {%- if resolution in ['month', 'day', 'hour', 'minute'] -%}
    -<select name="{{ month_field }}">
    {% for month in range(1, 13) -%}
      <option value="{{ "%02i"|format(month) }}"
        {%- if request.values.month_field -%}
          {%- if request.values.month_field|int == month %} selected
          {%- endif -%}
        {%- else -%}
          {%- if initial.month == month %} selected{%- endif -%}
        {%- endif -%}>{{ "%02i"|format(month) }}</option>
    {% endfor %}
    </select>
  {%- endif -%}

  {% if resolution in ['day', 'hour', 'minute'] -%}
    -<select name="{{ day_field }}">
      {% for day in range(1, 32) -%}
        <option value="{{ day }}"
          {%- if request.values.day_field -%}
            {%- if request.values.day_field|int == day %} selected
            {% endif -%}
          {% else %}
            {%- if initial.day == day %} selected{% endif -%}
          {%- endif %}>{{ "%02i"|format(day) }}</option>
      {% endfor -%}
    </select>
  {%- endif -%}

  {% if resolution in ['hour', 'minute'] %}
    <select name="{{ hour_field }}">
      {% for hour in range(24) %}
        <option value="{{ hour }}"
          {%- if request.values.hour_field -%}
            {%- if request.values.hour_field|int == hour %} selected
            {%- endif -%}
          {%- else -%}
            {%- if initial.hour == hour %} selected{%- endif -%}
          {%- endif %}>{{ "%02i"|format(hour) }}</option>
      {%- endfor %}
    </select>
  {%- endif -%}

  {% if resolution == 'minute' -%}
    :<select name="{{ minute_field }}">
      {% for minute in range(0, 31, 30) -%}
        <option value="{{ minute }}"
          {%- if request.values.minute_field %}
            {%- if request.values.minute_field|int == minute %} selected
            {%- endif %}
          {%- else %}
            {%- if initial.minute == minute %} selected{% endif %}
            {%- endif %}>{{ "%02i"|format(minute) }}</option>
      {% endfor %}
    </select>
  {%- endif %}
{%- endmacro -%}

{%- macro input_option(name, item_id, desc, initial=None) -%}
    <option value="{{ item_id }}"
        {%- if request.values.name -%}
            {%- if request.values.name == '' ~ item_id %} selected
            {%- endif -%}
        {%- else -%}
            {%- if initial == item_id %} selected{% endif -%}
            {%- endif -%}>{{ desc }}</option>
{%- endmacro -%}

{% macro input_text(name, initial=None, size=None, maxlength=None) %}
    <input name="{{ name }}" value="
        {%- if request.values.name -%}
            {{ request.values.name }}
        {%- elif initial is not none -%}
            {{initial}}
        {%- endif -%}"
        {%- if size %} size="{{ size }}"{% endif %}
        {%- if maxlength %} maxlength="{{ maxlength }}"{% endif %}>
{%- endmacro -%}

{% macro input_textarea(name, initial, rows, cols) -%}
  <textarea name="{{ name }}" rows="{{ rows }}" cols="{{ cols }}">
    {%- if request.values.name -%}
      {{ request.values.name }}
    {%- else -%}
      {{ initial }}
    {%- endif -%}
  </textarea>
{%- endmacro -%}

{%- macro input_checkbox(name, initial) %}
    <input type="checkbox" name="{{ name }}" value="true"
                {%- if request.values.name -%}
                    {%- if request.values.name == 'true' %} checked
                    {%- endif -%}
                {%- else -%}
                    {%- if initial == True %} checked{% endif -%}
                    {%- endif -%}>
{%- endmacro -%}
'''


def hh_format_filter(dt, modifier='full'):
    return "Ongoing" if dt is None else dt.strftime(FORMATS[modifier])


def now_if_none(dt):
    return utc_datetime_now() if dt is None else dt


env = Environment(autoescape=True)

env.filters['hh_format'] = hh_format_filter
env.filters['now_if_none'] = now_if_none

template_cache = {}


def render(template, vals, status_code=200, content_type='text/html'):
    if len(template_cache) > 10000:
        template_cache.clear()
    templ_str = prefix + template
    try:
        templ = template_cache[templ_str]
    except KeyError:
        templ = env.from_string(templ_str)
        template_cache[templ_str] = templ

    vals['request'] = request

    headers = {
        'mimetype': content_type,
        'Date': int(round(time.time() * 1000)),
        'Cache-Control': 'no-cache'}

    try:
        template_str = templ.render(vals)
    except:
        raise BadRequest(
            "Problem rendering template: " + traceback.format_exc())

    return Response(template_str, status_code, headers)


def hh_range(caches, start_date, finish_date):
    try:
        return caches['utils']['hh_range'][start_date][finish_date]
    except KeyError:
        try:
            utils_cache = caches['utils']
        except KeyError:
            utils_cache = caches['utils'] = {}

        try:
            ranges_cache = utils_cache['hh_range']
        except KeyError:
            ranges_cache = utils_cache['hh_range'] = {}

        try:
            range_start_cache = ranges_cache[start_date]
        except KeyError:
            range_start_cache = ranges_cache[start_date] = {}

        try:
            datetime_cache = utils_cache['datetime']
        except KeyError:
            datetime_cache = utils_cache['datetime'] = {}

        rg = []
        dt = start_date
        while dt <= finish_date:
            try:
                dt_stored = datetime_cache[dt]
            except KeyError:
                dt_stored = datetime_cache[dt] = dt

            rg.append(dt_stored)
            dt += HH

        range_tuple = range_start_cache[finish_date] = tuple(rg)
        return range_tuple


def hh_min(a_date, b_date):
    if a_date is None:
        return b_date
    if b_date is None:
        return a_date
    return min(a_date, b_date)


def hh_max(a_date, b_date):
    if a_date is None:
        return a_date
    if b_date is None:
        return b_date
    return max(a_date, b_date)


class keydefaultdict(defaultdict):
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        else:
            ret = self[key] = self.default_factory(key)
            return ret


ct = timezone('Europe/London')
root_path = None


def ct_datetime(year, month, day=1, hour=0, minute=0):
    return tz_datetime(ct, year, month, day, hour, minute)


def utc_datetime(year, month, day=1, hour=0, minute=0):
    return tz_datetime(utc, year, month, day, hour, minute)


def tz_datetime(tz, year, month, day=1, hour=0, minute=0):
    return tz.normalize(tz.localize(Datetime(year, month, day, hour, minute)))


def to_tz(tz, dt):
    if dt.tzinfo is None:
        return tz.normalize(tz.localize(dt))
    else:
        return tz.normalize(dt.astimezone(tz))


def to_ct(dt):
    return to_tz(ct, dt)


def to_utc(dt):
    return to_tz(utc, dt)


def utc_datetime_now():
    return Datetime.utcnow().replace(tzinfo=utc)


def utc_datetime_parse(date_str, format_str):
    return Datetime.strptime(date_str, format_str).replace(tzinfo=utc)


def csv_make_val(v):
    val = make_val(v)
    if isinstance(val, Datetime):
        return hh_format(val)
    else:
        return val


def make_val(v):
    if isinstance(v, set):
        if len(v) == 1:
            return make_val(v.pop())
        elif 1 < len(v) < 4:
            return ' | '.join(str(csv_make_val(el)) for el in sorted(v))
        else:
            return None
    else:
        return v


def get_file_script_latest(contract_name):
    return list(get_file_scripts(contract_name))[-1]


def get_file_script(contract_name, date):
    for start_date, finish_date, script in get_file_scripts(contract_name):
        if date >= start_date and not hh_after(date, finish_date):
            return start_date, finish_date, script


def get_file_scripts(contract_name):
    rscripts_path = os.path.join(root_path, 'rate_scripts', contract_name)

    rscripts = []
    for rscript_fname in sorted(os.listdir(rscripts_path)):
        if not rscript_fname.endswith('.zish'):
            continue
        try:
            start_str, finish_str = \
                rscript_fname.split('.')[0].split('_')
        except ValueError:
            raise Exception(
                "The rate script " + rscript_fname +
                " in the directory " + rscripts_path +
                " should consist of two dates separated by an " +
                "underscore.")
        start_date = to_utc(Datetime.strptime(start_str, "%Y%m%d%H%M"))
        if finish_str == 'ongoing':
            finish_date = None
        else:
            finish_date = to_utc(
                Datetime.strptime(finish_str, "%Y%m%d%H%M"))
        with open(os.path.join(rscripts_path, rscript_fname), 'r') as f:
            script = f.read()
        rscripts.append((start_date, finish_date, script))
    return tuple(rscripts)


class RateDict(Mapping):
    def __init__(self, contract_name, dt, rate_dict, key_history):
        self._contract_name = contract_name
        self._dt = dt
        for k, v in tuple(rate_dict.items()):
            if isinstance(v, Mapping):
                rate_dict[k] = RateDict(
                    contract_name, dt, v, key_history + [k])
        self._storage = rate_dict
        self._key_history = key_history

    def __getitem__(self, key):
        try:
            return self._storage[key]
        except KeyError:
            raise Exception(
                "For the contract " + self._contract_name +
                " and the rate script at " + hh_format(self._dt) +
                " the key " + str(self._key_history + [key]) +
                " can't be found.")

    def __iter__(self):
        return iter(self._storage)

    def __len__(self):
        return len(self._storage)


def identity_func(x):
    return x


def get_file_rates(cache, contract_name, dt):
    try:
        return cache['contract_names'][contract_name][dt]
    except KeyError:
        try:
            contract_names = cache['contract_names']
        except KeyError:
            contract_names = cache['contract_names'] = {}

        try:
            cont = contract_names[contract_name]
        except KeyError:
            cont = contract_names[contract_name] = {}

        try:
            return cont[dt]
        except KeyError:
            month_after = dt + relativedelta(months=1) + relativedelta(days=1)
            month_before = dt - relativedelta(months=1) - relativedelta(days=1)

            try:
                future_funcs = cache['future_funcs']
            except KeyError:
                future_funcs = {}
                cache['future_funcs'] = future_funcs

            try:
                future_func = future_funcs[contract_name]
            except KeyError:
                future_func = future_funcs[contract_name] = {
                    'start_date': None, 'func': identity_func}

            start_date = future_func['start_date']
            ffunc = future_func['func']

            if start_date is None:
                rs = get_file_script(contract_name, dt)

                if rs is None:
                    rs_start, rs_finish, script = get_file_script_latest(
                        contract_name)
                    func = ffunc
                    if dt < rs_start:
                        cstart = month_before
                        cfinish = min(month_after, rs_start - HH)
                    else:
                        cstart = max(rs_finish + HH, month_before)
                        cfinish = month_after
                else:
                    rs_start, rs_finish, script = rs
                    func = identity_func
                    cstart = max(rs_start, month_before)
                    if rs_finish is None:
                        cfinish = month_after
                    else:
                        cfinish = min(rs_finish, month_after)
            else:
                if dt < start_date:
                    rs = get_file_script(contract_name, dt)

                    if rs is None:
                        rs_start, rs_finish, script = get_file_script_latest(
                            contract_name)
                    else:
                        rs_start, rs_finish, script = rs

                    func = identity_func
                    cstart = max(rs_start, month_before)
                    cfinish = min(month_after, start_date - HH)
                else:
                    rs = get_file_script(contract_name, dt)
                    if rs is None:
                        rs_start, rs_finish, script = get_file_script_latest(
                            contract_name)
                    else:
                        rs_start, rs_finish, script = rs
                    func = ffunc
                    cstart = max(start_date, month_before)
                    cfinish = month_after
            try:
                rscript = RateDict(
                    contract_name, dt, func(zish.loads(script)), [])
            except zish.ZishException as e:
                raise BadRequest(
                    "Problem parsing rate script for contract " +
                    contract_name + " starting at " +
                    hh_format(start_date) + ": " + str(e))
            except BadRequest as e:
                raise BadRequest(
                    "Problem with rate script for contract " +
                    contract_name + " starting at " +
                    hh_format(start_date) + ": " + e.description)

            for hh_date in hh_range(cache, cstart, cfinish):
                cont[hh_date] = rscript
            return cont[dt]


def loads(ion_str):
    try:
        return load(StringIO(ion_str))
    except IonException as e:
        raise BadRequest("Problem with ION: " + str(e))


def dumps_orig(val):
    f = StringIO()
    dump(val, f)
    return f.getvalue()


def dump_val(val, indent):
    out = []
    next_indent = indent + '  '
    if isinstance(val, str):
        out.append('"' + val + '"')
    elif isinstance(val, Mapping):
        out.append('{\n')
        for i, (k, v) in enumerate(val.items()):
            out.append(
                next_indent + '"' + k + '": ' + dump_val(v, next_indent))
            if i < len(val) - 1:
                out.append(',\n')
        out.append('}')
    elif isinstance(val, Sequence):
        out.append('[\n')
        for i, v in enumerate(val):
            out.append(next_indent + dump_val(v, next_indent))
            if i < len(val) - 1:
                out.append(',\n')
        out.append(']')
    elif isinstance(val, Decimal):
        out.append(str(val))
    elif isinstance(val, bool):
        out.append('true' if val else 'false')
    elif isinstance(val, int):
        out.append(str(val))
    else:
        raise Exception(
            "Must be either a str, Decimal, Mapping, bool  or Sequence, " +
            "but got a " + str(type(val)))
    return ''.join(out)


def dumps(val):
    return '$ion_1_0 ' + dump_val(val, '')
