from dateutil.relativedelta import relativedelta

from sqlalchemy import func, select
from sqlalchemy.sql.expression import true

from werkzeug.exceptions import BadRequest

from chellow.models import Channel, Era, HhDatum, Laf, Llfc, Party
from chellow.utils import (
    HH,
    c_months_u,
    ct_datetime,
    hh_format,
    to_utc,
    utc_datetime,
)


BANDS = ("super-red", "red", "amber", "green")

KEYS = dict(
    (
        band,
        {
            "kwh": f"duos-{band}-kwh",
            "tariff-rate": f"{band}-gbp-per-kwh",
            "bill-rate": f"duos-{band}-rate",
            "gbp": f"duos-{band}-gbp",
        },
    )
    for band in BANDS
)

VL_LOOKUP = {
    "LV": {True: "lv-sub", False: "lv-net"},
    "HV": {True: "hv", False: "hv"},
    "EHV": {True: "ehv", False: "ehv"},
}


def datum_beginning_22(ds, hh):
    dno_rates = ds.hh_rate(ds.dno_contract.id, hh["start-date"])
    try:
        tariff = dno_rates["tariffs"][ds.llfc_code]
        lafs = dno_rates["lafs"][VL_LOOKUP[ds.voltage_level_code][ds.is_substation]]
    except KeyError as e:
        raise BadRequest(str(e))

    if ds.is_import:
        try:
            day_rate = float(tariff["day-gbp-per-kwh"])
        except KeyError as e:
            raise BadRequest(str(e))

        night_rate = float(tariff["night-gbp-per-kwh"])
        if 6 < hh["ct-decimal-hour"] <= 23:
            hh["duos-day-kwh"] = hh["msp-kwh"]
            hh["duos-day-gbp"] = hh["msp-kwh"] * day_rate
        else:
            hh["duos-night-kwh"] = hh["msp-kwh"]
            hh["duos-night-gbp"] = hh["msp-kwh"] * night_rate

    if 23 < hh["ct-decimal-hour"] <= 6:
        slot_name = "night"
    elif hh["ct-day-of-week"] < 5 and (hh["ct-month"] > 10 or hh["ct-month"] < 3):
        if 15.5 < hh["ct-decimal-hour"] < 18:
            slot_name = "winter-weekday-peak"
        elif 6 < hh["ct-decimal-hour"] < 15:
            slot_name = "winter-weekday-day"
        else:
            slot_name = "other"
    else:
        slot_name = "other"

    try:
        hh["laf"] = float(lafs[slot_name])
    except KeyError as e:
        raise BadRequest(str(e))

    hh["gsp-kwh"] = hh["laf"] * hh["msp-kwh"]
    hh["gsp-kw"] = hh["gsp-kwh"] * 2

    if hh["ct-is-month-end"]:
        month_to = hh["start-date"]
        month_from = month_to - relativedelta(months=1) + HH
        days_in_month = 0
        md_kva = 0
        month_imp_kvarh = 0
        month_kwh = 0
        for dsc in ds.get_data_sources(month_from, month_to):
            for h in dsc.hh_data:
                if h["ct-decimal-hour"] == 0:
                    days_in_month += 1
                md_kva = max(md_kva, (h["msp-kw"] ** 2 + h["imp-msp-kvar"] ** 2) ** 0.5)
                month_imp_kvarh += h["imp-msp-kvarh"]
                month_kwh += h["msp-kwh"]

        tariff = ds.hh_rate(ds.dno_contract.id, hh["start-date"])["tariffs"][
            ds.llfc_code
        ]
        try:
            reactive_rate = float(tariff["reactive-gbp-per-kvarh"])
        except KeyError as e:
            raise BadRequest(str(e))
        hh["duos-reactive-rate"] = reactive_rate

        if not ds.is_displaced:
            hh["duos-availability-kva"] = ds.sc
            hh["duos-excess-availability-kva"] = max(md_kva - ds.sc, 0)
            for prefix in ["", "excess-"]:
                tariff_key = prefix + "gbp-per-kva-per-day"
                if tariff_key in tariff:
                    rate_key = "duos-" + prefix + "availability-rate"
                    hh[rate_key] = float(tariff[tariff_key])
                    hh["duos-" + prefix + "availability-days"] = days_in_month
                    hh["duos-" + prefix + "availability-gbp"] = (
                        hh[rate_key]
                        * hh["duos-" + prefix + "availability-kva"]
                        * hh["duos-" + prefix + "availability-days"]
                    )

        hh["duos-reactive-gbp"] = (
            max(0, month_imp_kvarh - month_kwh / 2) * reactive_rate
        )


