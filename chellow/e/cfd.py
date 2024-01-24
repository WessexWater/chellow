from datetime import datetime as Datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta

from sqlalchemy import null, or_, select

from werkzeug.exceptions import BadRequest

from chellow.e.lcc import api_search, api_sql
from chellow.models import Contract, RateScript
from chellow.utils import c_months_u, ct_datetime, hh_format, to_ct, to_utc


def _find_quarter_rs(sess, contract_name, date):
    contract = Contract.get_non_core_by_name(sess, contract_name)
    rs = sess.scalars(
        select(RateScript).where(
            RateScript.contract == contract,
            RateScript.start_date <= date,
            or_(
                RateScript.finish_date == null(),
                RateScript.finish_date >= date,
            ),
        )
    ).one_or_none()
    if rs is None:
        return None
    else:
        st_ct = to_ct(rs.start_date)
        if (
            rs.finish_date is None
            and date
            > list(
                c_months_u(start_year=st_ct.year, start_month=st_ct.month, months=3)
            )[-1][-1]
        ):
            return None
        else:
            return rs.make_script()


def hh(data_source, use_bill_check=False):
    try:
        cfd_cache = data_source.caches["cfd"]
    except KeyError:
        cfd_cache = data_source.caches["cfd"] = {}

    for h in data_source.hh_data:
        try:
            h["cfd-rate"] = cfd_cache[h["start-date"]]
        except KeyError:
            h_start = h["start-date"]
            if use_bill_check:
                base_rate = (
                    float(
                        data_source.non_core_rate("cfd_forecast_ilr_tra", h_start)[
                            "record"
                        ]["Interim_Levy_Rate_GBP_Per_MWh"]
                    )
                    / 1000
                )
            else:
                daily_rs = _find_quarter_rs(
                    data_source.sess, "cfd_reconciled_daily_levy_rates", h_start
                )
                if daily_rs is None:
                    period_rs = _find_quarter_rs(
                        data_source.sess, "cfd_in_period_tracking", h_start
                    )
                    if period_rs is None:
                        ilr_rs = _find_quarter_rs(
                            data_source.sess, "cfd_forecast_ilr_tra", h_start
                        )
                        if ilr_rs is None:
                            base_rate_dec = Decimal(
                                data_source.non_core_rate(
                                    "cfd_advanced_forecast_ilr_tra", h_start
                                )["sensitivity"]["Base Case"][
                                    "Interim Levy Rate_GBP_Per_MWh"
                                ]
                            ) / Decimal(1000)

                        else:
                            base_rate_dec = Decimal(
                                ilr_rs["record"]["Interim_Levy_Rate_GBP_Per_MWh"]
                            ) / Decimal(1000)
                    else:
                        base_rate_dec = period_rs["rate_gbp_per_kwh"]
                else:
                    base_rate_dec = daily_rs["rate_gbp_per_kwh"]

                base_rate = float(base_rate_dec)

            effective_ocl_rate = data_source.non_core_rate(
                "cfd_operational_costs_levy", h["start-date"]
            )["record"]["Effective_OCL_Rate_GBP_Per_MWh"]
            if effective_ocl_rate == "":
                levy_rate_str = data_source.non_core_rate(
                    "cfd_operational_costs_levy", h_start
                )["record"]["OCL_Rate_GBP_Per_MWh"]
            else:
                levy_rate_str = effective_ocl_rate
            levy_rate = float(levy_rate_str) / 1000

            h["cfd-rate"] = cfd_cache[h_start] = base_rate + levy_rate


def lcc_import(sess, log, set_progress, s):
    import_in_period_tracking(sess, log, set_progress, s)
    import_operational_costs_levy(sess, log, set_progress, s)
    import_reconciled_daily_levy_rates(sess, log, set_progress, s)
    import_forecast_ilr_tra(sess, log, set_progress, s)
    import_advanced_forecast_ilr_tra(sess, log, set_progress, s)


def _quarters(s):
    quarter = {}
    res_j = api_search(
        s, "2fc2fad9-ad57-4901-982a-f92d4ef6c622", sort="Settlement_Date"
    )
    for record in res_j["result"]["records"]:
        settlement_date_str = record["Settlement_Date"]
        settlement_date_ct = to_ct(
            Datetime.strptime(settlement_date_str[:10], "%Y-%m-%d")
        )
        settlement_date = to_utc(settlement_date_ct)

        quarter[settlement_date] = record
        settlement_next_ct = settlement_date_ct + relativedelta(days=1)

        if settlement_next_ct.month in (1, 4, 7, 10) and settlement_next_ct.day == 1:
            yield quarter
            quarter = {}


def _parse_number(num_str):
    if num_str == "":
        return 0
    else:
        return float(num_str)


def _parse_date(date_str):
    return to_utc(to_ct(Datetime.strptime(date_str[:10], "%Y-%m-%d")))


