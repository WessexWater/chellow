import json

from decimal import Decimal
from io import BytesIO

from sqlalchemy import select
from chellow.models import Contract, RateScript
from chellow.rate_server import download
from chellow.utils import ct_datetime, hh_format, to_utc


def hh(supply_source):
    try:
        ro_cache = supply_source.caches["ro"]
    except KeyError:
        ro_cache = supply_source.caches["ro"] = {}

    for hh in supply_source.hh_data:
        try:
            hh["ro-rate"] = ro_rate = ro_cache[hh["start-date"]]
        except KeyError:
            h_start = hh["start-date"]
            hh["ro-rate"] = ro_rate = ro_cache[h_start] = float(
                supply_source.non_core_rate("ro", h_start)["ro_gbp_per_msp_kwh"]
            )

        ro_kwh = hh["msp-kwh"]
        hh["ro-msp-kwh"] = ro_kwh
        hh["ro-kwh"] = ro_kwh
        hh["ro-gbp"] = ro_kwh * ro_rate


def rate_server_import(sess, log, set_progress, s, paths):
    log("Starting to check for new electricity RO rates")
    contract_name = "ro"
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

    if not contract_props.get("enabled", True):
        log(
            "The automatic importer is disabled. To enable it, edit "
            "the contract properties to set 'enabled' to true."
        )
        return

    year_entries = {}
    for path, url in paths:
        if len(path) == 4:
            year, utility, rate_type, file_name = path
            if utility == "electricity" and rate_type == "ro":
                try:
                    fl_entries = year_entries[year]
                except KeyError:
                    fl_entries = year_entries[year] = {}

                fl_entries[file_name] = url

    for year, year_files in sorted(year_entries.items()):
        year_start = to_utc(ct_datetime(year, 4, 1))
        if year_start < contract.start_rate_script.start_date:
            continue
        rs = sess.execute(
            select(RateScript).where(
                RateScript.contract == contract,
                RateScript.start_date == year_start,
            )
        ).scalar_one_or_none()
        if rs is None:
            rs = contract.insert_rate_script(sess, year_start, {})

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
                script["ro_gbp_per_msp_kwh"] = Decimal(server_j["ro_gbp_per_msp_kwh"])
                rs.update(script)
                log(f"Updated RO rate script for {hh_format(year_start)}")

    log("Finished RO rates")
    sess.commit()