def datum_beginning_20(ds, hh):
    tariff = None
    dno_rates = ds.hh_rate(ds.dno_contract.id, hh["start-date"])
    for k, tf in dno_rates["tariffs"].items():
        if ds.llfc_code in [cd.strip() for cd in k.split(",")]:
            tariff = tf

    if tariff is None:
        raise BadRequest(
            "The tariff for the LLFC "
            + ds.llfc_code
            + " cannot be found for the DNO 20 at "
            + hh_format(hh["start-date"])
            + "."
        )

    lafs = dno_rates["lafs"][ds.voltage_level_code.lower()]

    try:
        day_rate = float(tariff["day-gbp-per-kwh"])
    except KeyError as e:
        raise BadRequest(str(e))

    if "night-gbp-per-kwh" in tariff:
        night_rate = float(tariff["night-gbp-per-kwh"])
        if 0 < hh["ct-decimal-hour"] <= 7:
            hh["duos-night-kwh"] = hh["msp-kwh"]
            hh["duos-night-gbp"] = hh["msp-kwh"] * night_rate
        else:
            hh["duos-day-kwh"] = hh["msp-kwh"]
            hh["duos-day-gbp"] = hh["msp-kwh"] * day_rate
    else:
        hh["duos-day-kwh"] = hh["msp-kwh"]
        hh["duos-day-gbp"] = hh["msp-kwh"] * day_rate

    if 0 < hh["ct-decimal-hour"] <= 7:
        slot_name = "night"
    elif (
        hh["ct-day-of-week"] < 5
        and 16 < hh["ct-decimal-hour"] <= 19
        and (hh["ct-month"] > 10 or hh["ct-month"] < 3)
    ):
        slot_name = "peak"
    elif (
        7 > hh["ct-day-of-week"] > 1
        and (7 < hh["ct-decimal-hour"] < 15 or 18.5 < hh["ct-decimal-hour"] < 19)
        and (hh["ct-month"] > 11 or hh["ct-month"] < 4)
    ):
        slot_name = "winter-weekday"
    else:
        slot_name = "other"
    hh["laf"] = float(lafs[slot_name])
    hh["gsp-kwh"] = hh["laf"] * hh["msp-kwh"]
    hh["gsp-kw"] = hh["gsp-kwh"] * 2

    if hh["ct-is-month-end"]:
        tariff = None
        for k, tf in dno_rates["tariffs"].items():
            if ds.llfc_code in map(str.strip, k.split(",")):
                tariff = tf
                break
        if tariff is None:
            raise BadRequest(
                "The tariff for the LLFC "
                + ds.llfc_code
                + " cannot be found for the DNO 20 at "
                + hh_format(hh["start-date"])
                + "."
            )
        if not ds.is_displaced:
            year_md_kva_095 = year_md_095(ds, ds.finish_date)

            hh["duos-excess-availability-kva"] = max(year_md_kva_095 - ds.sc, 0)
            billed_avail = max(ds.sc, year_md_kva_095)
            hh["duos-availability-kva"] = ds.sc

            for threshold, block in [
                (15, 15),
                (100, 5),
                (250, 10),
                (500, 25),
                (1000, 50),
                (None, 100),
            ]:
                if threshold is None or billed_avail < threshold:
                    if billed_avail % block > 0:
                        billed_avail = (int(billed_avail / block) + 1) * block
                    break
            try:
                le_200_avail_rate = float(
                    tariff["capacity-<=200-gbp-per-kva-per-month"]
                )
            except KeyError as e:
                raise BadRequest(str(e))

            hh["duos-availability-gbp"] = min(200, billed_avail) * le_200_avail_rate

            if billed_avail > 200:
                try:
                    gt_200_avail_rate = float(
                        tariff["capacity->200-gbp-per-kva-per-month"]
                    )
                except KeyError as e:
                    raise BadRequest(str(e))

                hh["duos-availability-gbp"] += (billed_avail - 200) * gt_200_avail_rate

        try:
            if "fixed-gbp-per-month" in tariff:
                hh["duos-standing-gbp"] = float(tariff["fixed-gbp-per-month"])
            else:
                hh["duos-standing-gbp"] = (
                    float(tariff["fixed-gbp-per-day"]) * hh["utc-day"]
                )
        except KeyError as e:
            raise BadRequest(str(e))