def _parse_varying_date(date_str):
    if "-" in date_str:
        pattern = "%Y-%m-%d"
    elif "/" in date_str:
        pattern = "%d/%m/%Y"
    else:
        raise BadRequest(f"The date {date_str} is not recognized.")
    return to_utc(to_ct(Datetime.strptime(date_str[:10], pattern)))


def import_in_period_tracking(sess, log, set_progress, s):
    log("Starting to check for new LCC CfD In-Period Tracking")

    contract_name = "cfd_in_period_tracking"
    contract = Contract.find_non_core_by_name(sess, contract_name)
    if contract is None:
        contract = Contract.insert_non_core(
            sess, contract_name, "", {}, to_utc(ct_datetime(1996, 4, 1)), None, {}
        )

    for quarter in _quarters(s):
        quarter_start = sorted(quarter.keys())[0]
        rs = sess.execute(
            select(RateScript).where(
                RateScript.contract == contract,
                RateScript.start_date == quarter_start,
            )
        ).scalar_one_or_none()
        if rs is None:
            rs = contract.insert_rate_script(sess, quarter_start, {"records": {}})

        gbp = 0
        kwh = 0
        for record in quarter.values():
            gbp += _parse_number(record["Actual_CFD_Payments_GBP"])
            gbp += _parse_number(record["Expected_CFD_Payments_GBP"])
            kwh += _parse_number(record["Actual_Eligible_Demand_MWh"]) * 1000
            kwh += _parse_number(record["Expected_Eligible_Demand_MWh"]) * 1000

        rate = gbp / kwh

        rs_script = rs.make_script()
        records = rs_script["records"]
        for k, v in sorted(quarter.items()):
            records[hh_format(k)] = v
        rs_script["rate_gbp_per_kwh"] = rate
        rs.update(rs_script)
        sess.commit()
    log("Finished LCC CfD In-Period Tracking")


def import_operational_costs_levy(sess, log, set_progress, s):
    log("Starting to check for new LCC CfD Operational Costs Levy")

    contract_name = "cfd_operational_costs_levy"
    contract = Contract.find_non_core_by_name(sess, contract_name)
    if contract is None:
        contract = Contract.insert_non_core(
            sess, contract_name, "", {}, to_utc(ct_datetime(1996, 4, 1)), None, {}
        )

    res_j = api_search(s, "44f41eac-61b3-4e8d-8c52-3eda7b8e8517", sort="Period_Start")
    for record in res_j["result"]["records"][1:]:  # skip title row
        period_start_str = record["Period_Start"]
        period_start = to_utc(
            to_ct(Datetime.strptime(period_start_str[:10], "%Y-%m-%d"))
        )

        rs = sess.execute(
            select(RateScript).where(
                RateScript.contract == contract,
                RateScript.start_date == period_start,
            )
        ).scalar_one_or_none()
        if rs is None:
            rs = contract.insert_rate_script(sess, period_start, {})

        rs_script = rs.make_script()
        rs_script["record"] = record
        rs.update(rs_script)
        sess.commit()


RUN_TYPES = ("II", "SF", "R1", "R2", "R3", "RF", "DF")


def _reconciled_days(s, search_from):
    runs = {}
    res_j = api_sql(
        s,
        f"""SELECT * from "e0e163cb-ba36-416d-83fe-976992d61516"
        WHERE "Settlement_Date" > '{search_from}' ORDER BY "Settlement_Date"
        """,
    )

    records = res_j["result"]["records"]
    if len(records) > 0:
        prev_settlement_date = _parse_date(records[0]["Settlement_Date"])
        runs = {}
        for record in records:
            settlement_date = _parse_date(record["Settlement_Date"])
            if settlement_date != prev_settlement_date:
                yield prev_settlement_date, runs
                runs = {}

            settlement_run_type = record["Settlement_Run_Type"]
            runs[settlement_run_type] = record
            prev_settlement_date = settlement_date

        yield settlement_date, runs


def _reconciled_daily_quarters(s, search_from):
    quarter = {}
    for settlement_date, lcc_runs in _reconciled_days(s, search_from):
        try:
            runs = quarter[settlement_date]
        except KeyError:
            runs = quarter[settlement_date] = {}

        for run_type, record in lcc_runs.items():
            runs[run_type] = record

        settlement_next_ct = to_ct(settlement_date) + relativedelta(days=1)

        if settlement_next_ct.month in (1, 4, 7, 10) and settlement_next_ct.day == 1:
            yield quarter
            quarter = {}


