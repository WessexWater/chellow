from sqlalchemy import select


from chellow.models import Contract, RateScript
from chellow.national_grid import api_get
from chellow.utils import (
    ct_datetime,
    to_utc,
)


BANDED_START = to_utc(ct_datetime(2023, 4, 1))


def hh(ds):
    for hh in ds.hh_data:
        if hh["start-date"] >= BANDED_START:
            _process_banded_hh(ds, hh)


BAND_LOOKUP = {
    "Domestic Aggregated (Related MPAN)": "Domestic",
    "Domestic Aggregated with Residual": "Domestic",
    "HV Generation Site Specific": "HV1",
    "HV Generation Site Specific no RP charge": "HV1",
    "HV Site Specific Band 1": "HV1",
    "HV Site Specific Band 2": "HV2",
    "HV Site Specific Band 3": "HV3",
    "HV Site Specific Band 4": "HV4",
    "HV Site Specific No Residual": "HV1",
    "LV Generation Aggregated": "LV1",
    "LV Generation Site Specific": "LV1",
    "LV Generation Site Specific no RP charge": "LV1",
    "LV Site Specific Band 1": "LV1",
    "LV Site Specific Band 2": "LV2",
    "LV Site Specific Band 3": "LV3",
    "LV Site Specific Band 4": "LV4",
    "LV Site Specific No Residual": "LV1",
    "LV Sub Generation Aggregated": "LV1",
    "LV Sub Generation Site Specific": "LV1",
    "LV Sub Generation Site Specific no RP charge": "LV1",
    "LV Sub Site Specific Band 1": "LV1",
    "LV Sub Site Specific Band 2": "LV2",
    "LV Sub Site Specific Band 3": "LV3",
    "LV Sub Site Specific Band 4": "LV4",
    "LV Sub Site Specific No Residual": "LV1",
    "Non-Domestic Aggregated (related MPAN)": "LV_NoMIC_1",
    "Non-Domestic Aggregated Band 1": "LV_NoMIC_1",
    "Non-Domestic Aggregated Band 2": "LV_NoMIC_2",
    "Non-Domestic Aggregated Band 3": "LV_NoMIC_3",
    "Non-Domestic Aggregated Band 4": "LV_NoMIC_4",
    "Non-Domestic Aggregated No Residual": "LV_NoMIC_1",
    "Unmetered Supplies": "Unmetered",
    "Designated EHV0": "EHV1",
    "Designated EHV1": "EHV1",
    "Designated EHV2": "EHV2",
    "Designated EHV3": "EHV3",
    "Designated EHV4": "EHV4",
}


def _process_banded_hh(ds, hh):
    rates = ds.non_core_rate("tnuos", hh["start-date"])
    band_code = BAND_LOOKUP[hh["duos-description"]]
    hh["tnuos-band"] = band_code
    if hh["ct-decimal-hour"] == 12:
        rate = float(rates["bands"][band_code]["TDR Tariff"])
        hh["tnuos-rate"] = rate
        if band_code == "Unmetered":
            hh["tnuos-gbp"] = rate / 100 * ds.sc / 365
        else:
            hh["tnuos-gbp"] = rate
        hh["tnuos-days"] = 1


def national_grid_import(sess, log, set_progress, s):
    log("Starting to check for new TNUoS TDR Tariffs")

    contract = Contract.get_non_core_by_name(sess, "tnuos")

    params = {"sql": """SELECT * FROM "dcca94fd-343e-4d4e-8c5d-66009dec4ad3" """}
    res_j = api_get(s, "datastore_search_sql", params=params)
    for record in res_j["result"]["records"]:
        # {
        #   "_id": 1,
        #   "Publication": "Final",
        #   "Year_FY": 2024,
        #   "Published_Date": "2023-02-14",
        #   "TDR Band": "Domestic",
        #   "TDR Tariff": 0.119264,
        #   "Notes": "Domestic"
        # },
        fy_year = int(record["Year_FY"]) - 1
        fy_start = to_utc(ct_datetime(fy_year, 4, 1))
        if fy_start < contract.start_rate_script.start_date:
            continue

        rs = sess.execute(
            select(RateScript).where(
                RateScript.contract == contract,
                RateScript.start_date == fy_start,
            )
        ).scalar_one_or_none()
        if rs is None:
            rs = contract.insert_rate_script(sess, fy_start, {})

        rs_script = rs.make_script()
        try:
            bands = rs_script["bands"]
        except KeyError:
            bands = rs_script["bands"] = {}

        record_key = record["TDR Band"]
        record_published_date = record["Published_Date"]

        band = bands.get(record_key)
        if band is None or band["Published_Date"] < record_published_date:
            if "TDR Tariff" not in record:
                tdr_tariff = [
                    v for k, v in record.items() if k.startswith("TDR Tariff")
                ][0]
                record["TDR Tariff"] = tdr_tariff
            bands[record_key] = record
            rs.update(rs_script)
            sess.commit()

    log("Finished TNUoS TDR Tariffs")
    sess.commit()