def year_md_095(data_source, finish):
    if data_source.site is None:
        return year_md_095_supply(data_source, finish)
    else:
        return year_md_095_site(data_source, finish)


def year_md_095_supply(ds, finish):
    supply = ds.supply
    sess = ds.sess
    md_kva = 0
    month_finish = finish - relativedelta(months=11)

    while not month_finish > finish:
        month_start = month_finish - relativedelta(months=1) + HH
        month_kwh_result = (
            sess.query(func.sum(HhDatum.value), func.max(HhDatum.value))
            .join(Channel)
            .join(Era)
            .filter(
                Era.supply == supply,
                HhDatum.start_date >= month_start,
                HhDatum.start_date <= month_finish,
                Channel.channel_type == "ACTIVE",
                Channel.imp_related == true(),
            )
            .one()
        )

        if month_kwh_result[0] is not None:
            month_md_kw = float(month_kwh_result[1]) * 2
            month_kwh = float(month_kwh_result[0])
            month_kvarh = (
                sess.query(func.sum(HhDatum.value))
                .join(Channel)
                .join(Era)
                .filter(
                    Era.supply == supply,
                    HhDatum.start_date >= month_start,
                    HhDatum.start_date <= month_finish,
                    Channel.channel_type == "REACTIVE_IMP",
                    Channel.imp_related == true(),
                )
                .one()[0]
            )
            if month_kvarh is None:
                pf = 0.95
            else:
                month_kvarh = float(month_kvarh)
                if month_kwh == 0 and month_kvarh == 0:
                    pf = 1
                else:
                    pf = month_kwh / (month_kwh**2 + month_kvarh**2) ** 0.5
            month_kva = month_md_kw / pf
            md_kva = max(md_kva, month_kva)
        month_finish += relativedelta(months=1)
    return md_kva


def year_md_095_site(data_source, finish, pw):
    md_kva = 0
    month_finish = finish - relativedelta(months=12)

    while not month_finish > finish:
        month_start = month_finish - relativedelta(months=1) + HH
        month_data = {"start": month_start, "finish": month_finish}
        data_source.sum_md(month_data, pw)
        if month_data["sum-kwh"] is None:
            month_md_kw = 0
            month_kwh = 0
        else:
            month_md_kw = month_data["md-kw"]
            month_kwh = month_data["sum-kwh"]

        data_source.sum_md(month_data, pw, False)
        if month_data["sum-kvarh"] is not None:
            month_kvarh = month_data["sum-kvarh"]

        if month_kvarh == 0:
            month_kva = month_md_kw / 0.95
        else:
            if month_kwh == 0 and month_kvarh == 0:
                pf = 1
            else:
                pf = month_kwh / (month_kwh**2 + month_kvarh**2) ** 0.5
            month_kva = month_md_kw / pf
        md_kva = max(md_kva, month_kva)
        month_finish += relativedelta(months=1)
    return md_kva, ""


