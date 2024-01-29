import csv
from decimal import Decimal

from dateutil.relativedelta import relativedelta


from werkzeug.exceptions import BadRequest

from zish import loads

from chellow.models import Contract, RateScript
from chellow.utils import (
    ct_datetime_parse,
    hh_format,
    to_utc,
    u_months_u,
    utc_datetime_now,
)


ELEXON_PORTAL_SCRIPTING_KEY_KEY = "elexonportal_scripting_key"


def hh(data_source):
    try:
        cache = data_source.caches["rcrc"]
    except KeyError:
        cache = data_source.caches["rcrc"] = {}

    for hh in data_source.hh_data:
        try:
            hh["rcrc-rate"] = rcrc = cache[hh["start-date"]]
        except KeyError:
            h_start = hh["start-date"]
            rates = data_source.non_core_rate("rcrc", h_start)["rates"]
            try:
                hh["rcrc-rate"] = rcrc = cache[h_start] = (
                    float(rates[key_format(h_start)]) / 1000
                )
            except KeyError:
                try:
                    dt = h_start - relativedelta(days=3)
                    hh["rcrc-rate"] = rcrc = cache[h_start] = (
                        float(rates[key_format(dt)]) / 1000
                    )
                except KeyError:
                    raise BadRequest(
                        f"For the RCRC rate script at {hh_format(dt)} the rate cannot "
                        f"be found."
                    )

        hh["rcrc-kwh"] = hh["nbp-kwh"]
        hh["rcrc-gbp"] = hh["nbp-kwh"] * rcrc


def key_format(dt):
    return dt.strftime("%d %H:%M Z")


def _find_month(lines, month_start, month_finish):
    parser = csv.reader(lines, delimiter=",", quotechar='"')
    next(parser)
    next(parser)
    month_rcrcs = {}
    for values in parser:
        if len(values) == 0:
            continue
        date_str = values[0]
        if "/" in date_str:
            pattern = "%d/%m/%Y"
        elif " " in date_str:
            pattern = "%d %b %Y"
        else:
            raise BadRequest(f"Date format {date_str} not recognized.")
        hh_date = to_utc(ct_datetime_parse(date_str, pattern))
        hh_date += relativedelta(minutes=30 * int(values[2]))
        if month_start <= hh_date <= month_finish:
            month_rcrcs[key_format(hh_date)] = Decimal(values[3])
    return month_rcrcs


def elexon_import(sess, log, set_progress, s, scripting_key):
    log("Starting to check RCRCs.")
    contract = Contract.get_non_core_by_name(sess, "rcrc")
    latest_rs = (
        sess.query(RateScript)
        .filter(RateScript.contract_id == contract.id)
        .order_by(RateScript.start_date.desc())
        .first()
    )
    latest_rs_id = latest_rs.id
    latest_rs_start = latest_rs.start_date

    months = list(
        u_months_u(
            start_year=latest_rs_start.year, start_month=latest_rs_start.month, months=2
        )
    )
    month_start, month_finish = months[1]
    now = utc_datetime_now()
    if now > month_finish:
        params = {"key": scripting_key}
        url_str = "https://downloads.elexonportal.co.uk/file/download/RCRC_FILE"
        log(
            f"Downloading {url_str}?key={scripting_key} to see if data is available "
            f"from {hh_format(month_start)} to {hh_format(month_finish)}."
        )

        sess.rollback()  # Avoid long-running transaction
        r = s.get(url_str, timeout=120, params=params)
        month_rcrcs = _find_month(
            (x.decode() for x in r.iter_lines()), month_start, month_finish
        )
        if key_format(month_finish) in month_rcrcs:
            log("The whole month's data is there.")
            script = {"rates": month_rcrcs}
            contract = Contract.get_non_core_by_name(sess, "rcrc")
            rs = RateScript.get_by_id(sess, latest_rs_id)
            contract.update_rate_script(
                sess, rs, rs.start_date, month_finish, loads(rs.script)
            )
            contract.insert_rate_script(sess, month_start, script)
            sess.commit()
            log(f"Added a new rate script starting at {hh_format(month_start)}.")
        else:
            msg = "There isn't a whole month there yet."
            if len(month_rcrcs) > 0:
                msg += f" The last date is {sorted(month_rcrcs.keys())[-1]}"
            log(msg)