def import_reconciled_daily_levy_rates(sess, log, set_progress, s):
    log("Starting to check for new LCC CfD Reconciled Daily Levy Rates")

    contract_name = "cfd_reconciled_daily_levy_rates"
    contract = Contract.find_non_core_by_name(sess, contract_name)
    if contract is None:
        contract = Contract.insert_non_core(
            sess, contract_name, "", {}, to_utc(ct_datetime(1996, 4, 1)), None, {}
        )

    search_from = "1996-04-01"
    for rs in sess.scalars(
        select(RateScript)
        .where(RateScript.contract == contract)
        .order_by(RateScript.start_date.desc())
    ):
        script = rs.make_script()
        try:
            records = script["records"]
        except KeyError:
            break

        complete = True
        rs_start_ct = to_ct(rs.start_date)
        quarter_finish_ct = (
            rs_start_ct + relativedelta(months=3) - relativedelta(days=1)
        )
        day_ct = rs_start_ct
        while day_ct <= quarter_finish_ct:
            try:
                records[hh_format(to_utc(day_ct))]["DF"]
            except KeyError:
                complete = False
                break

            day_ct += relativedelta(days=1)

        if complete:
            search_from = quarter_finish_ct.strftime("%Y-%m-%d")
        else:
            break

    for quarter in _reconciled_daily_quarters(s, search_from):
        quarter_start = sorted(quarter.keys())[0]
        rs = sess.execute(
            select(RateScript).where(
                RateScript.contract == contract,
                RateScript.start_date == quarter_start,
            )
        ).scalar_one_or_none()
        if rs is None:
            rs = contract.insert_rate_script(sess, quarter_start, {"records": {}})

        gbp = 0
        kwh = 0
        run_types_reverse = list(reversed(RUN_TYPES))
        for runs in quarter.values():
            top_run = None
            for run_type in run_types_reverse:
                if run_type in runs:
                    top_run = runs[run_type]
                    break

            eligible_mwh = _parse_number(top_run["Reconciled_Eligible_Demand_MWh"])
            gbp += (
                _parse_number(top_run["Reconciled_Daily_Levy_Rate_GBP_Per_MWh"])
                * eligible_mwh
            )
            kwh += eligible_mwh * 1000

        rate = gbp / kwh

        rs_script = rs.make_script()
        records = rs_script["records"]
        for dt, runs in sorted(quarter.items()):
            date_str = hh_format(dt)
            try:
                rs_runs = records[date_str]
            except KeyError:
                rs_runs = records[date_str] = {}

            for run_type, record in runs.items():
                rs_runs[run_type] = record

        rs_script["rate_gbp_per_kwh"] = rate
        rs.update(rs_script)
        sess.commit()

    log("Finished LCC CfD Reconciled Daily Levy Rates")
    sess.commit()


def import_forecast_ilr_tra(sess, log, set_progress, s):
    log("Starting to check for new LCC CfD Forecast ILR TRA")

    contract_name = "cfd_forecast_ilr_tra"
    contract = Contract.find_non_core_by_name(sess, contract_name)
    if contract is None:
        contract = Contract.insert_non_core(
            sess, contract_name, "", {}, to_utc(ct_datetime(1996, 4, 1)), None, {}
        )

    res_j = api_search(s, "fbece4ce-7cfc-42b7-8fb2-387cf59a3c32", sort="Period_Start")
    for record in res_j["result"]["records"]:
        period_start_str = record["Period_Start"]
        period_start = _parse_varying_date(period_start_str)

        rs = sess.execute(
            select(RateScript).where(
                RateScript.contract == contract,
                RateScript.start_date == period_start,
            )
        ).scalar_one_or_none()
        if rs is None:
            rs = contract.insert_rate_script(sess, period_start, {})

        rs_script = rs.make_script()
        rs_script["record"] = record
        rs.update(rs_script)
        sess.commit()
    log("Finished LCC CfD Forecast ILR TRA")


def import_advanced_forecast_ilr_tra(sess, log, set_progress, s):
    log("Starting to check for new LCC CfD Advanced Forecast ILR TRA")

    contract_name = "cfd_advanced_forecast_ilr_tra"
    contract = Contract.find_non_core_by_name(sess, contract_name)
    if contract is None:
        contract = Contract.insert_non_core(
            sess, contract_name, "", {}, to_utc(ct_datetime(1996, 4, 1)), None, {}
        )

    res_j = api_search(s, "e3ad6876-c1e9-46f9-b557-cb9bdae53885", sort="Period Start")
    for record in res_j["result"]["records"]:
        period_start_str = record["Period Start"]
        period_start = _parse_varying_date(period_start_str)

        rs = sess.execute(
            select(RateScript).where(
                RateScript.contract == contract,
                RateScript.start_date == period_start,
            )
        ).scalar_one_or_none()
        if rs is None:
            rs = contract.insert_rate_script(sess, period_start, {})

        sensitivity = record["Sensitivity"]
        rs_script = rs.make_script()
        try:
            rs_sensitivity = rs_script["sensitivity"]
        except KeyError:
            rs_sensitivity = rs_script["sensitivity"] = {}
        rs_sensitivity[sensitivity] = record
        rs.update(rs_script)

        sess.commit()

    log("Finished LCC CfD Advanced Forecast ILR TRA")