def datum_beginning_14(ds, hh):
    rates = ds.hh_rate(ds.dno_contract.id, hh["start-date"])
    try:
        tariff = rates["tariffs"][ds.llfc_code]
    except KeyError as e:
        raise BadRequest(str(e))

    if 0 < hh["ct-decimal-hour"] <= 7:
        hh["duos-night-kwh"] = hh["msp-kwh"]
        hh["duos-night-gbp"] = hh["msp-kwh"] * float(tariff["night-gbp-per-kwh"])
    else:
        hh["duos-day-kwh"] = hh["msp-kwh"]
        hh["duos-day-gbp"] = hh["msp-kwh"] * float(tariff["day-gbp-per-kwh"])

    if 0 < hh["ct-decimal-hour"] <= 7:
        slot = "night"
    elif (
        hh["ct-day-of-week"] < 5
        and hh["ct-decimal-hour"] > 15.5
        and hh["ct-decimal-hour"] < 19
        and (hh["ct-month"] > 11 or hh["ct-month"] < 4)
    ):
        slot = "winter-weekday-peak"
    elif (
        hh["ct-day-of-week"] < 5
        and (7 <= hh["ct-decimal-hour"] < 16 or 18 < hh["ct-decimal-hour"] < 20)
        and (hh["ct-month"] > 11 or hh["ct-month"] < 4)
    ):
        slot = "winter-weekday-day"
    else:
        slot = "other"

    hh["laf"] = float(rates["lafs"][ds.voltage_level_code.lower()][slot])
    hh["gsp-kwh"] = hh["msp-kwh"] * hh["laf"]
    hh["gsp-kw"] = hh["gsp-kwh"] * 2

    if hh["utc-decimal-hour"] == 0:
        hh["duos-standing-gbp"] = float(tariff["fixed-gbp-per-day"])

    if hh["ct-is-month-end"]:
        month_to = hh["start-date"]
        month_from = month_to - relativedelta(months=1) + HH
        availability = ds.sc
        reactive_rate = float(tariff["reactive-gbp-per-kvarh"])
        hh["duos-reactive-rate"] = reactive_rate
        imp_msp_kvarh = 0
        msp_kwh = 0
        md_kva = 0
        for dsc in ds.get_data_sources(month_from, month_to):
            for h in dsc.hh_data:
                imp_msp_kvarh += h["imp-msp-kvarh"]
                msp_kwh += h["msp-kwh"]
                md_kva = max(
                    md_kva,
                    (h["msp-kw"] ** 2 + (h["imp-msp-kvar"] + h["exp-msp-kvar"]) ** 2)
                    ** 0.5,
                )
        hh["duos-reactive-gbp"] = max(0, imp_msp_kvarh - msp_kwh / 3) * reactive_rate
        if not ds.is_displaced:
            availability_rate = float(tariff["availability-gbp-per-kva-per-day"])
            hh["duos-availability-rate"] = availability_rate
            billed_avail = max(availability, md_kva)
            hh["duos-availability-gbp"] = availability_rate * billed_avail
            hh["duos-availability-agreed-kva"] = ds.sc
            hh["duos-availability-billed-kva"] = billed_avail


