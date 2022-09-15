import time
import traceback
from collections import defaultdict
from collections.abc import Mapping, Set
from datetime import datetime as Datetime
from decimal import Decimal, InvalidOperation

from dateutil.relativedelta import relativedelta

from flask import Response, request

from jinja2 import Environment

from pytz import timezone, utc

from werkzeug.exceptions import BadRequest

from zish import ZishException, loads

url_root = ""

HH = relativedelta(minutes=30)
MONTH = relativedelta(months=1)
YEAR = relativedelta(years=1)


def req_str(name):
    try:
        return request.values[name]
    except KeyError:
        raise BadRequest(f"The field {name} is required.")


def req_bool(name):
    try:
        return request.values[name] == "true"
    except KeyError:
        return False


def req_int(name):
    try:
        return int(req_str(name))
    except ValueError as e:
        raise BadRequest(f"Problem parsing the field {name} as an integer: {e}")


def req_zish(name):
    try:
        return loads(req_str(name))
    except ZishException as e:
        raise BadRequest(f"Problem parsing the field {name} as Zish: {e}")


def req_date(prefix, resolution="minute"):
    year = req_int(f"{prefix}_year")
    month = req_int(f"{prefix}_month")
    day = req_int(f"{prefix}_day")

    try:
        if resolution == "day":
            d = ct_datetime(year, month, day)
        elif resolution == "minute":
            hour = req_int(f"{prefix}_hour")
            minute = req_int(f"{prefix}_minute")
            d = ct_datetime(year, month, day, hour, minute)
    except ValueError as e:
        raise BadRequest(f"Problem parsing the date {prefix}: {e}.")

    return to_utc(d)


def req_decimal(name):
    try:
        return Decimal(req_str(name))
    except InvalidOperation as e:
        raise BadRequest(f"Problem parsing the field {name} as a decimal: {e}.")


def req_file(name):
    try:
        return request.files[name]
    except KeyError:
        raise BadRequest(f"The file {name} is required.")


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
            "The half-hour must start exactly on the hour or half past the hour."
        )
    return dt


def parse_hh_start(start_date_str):
    if len(start_date_str) == 0:
        return None

    try:
        year = int(start_date_str[:4])
        month = int(start_date_str[5:7])
        day = int(start_date_str[8:10])
        hour = int(start_date_str[11:13])
        minute = int(start_date_str[14:16])
        if start_date_str[-1] == "Z":
            dt = utc_datetime(year, month, day, hour, minute)
        else:
            dt = to_utc(ct_datetime(year, month, day, hour, minute))
        return validate_hh_start(dt)
    except ValueError as e:
        raise BadRequest(
            f"Can't parse the date: {start_date_str}. It needs to be of the "
            f"form yyyy-mm-dd hh:MM with an optional Z on the end. {e}"
        )


def parse_mpan_core(mcore):
    mcore = mcore.strip().replace(" ", "")
    if len(mcore) != 13:
        raise BadRequest(f"The MPAN core '{mcore}' must contain exactly 13 digits.")

    for char in mcore:
        if char not in "0123456789":
            raise BadRequest("Each character of an MPAN must be a digit.")

    ps = [3, 5, 7, 13, 17, 19, 23, 29, 31, 37, 41, 43]
    cd = sum(p * int(d) for p, d in zip(ps, mcore[:-1])) % 11 % 10
    if cd != int(mcore[-1]):
        raise BadRequest(
            f"The MPAN core {mcore} is not valid. It fails the checksum test."
        )

    return " ".join([mcore[:2], mcore[2:6], mcore[6:10], mcore[10:]])


def parse_bool(bool_str):
    val = bool_str.strip().lower()
    if val == "true":
        return True
    elif val == "false":
        return False
    else:
        raise BadRequest(f"A boolean must be 'true' or 'false', but got '{bool_str}'.")


def hh_format(dt, ongoing_str="ongoing", with_hh=False):
    if dt is None:
        return (ongoing_str, ongoing_str) if with_hh else ongoing_str
    else:
        if dt.tzinfo is None:
            ts = to_utc(dt)
        else:
            ts = dt
        d = to_ct(ts)
        dt_str = d.strftime("%Y-%m-%d %H:%M")
        if with_hh:
            dc = ct_datetime(d.year, d.month, d.day)
            du = to_utc(dc)
            hh = 0
            while dc.day == d.day and du <= ts:
                hh += 1
                du += HH
                dc = to_ct(du)
            return dt_str, hh
        else:
            return dt_str


