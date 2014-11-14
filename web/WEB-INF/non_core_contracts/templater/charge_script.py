from jinja2 import Template, Environment, PackageLoader
import time
from datetime import datetime
import sys
import traceback
from net.sf.chellow.monad import Monad

Monad.getUtils()['impt'](globals(), 'utils')
UserException = utils.UserException


FORMATS = {'year': '%Y', 'month': '%m', 'day': '%d', 'hour': '%H',
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
    {%- if request.getParameter(year_field) -%}
      {{ request.getParameter(year_field) }}
    {%- else -%}
      {{ initial|hh_format('year') }}
    {%- endif %}">

  {%- if resolution in ['month', 'day', 'hour', 'minute'] -%}
    -<select name="{{ month_field }}">
    {% for month in range(1, 13) -%}
      <option value="{{ "%02i"|format(month) }}"
        {%- if request.getParameter(month_field) -%}
          {%- if request.getParameter(month_field)|int == month %} selected
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
          {%- if request.getParameter(day_field) -%}
            {%- if request.getParameter(day_field)|int == day %} selected
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
          {%- if request.getParameter(hour_field) -%}
            {%- if request.getParameter(hour_field)|int == hour %} selected
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
          {%- if request.getParameter(minute_field) %}
            {%- if request.getParameter(minute_field)|int == minute %} selected
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
        {%- if request.getParameter(name) -%}
            {%- if request.getParameter(name) == '' ~ item_id %} selected{% endif -%}
        {%- else -%}
            {%- if initial == item_id %} selected{% endif -%}
            {%- endif -%}>{{ desc }}</option>
{%- endmacro -%}

{% macro input_text(name, initial=None, size=None, maxlength=None) %}
    <input name="{{ name }}" value="
        {%- if request.getParameter(name) -%}
            {{ request.getParameter(name) }}
        {%- elif initial is not none -%}
            {{initial}}
        {%- endif -%}"
        {%- if size %} size="{{ size }}"{% endif %}
        {%- if maxlength %} maxlength="{{ maxlength }}"{% endif %}>
{%- endmacro -%}

{% macro input_textarea(name, initial, rows, cols) -%}
  <textarea name="{{ name }}" rows="{{ rows }}" cols="{{ cols }}">
    {%- if request.getParameter(name) -%}
      {{ request.getParameter(name) }}
    {%- else -%}
      {{ initial }}
    {%- endif -%}
  </textarea>      
{%- endmacro -%}

{%- macro input_checkbox(name, initial) %}
    <input type="checkbox" name="{{ name }}" value="true"
                {%- if request.getParameter(name) -%}
                    {%- if request.getParameter(name) == 'true' %} checked{% endif -%}
                {%- else -%}
                    {%- if initial == True %} checked{% endif -%}
                    {%- endif -%}>
{%- endmacro -%}
'''

def hh_format_filter(dt, modifier='full'):
    return "Ongoing" if dt is None else dt.strftime(FORMATS[modifier])

def now_if_none(dt):
    if dt is None:
        return datetime.utcnow()
    else:
        return dt

env = Environment(autoescape=True)

env.filters['hh_format'] = hh_format_filter
env.filters['now_if_none'] = now_if_none

# to use: Monad.getContext().getAttribute('net.sf.chellow.jinja').get("render")(inv, template, vals)

template_cache = {}

def render(inv, template, vals, status_code=200, content_type='text/html'):
    if len(template_cache) > 10000:
        template_cache.clear()
    templ_str = prefix + template
    try:
        templ = template_cache[templ_str]
    except KeyError:
        templ = env.from_string(templ_str)
        template_cache[templ_str] = templ

    vals['request'] = inv.getRequest()

    if sys.platform.startswith('java'):
        vals['context_path'] = inv.getRequest().getContextPath()
        res = inv.getResponse()
        res.setContentType(content_type)
        res.setDateHeader("Date", int(round(time.time() * 1000)))
        res.setHeader("Cache-Control", "no-cache")
        res.setStatus(status_code)
        writer = res.getWriter()
        writer.write(templ.render(vals))
        writer.close()
    else:
        from flask import Response

        vals['context_path'] = '/chellow'
       
        headers = {
            'mimetype': content_type,
            'Date': int(round(time.time() * 1000)),
            'Cache-Control': 'no-cache'}

        try:
            template_str = templ.render(vals)
        except:
            raise UserException(
                "Problem rendering template: " + traceback.format_exc())

        inv.response = Response(template_str, status_code, headers)