def datum_2010_04_01(ds, hh):
    start_date = hh["start-date"]
    dno_cache = ds.caches["dno"][ds.dno_code]

    if not ds.full_channels and not (hh["msp-kwh"] > 0 and hh["anti-msp-kwh"] == 0):
        imp_msp_kvarh, exp_msp_kvarh = 0, 0
    else:
        imp_msp_kvarh, exp_msp_kvarh = hh["imp-msp-kvarh"], hh["exp-msp-kvarh"]

    try:
        gsp_group_cache = dno_cache[ds.gsp_group_code]
    except KeyError:
        gsp_group_cache = dno_cache[ds.gsp_group_code] = {}

    try:
        tariff = gsp_group_cache["tariffs"][ds.llfc_code][start_date]
    except KeyError:
        try:
            tariff_cache = gsp_group_cache["tariffs"]
        except KeyError:
            tariff_cache = gsp_group_cache["tariffs"] = {}

        try:
            tariffs = tariff_cache[ds.llfc_code]
        except KeyError:
            tariffs = tariff_cache[ds.llfc_code] = {}

        try:
            tariff = tariffs[start_date]
        except KeyError:
            tariff = None
            try:
                tariff_list = ds.hh_rate(ds.dno_contract.id, start_date)[
                    ds.gsp_group_code
                ]["tariffs"]
            except KeyError as e:
                raise BadRequest(str(e))

            for llfcs_pcs, tf in tariff_list.items():
                key = llfcs_pcs.split("_")
                llfcs = [v.strip() for v in key[0].split(",")]
                if len(key) == 2:
                    pcs = [v.strip() for v in key[1].split(",")]
                else:
                    pcs = None

                if ds.llfc_code in llfcs and (pcs is None or ds.pc_code in pcs):
                    tariff = tf
                    break

            if tariff is None:
                raise BadRequest(
                    f"For the DNO {ds.dno_code} and timestamp {hh_format(start_date)} "
                    f"and GSP group {ds.gsp_group_code}, the LLFC '{ds.llfc_code}' "
                    f"can't be found in the 'tariffs' section."
                )

            tariffs[start_date] = tariff

    try:
        band = gsp_group_cache["bands"][start_date]
    except KeyError:
        try:
            bands_cache = gsp_group_cache["bands"]
        except KeyError:
            bands_cache = gsp_group_cache["bands"] = {}

        try:
            band = bands_cache[start_date]
        except KeyError:
            band = "green"
            ct_hr = hh["ct-decimal-hour"]
            weekend = hh["ct-day-of-week"] > 4
            try:
                slots = ds.hh_rate(ds.dno_contract.id, start_date)[ds.gsp_group_code][
                    "bands"
                ]
            except KeyError as e:
                raise BadRequest(str(e))

            for slot in slots:
                slot_weekend = slot["weekend"] == 1
                if slot_weekend == weekend and slot["start"] <= ct_hr < slot["finish"]:
                    band = slot["band"]
                    break

            bands_cache[start_date] = band

    try:
        laf = dno_cache["lafs"][ds.llfc_code][start_date]
    except KeyError:
        try:
            laf_cache = dno_cache["lafs"]
        except KeyError:
            laf_cache = dno_cache["lafs"] = {}

        try:
            laf_cache_llfc = laf_cache[ds.llfc_code]
        except KeyError:
            laf_cache_llfc = laf_cache[ds.llfc_code] = {}

        try:
            laf = laf_cache_llfc[start_date]
        except KeyError:
            dno_code = ds.dno_code
            if dno_code in ("88", "99"):
                laf_cache_llfc[start_date] = 1
            else:
                m_start, m_finish = next(
                    c_months_u(
                        start_year=hh["ct-year"], start_month=hh["ct-month"], months=1
                    )
                )
                for (laf,) in ds.sess.execute(
                    select(Laf)
                    .join(Llfc)
                    .join(Party)
                    .where(
                        Party.dno_code == ds.dno_code,
                        Llfc.code == ds.llfc_code,
                        Laf.timestamp >= m_start,
                        Laf.timestamp <= m_finish,
                    )
                ):
                    laf_cache_llfc[laf.timestamp] = float(laf.value)

            try:
                laf = laf_cache_llfc[start_date]
            except KeyError:
                laf = laf_cache_llfc[start_date] = 1

    hh["laf"] = laf
    hh["gsp-kwh"] = laf * hh["msp-kwh"]
    hh["gsp-kw"] = hh["gsp-kwh"] * 2

    kvarh = max(
        max(imp_msp_kvarh, exp_msp_kvarh) - (0.95**-2 - 1) ** 0.5 * hh["msp-kwh"], 0
    )

    hh["duos-reactive-kvarh"] = kvarh

    duos_reactive_rate = tariff.get("gbp-per-kvarh")
    if duos_reactive_rate is not None:
        duos_reactive_rate = float(duos_reactive_rate)
        if duos_reactive_rate != 0:
            hh["duos-reactive-rate"] = duos_reactive_rate
            hh["duos-reactive-gbp"] = kvarh * duos_reactive_rate

    rate = float(tariff[KEYS[band]["tariff-rate"]])
    hh[KEYS[band]["bill-rate"]] = rate
    hh[KEYS[band]["kwh"]] = hh["msp-kwh"]
    hh[KEYS[band]["gbp"]] = rate * hh["msp-kwh"]

    if hh["ct-decimal-hour"] == 23.5 and not ds.is_displaced:
        hh["duos-fixed-days"] = 1
        rate = float(tariff["gbp-per-mpan-per-day"])
        hh["duos-fixed-rate"] = rate
        hh["duos-fixed-gbp"] = rate

        hh["duos-availability-days"] = 1
        kva = ds.sc
        hh["duos-availability-kva"] = kva
        rate = float(tariff["gbp-per-kva-per-day"])
        hh["duos-availability-rate"] = rate
        hh["duos-availability-gbp"] = rate * kva

    if hh["ct-is-month-end"] and not ds.is_displaced:
        month_to = start_date
        month_from = to_utc(ct_datetime(hh["ct-year"], hh["ct-month"], 1))
        md_kva = 0
        days_in_month = 0
        for dsc in ds.get_data_sources(month_from, month_to):
            for datum in dsc.hh_data:
                md_kva = max(
                    md_kva,
                    (
                        datum["msp-kw"] ** 2
                        + max(datum["imp-msp-kvar"], datum["exp-msp-kvar"]) ** 2
                    )
                    ** 0.5,
                )
                if datum["ct-decimal-hour"] == 0:
                    days_in_month += 1

        excess_kva = max(md_kva - ds.sc, 0)

        if "excess-gbp-per-kva-per-day" in tariff and excess_kva != 0:
            rate = float(tariff["excess-gbp-per-kva-per-day"])
            hh["duos-excess-availability-kva"] = excess_kva
            rate = float(tariff["excess-gbp-per-kva-per-day"])
            hh["duos-excess-availability-rate"] = rate
            hh["duos-excess-availability-days"] = days_in_month
            hh["duos-excess-availability-gbp"] = rate * excess_kva * days_in_month