CHANNEL_TYPES = "ACTIVE", "REACTIVE_IMP", "REACTIVE_EXP"


def parse_channel_type(channel_type):
    tp = channel_type.upper()
    if tp not in CHANNEL_TYPES:
        raise BadRequest(
            f"The given channel type is '{channel_type}' but it should be one of "
            f"{CHANNEL_TYPES}."
        )
    return tp


def parse_pc_code(code):
    return str(int(code)).zfill(2)


def send_response(
    content,
    args=None,
    status=200,
    content_type="text/csv; charset=utf-8",
    file_name=None,
):
    headers = {}
    if args is None:
        args = ()

    if file_name is not None:
        headers["Content-Disposition"] = f'attachment; filename="{file_name}"'

    return Response(
        content(*args), status=status, content_type=content_type, headers=headers
    )


FORMATS = {
    "year": "%Y",
    "month": "%m",
    "day": "%d",
    "hour": "%H",
    "minute": "%M",
    "full": "%Y-%m-%d %H:%M",
    "date": "%Y-%m-%d",
}

prefix = """
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

{% macro input_text(
    name, initial=None, size=None, maxlength=None, placeholder=None) %}
    <input name="{{ name }}" value="
        {%- if request.values.name -%}
            {{ request.values.name }}
        {%- elif initial is not none -%}
            {{initial}}
        {%- endif -%}"
        {%- if size %} size="{{ size }}"{% endif %}
        {%- if placeholder %} placeholder="{{ placeholder }}"{% endif %}
        {%- if maxlength %} maxlength="{{ maxlength }}"{% endif %}>
{%- endmacro -%}

{% macro input_textarea(name, initial, rows, cols, placeholder=None) -%}
  <textarea name="{{ name }}" rows="{{ rows }}" cols="{{ cols }}"
    {%- if placeholder %} placeholder="{{ placeholder }}"{% endif %}>
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
"""


def hh_format_filter(dt, modifier="full"):
    return "Ongoing" if dt is None else dt.strftime(FORMATS[modifier])


def now_if_none(dt):
    return utc_datetime_now() if dt is None else dt


env = Environment(autoescape=True)

env.filters["hh_format"] = hh_format_filter
env.filters["now_if_none"] = now_if_none

template_cache = {}


def render(template, vals, status_code=200, content_type="text/html"):
    if len(template_cache) > 10000:
        template_cache.clear()
    templ_str = prefix + template
    try:
        templ = template_cache[templ_str]
    except KeyError:
        templ = env.from_string(templ_str)
        template_cache[templ_str] = templ

    vals["request"] = request

    headers = {
        "mimetype": content_type,
        "Date": int(round(time.time() * 1000)),
        "Cache-Control": "no-cache",
    }

    try:
        template_str = templ.render(vals)
    except BaseException:
        raise BadRequest(f"Problem rendering template: {traceback.format_exc()}")

    return Response(template_str, status_code, headers)


def hh_range(caches, start_date, finish_date):
    try:
        return caches["utils"]["hh_range"][start_date][finish_date]
    except KeyError:
        try:
            utils_cache = caches["utils"]
        except KeyError:
            utils_cache = caches["utils"] = {}

        try:
            ranges_cache = utils_cache["hh_range"]
        except KeyError:
            ranges_cache = utils_cache["hh_range"] = {}

        try:
            range_start_cache = ranges_cache[start_date]
        except KeyError:
            range_start_cache = ranges_cache[start_date] = {}

        try:
            datetime_cache = utils_cache["datetime"]
        except KeyError:
            datetime_cache = utils_cache["datetime"] = {}

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


ct = timezone("Europe/London")
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


def ct_datetime_now():
    return to_ct(utc_datetime_now())


def utc_datetime_parse(date_str, format_str):
    return Datetime.strptime(date_str, format_str).replace(tzinfo=utc)


def ct_datetime_parse(date_str, format_str):
    return to_ct(Datetime.strptime(date_str, format_str))


