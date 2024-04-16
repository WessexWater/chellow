import datetime
import traceback
from datetime import timedelta as Timedelta

from sqlalchemy import select

from werkzeug.exceptions import BadRequest

import xlrd

from zish import loads

from chellow.models import Contract, RateScript
from chellow.utils import HH, ct_datetime, hh_format, to_ct, to_utc


def key_format(dt):
    return dt.strftime("%d %H:%M")


def hh(data_source):
    for h in data_source.hh_data:
        try:
            sbp, ssp = data_source.caches["system_price"][h["start-date"]]
        except KeyError:
            try:
                system_price_cache = data_source.caches["system_price"]
            except KeyError:
                system_price_cache = data_source.caches["system_price"] = {}

            h_start = h["start-date"]
            rates = data_source.non_core_rate("system_price", h_start)[
                "gbp_per_nbp_mwh"
            ]

            try:
                try:
                    rdict = rates[key_format(h_start)]
                except KeyError:
                    rdict = rates[key_format(h_start - Timedelta(days=3))]
                sbp = float(rdict["sbp"] / 1000)
                ssp = float(rdict["ssp"] / 1000)
                system_price_cache[h_start] = (sbp, ssp)
            except KeyError:
                raise BadRequest(
                    f"For the System Price rate script at {hh_format(h_start)} "
                    f"the rate cannot be found."
                )
            except TypeError:
                raise BadRequest(
                    f"For the System Price rate script at {hh_format(h_start)} "
                    f"the rate 'rates_gbp_per_mwh' has the problem: "
                    f"{traceback.format_exc()}"
                )

        h["sbp"] = sbp
        h["sbp-gbp"] = h["nbp-kwh"] * sbp

        h["ssp"] = ssp
        h["ssp-gbp"] = h["nbp-kwh"] * ssp


def elexon_import(sess, log, set_progress, s, scripting_key):
    log("Starting to check System Prices.")
    contract_name = "system_price"
    contract = Contract.find_non_core_by_name(sess, contract_name)
    if contract is None:
        contract = Contract.insert_non_core(
            sess,
            contract_name,
            "",
            {"enabled": True},
            to_utc(ct_datetime(1996, 4, 1)),
            None,
            {},
        )
        sess.commit()
    contract_props = contract.make_properties()

    if not contract_props.get("enabled", False):
        log(
            "The automatic importer is disabled. To enable it, edit "
            "the contract properties to set 'enabled' to True."
        )
        return

    for rscript in sess.scalars(
        select(RateScript)
        .where(RateScript.contract == contract)
        .order_by(RateScript.start_date.desc())
    ):
        ns = loads(rscript.script)
        rates = ns.get("gbp_per_nbp_mwh", {})
        if len(rates) == 0:
            fill_start = rscript.start_date
            break
        elif rates[key_format(rscript.finish_date)]["run"] == "DF":
            fill_start = rscript.finish_date + HH
            break
    params = {"key": scripting_key}
    url = "https://downloads.elexonportal.co.uk/file/download/BESTVIEWPRICES_FILE"

    log(
        f"Downloading from {url}?key={scripting_key} and extracting data from "
        f"{hh_format(fill_start)}"
    )

    sess.rollback()  # Avoid long-running transactions
    res = s.get(url, params=params)
    log(f"Received {res.status_code} {res.reason}")
    data = res.content
    book = xlrd.open_workbook(file_contents=data)
    sbp_sheet = book.sheet_by_index(1)
    ssp_sheet = book.sheet_by_index(2)

    sp_months = []
    sp_month = None
    for row_index in range(1, sbp_sheet.nrows):
        sbp_row = sbp_sheet.row(row_index)
        ssp_row = ssp_sheet.row(row_index)
        raw_date = datetime.datetime(
            *xlrd.xldate_as_tuple(sbp_row[0].value, book.datemode)
        )
        hh_date_ct = to_ct(raw_date)
        hh_date = to_utc(hh_date_ct)
        run_code = sbp_row[1].value
        for col_idx in range(2, 52):
            if hh_date >= fill_start:
                sbp_val = sbp_row[col_idx].value
                if sbp_val != "":
                    if hh_date.day == 1 and hh_date.hour == 0 and hh_date.minute == 0:
                        sp_month = {}
                        sp_months.append(sp_month)
                    ssp_val = ssp_row[col_idx].value
                    if sp_month is not None:
                        sp_month[hh_date] = {
                            "run": run_code,
                            "sbp": sbp_val,
                            "ssp": ssp_val,
                        }
            hh_date += HH
    log("Successfully extracted data.")
    last_date = sorted(sp_months[-1].keys())[-1]
    if last_date.month == (last_date + HH).month:
        del sp_months[-1]
    if "limit" in contract_props:
        sp_months = sp_months[0:1]
    for sp_month in sp_months:
        sorted_keys = sorted(sp_month.keys())
        month_start = sorted_keys[0]
        month_finish = sorted_keys[-1]
        rs = (
            sess.query(RateScript)
            .filter(
                RateScript.contract == contract,
                RateScript.start_date == month_start,
            )
            .first()
        )
        if rs is None:
            log(f"Adding a new rate script starting at {hh_format(month_start)}.")

            latest_rs = (
                sess.query(RateScript)
                .filter(RateScript.contract == contract)
                .order_by(RateScript.start_date.desc())
                .first()
            )

            contract.update_rate_script(
                sess,
                latest_rs,
                latest_rs.start_date,
                month_finish,
                loads(latest_rs.script),
            )
            rs = contract.insert_rate_script(sess, month_start, {})
            sess.flush()
        script = {
            "gbp_per_nbp_mwh": dict((key_format(k), v) for k, v in sp_month.items())
        }
        log(f"Updating rate script starting at {hh_format(month_start)}.")
        contract.update_rate_script(sess, rs, rs.start_date, rs.finish_date, script)
        sess.commit()