def datum_2012_02_23(ds, hh):
    start_date = hh["start-date"]
    dno_cache = ds.caches["dno"][ds.dno_code]

    if not ds.full_channels and hh["msp-kwh"] == 0:
        imp_msp_kvarh, exp_msp_kvarh = 0, 0
    else:
        imp_msp_kvarh, exp_msp_kvarh = hh["imp-msp-kvarh"], hh["exp-msp-kvarh"]

    try:
        gsp_group_cache = dno_cache[ds.gsp_group_code]
    except KeyError:
        gsp_group_cache = dno_cache[ds.gsp_group_code] = {}

    try:
        tariff = gsp_group_cache["tariffs"][ds.pc_code][ds.llfc_code][start_date]
    except KeyError:
        try:
            tariffs_cache = gsp_group_cache["tariffs"]
        except KeyError:
            tariffs_cache = gsp_group_cache["tariffs"] = {}

        try:
            pc_cache = tariffs_cache[ds.pc_code]
        except KeyError:
            pc_cache = tariffs_cache[ds.pc_code] = {}

        try:
            tariffs = pc_cache[ds.llfc_code]
        except KeyError:
            tariffs = pc_cache[ds.llfc_code] = {}

        try:
            tariff = tariffs[start_date]
        except KeyError:
            tariff = None
            try:
                tariff_list = ds.hh_rate(ds.dno_contract.id, start_date)[
                    ds.gsp_group_code
                ]["tariffs"]
            except KeyError as e:
                raise BadRequest(str(e))

            for llfcs_pcs, tf in tariff_list.items():
                key = llfcs_pcs.split("_")
                llfcs = [v.strip() for v in key[0].split(",")]
                if len(key) == 2:
                    pcs = [v.strip() for v in key[1].split(",")]
                else:
                    pcs = None

                if ds.llfc_code in llfcs and (pcs is None or ds.pc_code in pcs):
                    tariff = tf
                    break

            if tariff is None:
                raise BadRequest(
                    f"For the DNO {ds.dno_code} and timestamp {hh_format(start_date)} "
                    f"and GSP group {ds.gsp_group_code}, the LLFC {ds.llfc_code} "
                    f"with PC {ds.pc_code} can't be found in the 'tariffs' section."
                )

            tariffs[start_date] = tariff

    if KEYS["super-red"]["tariff-rate"] in tariff:
        try:
            band = gsp_group_cache["super-red-band"][start_date]
        except KeyError:
            try:
                bands_cache = gsp_group_cache["super-red-band"]
            except KeyError:
                bands_cache = gsp_group_cache["super-red-band"] = {}

            try:
                band = bands_cache[start_date]
            except KeyError:
                band = None
                ct_hr = hh["ct-decimal-hour"]
                weekend = hh["ct-day-of-week"] > 4
                try:
                    slots = ds.hh_rate(ds.dno_contract.id, start_date)[
                        ds.gsp_group_code
                    ]["super_red"]
                except KeyError as e:
                    raise BadRequest(str(e))

                for slot in slots:
                    if (
                        slot["weekend"] == weekend
                        and slot["start-hour"] <= ct_hr < slot["finish-hour"]
                        and (
                            hh["ct-month"] > slot["start-month"]
                            or (
                                hh["ct-month"] == slot["start-month"]
                                and hh["ct-day"] >= slot["start-day"]
                            )
                        )
                        and (
                            hh["ct-month"] < slot["finish-month"]
                            or (
                                hh["ct-month"] == slot["finish-month"]
                                and (
                                    slot["finish-day"] == "last"
                                    or hh["ct-day"] <= slot["finish-day"]
                                )
                            )
                        )
                    ):
                        band = "super-red"
                        break

                bands_cache[start_date] = band
    else:

        try:
            band = gsp_group_cache["rag-bands"][start_date]
        except KeyError:
            try:
                bands_cache = gsp_group_cache["rag-bands"]
            except KeyError:
                bands_cache = gsp_group_cache["rag-bands"] = {}

            try:
                band = bands_cache[start_date]
            except KeyError:
                band = "green"
                ct_hr = hh["ct-decimal-hour"]
                weekend = hh["ct-day-of-week"] > 4
                try:
                    slots = ds.hh_rate(ds.dno_contract.id, start_date)[
                        ds.gsp_group_code
                    ]["bands"]
                except KeyError as e:
                    raise BadRequest(str(e))

                for slot in slots:
                    if (
                        slot["weekend"] == weekend
                        and slot["start"] <= ct_hr < slot["finish"]
                    ):
                        band = slot["band"]
                        break

                bands_cache[start_date] = band

    try:
        laf = dno_cache["lafs"][ds.llfc_code][start_date]
    except KeyError:
        try:
            laf_cache = dno_cache["lafs"]
        except KeyError:
            laf_cache = dno_cache["lafs"] = {}

        try:
            laf_cache_llfc = laf_cache[ds.llfc_code]
        except KeyError:
            laf_cache_llfc = laf_cache[ds.llfc_code] = {}

        try:
            laf = laf_cache_llfc[start_date]
        except KeyError:
            for laf_obj in ds.sess.execute(
                select(Laf)
                .join(Llfc)
                .join(Party)
                .where(
                    Party.dno_code == ds.dno_code,
                    Llfc.code == ds.llfc_code,
                    Laf.timestamp >= ds.start_date,
                    Laf.timestamp <= ds.finish_date,
                )
            ).scalars():
                laf_cache_llfc[laf_obj.timestamp] = float(laf_obj.value)

            lafs = {}
            for laf_obj in ds.sess.execute(
                select(Laf)
                .join(Llfc)
                .join(Party)
                .where(
                    Party.dno_code == ds.dno_code,
                    Llfc.code == ds.llfc_code,
                    Laf.timestamp >= ds.history_start,
                    Laf.timestamp <= ds.history_finish,
                )
            ).scalars():
                lafs[laf_obj.timestamp] = float(laf_obj.value)

            for h in ds.hh_data:
                hstart = h["start-date"]
                if hstart not in laf_cache_llfc:
                    hist_hstart = h["hist-start"]
                    laf_value = lafs[hist_hstart] if hist_hstart in lafs else 1
                    laf_cache_llfc[hstart] = laf_value

            laf = laf_cache_llfc[start_date]

    hh["laf"] = laf
    hh["gsp-kwh"] = laf * hh["msp-kwh"]
    hh["gsp-kw"] = hh["gsp-kwh"] * 2

    kvarh = max(
        max(imp_msp_kvarh, exp_msp_kvarh) - (0.95**-2 - 1) ** 0.5 * hh["msp-kwh"], 0
    )

    hh["duos-reactive-kvarh"] = kvarh

    hh["duos-description"] = tariff["description"]

    duos_reactive_rate = tariff.get("gbp-per-kvarh")
    if duos_reactive_rate is not None:
        duos_reactive_rate = float(duos_reactive_rate)
        if duos_reactive_rate != 0:
            hh["duos-reactive-rate"] = duos_reactive_rate
            hh["duos-reactive-gbp"] = kvarh * duos_reactive_rate

    if band is not None:
        rate = float(tariff[KEYS[band]["tariff-rate"]])
        hh[KEYS[band]["bill-rate"]] = rate
        hh[KEYS[band]["kwh"]] = hh["msp-kwh"]
        hh[KEYS[band]["gbp"]] = rate * hh["msp-kwh"]

    if hh["ct-decimal-hour"] == 23.5 and not ds.is_displaced:
        hh["duos-fixed-days"] = 1
        rate = float(tariff["gbp-per-mpan-per-day"])
        hh["duos-fixed-rate"] = rate
        hh["duos-fixed-gbp"] = rate

        hh["duos-availability-days"] = 1
        kva = ds.sc
        hh["duos-availability-kva"] = kva
        rate = float(tariff["gbp-per-kva-per-day"])
        hh["duos-availability-rate"] = rate
        hh["duos-availability-gbp"] = rate * kva

    if hh["ct-is-month-end"] and not ds.is_displaced:
        month_to = start_date
        month_from = to_utc(ct_datetime(hh["ct-year"], hh["ct-month"], 1))
        md_kva = 0
        days_in_month = 0
        for dsc in ds.get_data_sources(month_from, month_to):
            for datum in dsc.hh_data:
                md_kva = max(md_kva, datum["msp-kva"])
                if datum["ct-decimal-hour"] == 0:
                    days_in_month += 1

        excess_kva = max(md_kva - ds.sc, 0)

        if "excess-gbp-per-kva-per-day" in tariff and excess_kva != 0:
            rate = float(tariff["excess-gbp-per-kva-per-day"])
            hh["duos-excess-availability-kva"] = excess_kva
            rate = float(tariff["excess-gbp-per-kva-per-day"])
            hh["duos-excess-availability-rate"] = rate
            hh["duos-excess-availability-days"] = days_in_month
            hh["duos-excess-availability-gbp"] = rate * excess_kva * days_in_month


