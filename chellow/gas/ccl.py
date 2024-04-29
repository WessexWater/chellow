import json
from decimal import Decimal
from io import BytesIO

from sqlalchemy import select

from chellow.gas.engine import g_rates
from chellow.models import GContract, GRateScript
from chellow.rate_server import download
from chellow.utils import ct_datetime, hh_format, to_utc


DAILY_THRESHOLD = 145


def vb(ds):
    for hh in ds.hh_data:
        rate = float(
            g_rates(ds.sess, ds.caches, "ccl", hh["start_date"], True)[
                "ccl_gbp_per_kwh"
            ]
        )

        hh["ccl"] = rate


def rate_server_import(sess, log, set_progress, s, paths):
    log("Starting to check for new gas CCL rates")
    g_contract_name = "ccl"
    g_contract = GContract.find_industry_by_name(sess, g_contract_name)
    if g_contract is None:
        g_contract = GContract.insert_industry(
            sess,
            g_contract_name,
            "",
            {"enabled": True},
            to_utc(ct_datetime(1996, 4, 1)),
            None,
            {},
        )
        sess.commit()
    g_contract_props = g_contract.make_properties()

    if not g_contract_props.get("enabled", False):
        log(
            "The automatic importer is disabled. To enable it, edit "
            "the contract properties to set 'enabled' to true."
        )
        return

    year_entries = {}
    for path, url in paths:
        if len(path) == 4:
            year, utility, rate_type, file_name = path
            if utility == "gas" and rate_type == "ccl":
                try:
                    fl_entries = year_entries[year]
                except KeyError:
                    fl_entries = year_entries[year] = {}

                fl_entries[file_name] = url

    for year, year_files in sorted(year_entries.items()):
        year_start = to_utc(ct_datetime(year, 4, 1))
        if year_start < g_contract.start_g_rate_script.start_date:
            continue
        rs = sess.execute(
            select(GRateScript).where(
                GRateScript.g_contract == g_contract,
                GRateScript.start_date == year_start,
            )
        ).scalar_one_or_none()
        if rs is None:
            rs = g_contract.insert_g_rate_script(sess, year_start, {})

        if len(year_files) > 0:
            file_name, url = sorted(year_files.items())[-1]

            rs_script = rs.make_script()
            if rs_script.get("a_file_name") != file_name:
                log(
                    f"Found new file {file_name} for rate script starting "
                    f"{hh_format(year_start)}"
                )
                script = {"a_file_name": file_name}
                server_j = json.load(BytesIO(download(s, url)))
                script["ccl_gbp_per_kwh"] = Decimal(server_j["ccl_gbp_per_kwh"])
                rs.update(script)
                log(f"Updated CCL rate script for {hh_format(year_start)}")

    log("Finished CCL rates")
    sess.commit()