def u_months_u(
    start_year=None, start_month=None, finish_year=None, finish_month=None, months=1
):

    if start_year is None:
        start = utc_datetime(finish_year, finish_month) - relativedelta(
            months=months - 1
        )
    else:
        start = utc_datetime(start_year, start_month)

    if finish_year is None:
        if months is None:
            finish = None
        else:
            finish = start + relativedelta(months=months) - HH
    else:
        finish = utc_datetime(finish_year, finish_month) + MONTH - HH

    dt = start
    while hh_before(dt, finish):
        yield dt, dt + MONTH - HH
        dt += MONTH


def c_months_u(
    start_year=None, start_month=None, finish_year=None, finish_month=None, months=1
):

    for c_m_start_c, c_m_finish_c in c_months_c(
        start_year=start_year,
        start_month=start_month,
        finish_year=finish_year,
        finish_month=finish_month,
        months=months,
    ):
        yield to_utc(c_m_start_c), to_utc(c_m_finish_c)


def c_months_c(
    start_year=None, start_month=None, finish_year=None, finish_month=None, months=1
):

    for u_m_start_u, u_m_finish_u in u_months_u(
        start_year=start_year,
        start_month=start_month,
        finish_year=finish_year,
        finish_month=finish_month,
        months=months,
    ):
        c_m_start_c = ct_datetime(u_m_start_u.year, u_m_start_u.month)
        c_m_finish_c = ct_datetime(
            u_m_finish_u.year, u_m_finish_u.month, u_m_finish_u.day, 23, 30
        )

        yield c_m_start_c, c_m_finish_c


def csv_make_val(v):
    if isinstance(v, (Set, list)):
        if len(v) == 1:
            return csv_make_val(next(iter(v)))
        elif 1 < len(v) < 4:
            vals = set(str(csv_make_val(val)) for val in v)
            return " | ".join(sorted(vals))
        else:
            return ""
    elif isinstance(v, Datetime):
        return hh_format(v)
    elif v is None:
        return ""
    else:
        return v


def make_val(v):
    if isinstance(v, (Set, list)):
        if len(v) == 1:
            return make_val(next(iter(v)))
        elif 1 < len(v) < 4:
            vals = set(str(csv_make_val(val)) for val in v)
            return " | ".join(sorted(vals))
        else:
            return None
    elif isinstance(v, Datetime):
        return to_ct(v)
    else:
        return v


class PropDict(Mapping):
    def __init__(self, location, rate_dict, parent_keys=None):
        if not isinstance(rate_dict, Mapping):
            raise Exception(
                f"The rate_dict must be a mapping, but got a {type(rate_dict)} with "
                f"value {rate_dict}"
            )
        self._location = location
        self._parent_keys = [] if parent_keys is None else parent_keys
        storage = {}
        for k, v in rate_dict.items():
            if isinstance(v, Mapping):
                storage[k] = PropDict(location, v, self._parent_keys + [k])
            else:
                storage[k] = v
                if isinstance(v, list):
                    for i, val in enumerate(tuple(v)):
                        if isinstance(val, Mapping):
                            v[i] = PropDict(
                                location,
                                val,
                                self._parent_keys + ["<list item " + str(i) + ">"],
                            )
        self._storage = storage

    def __getitem__(self, key):
        try:
            return self._storage[key]
        except KeyError:
            try:
                return self._storage["*"]
            except KeyError:
                raise KeyError(
                    f"Can't find the the key {self._parent_keys + [key]} or the "
                    f"wildcard {self._parent_keys + ['*']} in {self._location}"
                )

    def __iter__(self):
        return iter(self._storage)

    def __len__(self):
        return len(self._storage)


def reduce_bill_hhs(bill_hhs):
    bill = {}
    for bill_hh in bill_hhs.values():
        for k, v in bill_hh.items():
            if isinstance(v, set):
                if k in bill:
                    bill[k].update(v)
                else:
                    bill[k] = v

            else:
                try:
                    bill[k] += v
                except KeyError:
                    bill[k] = v
                except TypeError as e:
                    raise BadRequest(
                        f"For bill[{k}] {bill[k]} the value {v} can't be added on. {e} "
                        f"{traceback.format_exc()}"
                    )

    return bill


def write_row(writer, *vals):
    writer.writerow(csv_make_val(v) for v in vals)