CUTOFF_DATE_1 = utc_datetime(2010, 3, 31, 23, 0)
CUTOFF_DATE_2 = utc_datetime(2012, 2, 23, 0, 0)


def duos_vb(ds):
    try:
        data_func_cache = ds.caches["dno"][ds.dno_code]["data_funcs"]
    except KeyError:
        try:
            dno_caches = ds.caches["dno"]
        except KeyError:
            dno_caches = ds.caches["dno"] = {}

        try:
            dno_cache = dno_caches[ds.dno_code]
        except KeyError:
            dno_cache = dno_caches[ds.dno_code] = {}

        try:
            data_func_cache = dno_cache["data_funcs"]
        except KeyError:
            data_func_cache = dno_cache["data_funcs"] = {}

    for hh in ds.hh_data:
        try:
            data_func_cache[hh["start-date"]](ds, hh)
        except KeyError:
            if hh["start-date"] < CUTOFF_DATE_1:
                if ds.dno_code == "14":
                    data_func = datum_beginning_14
                elif ds.dno_code == "20":
                    data_func = datum_beginning_20
                elif ds.dno_code in ("22", "99"):
                    data_func = datum_beginning_22
                else:
                    raise Exception("Not recognized")
            elif hh["start-date"] < CUTOFF_DATE_2:
                data_func = datum_2010_04_01
            else:
                data_func = datum_2012_02_23

            data_func_cache[hh["start-date"]] = data_func
            data_func(ds, hh)
