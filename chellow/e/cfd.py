from datetime import datetime as Datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta

from sqlalchemy import null, or_, select

from werkzeug.exceptions import BadRequest

from chellow.e.lcc import api_records
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
        return False
    else:
        st_ct = to_ct(rs.start_date)
        if (
            rs.finish_date is None
            and date
            > list(
                c_months_u(start_year=st_ct.year, start_month=st_ct.month, months=3)
            )[-1][-1]
        ):
            return False
        else:
            return True


def _find_top_run(runs):
    run_types_reverse = list(reversed(RUN_TYPES))
    for run_type in run_types_reverse:
        if run_type in runs:
            return runs[run_type]


def hh(data_source, use_bill_check=False):
    try:
        cfd_cache = data_source.caches["cfd"]
    except KeyError:
        cfd_cache = data_source.caches["cfd"] = {}

    for h in data_source.hh_data:
        try:
            h["cfd-rates"] = cfd_cache[h["start-date"]]
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
                rates = data_source.non_core_rate(
                    "cfd_reconciled_daily_levy_rates", h_start
                )
                records = rates["records"]
                dt_str = hh_format(h_start)[:11] + "00:00"

                try:
                    runs = records[dt_str]
                    top_run = _find_top_run(runs)
                    base_rate = (
                        _parse_number(top_run["Reconciled_Daily_Levy_Rate_GBP_Per_MWh"])
                        / 1000
                    )
                except KeyError:
                    base_rate = None

                if base_rate is None:
                    rates = data_source.non_core_rate("cfd_in_period_tracking", h_start)
                    records = rates["records"]

                    if dt_str in records:
                        record = records[dt_str]
                        gbp = _parse_number(
                            record["Actual_CFD_Payments_GBP"]
                        ) + _parse_number(record["Expected_CFD_Payments_GBP"])
                        mwh = _parse_number(
                            record["Actual_Eligible_Demand_MWh"]
                        ) + _parse_number(record["Expected_Eligible_Demand_MWh"])

                        base_rate = gbp / mwh / 1000
                    else:
                        base_rate = None

                if base_rate is None:
                    if _find_quarter_rs(
                        data_source.sess, "cfd_forecast_ilr_tra", h_start
                    ):
                        base_rate_dec = Decimal(
                            data_source.non_core_rate("cfd_forecast_ilr_tra", h_start)[
                                "record"
                            ]["Interim_Levy_Rate_GBP_Per_MWh"]
                        ) / Decimal(1000)

                    else:
                        base_rate_dec = Decimal(
                            data_source.non_core_rate(
                                "cfd_advanced_forecast_ilr_tra", h_start
                            )["sensitivity"]["Base Case"][
                                "Interim Levy Rate_GBP_Per_MWh"
                            ]
                        ) / Decimal(1000)

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

            h["cfd-rates"] = cfd_cache[h_start] = {
                "supplier-obligation": base_rate,
                "operational": levy_rate,
            }


def lcc_import(sess, log, set_progress, s):
    import_in_period_tracking(sess, log, set_progress, s)
    import_operational_costs_levy(sess, log, set_progress, s)
    import_reconciled_daily_levy_rates(sess, log, set_progress, s)
    import_forecast_ilr_tra(sess, log, set_progress, s)
    import_advanced_forecast_ilr_tra(sess, log, set_progress, s)


def _quarters(log, s):
    quarter = {}
    for record in api_records(log, s, "003f527c-aa35-4198-adbb-21a61fc760eb"):
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

    for quarter in _quarters(log, s):
        quarter_start = sorted(quarter.keys())[0]
        rs = sess.execute(
            select(RateScript).where(
                RateScript.contract == contract,
                RateScript.start_date == quarter_start,
            )
        ).scalar_one_or_none()
        if rs is None:
            rs = contract.insert_rate_script(sess, quarter_start, {"records": {}})

        rs_script = rs.make_script()
        records = rs_script["records"]
        for k, v in sorted(quarter.items()):
            records[hh_format(k)] = v
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

    for record in api_records(log, s, "41c32b4f-388b-464f-9c3f-fbf1a6cfdca4", skip=1):
        period_start = _parse_date(record["Period_Start"])

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


def _reconciled_quarters(log, s, search_from):
    quarters = {}

    for record in api_records(log, s, "24944bfe-b546-4f50-8bf6-895d8f769b2b"):
        settlement_date = _parse_date(record["Settlement_Date"])
        if settlement_date > search_from:
            settlement_date_ct = to_ct(settlement_date)
            quarter_start_ct_month = int((settlement_date_ct.month - 1) / 3) * 3 + 1
            quarter_start = to_utc(
                ct_datetime(settlement_date_ct.year, quarter_start_ct_month, 1)
            )
            try:
                quarter = quarters[quarter_start]
            except KeyError:
                quarter = quarters[quarter_start] = {}

            try:
                day = quarter[settlement_date]
            except KeyError:
                day = quarter[settlement_date] = {}

            settlement_run_type = record["Settlement_Run_Type"]
            day[settlement_run_type] = record

    # Only return complate quarters
    if len(quarters) > 0:
        last_start = sorted(quarters.keys())[-1]
        del quarters[last_start]
    return quarters


def import_reconciled_daily_levy_rates(sess, log, set_progress, s):
    log("Starting to check for new LCC CfD Reconciled Daily Levy Rates")

    contract_name = "cfd_reconciled_daily_levy_rates"
    contract = Contract.find_non_core_by_name(sess, contract_name)
    if contract is None:
        contract = Contract.insert_non_core(
            sess, contract_name, "", {}, to_utc(ct_datetime(1996, 4, 1)), None, {}
        )

    search_from = to_utc(ct_datetime(1996, 4, 1))
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
            search_from = to_utc(quarter_finish_ct)
        else:
            break

    for quarter_start, quarter in _reconciled_quarters(log, s, search_from).items():

        rs = sess.execute(
            select(RateScript).where(
                RateScript.contract == contract,
                RateScript.start_date == quarter_start,
            )
        ).scalar_one_or_none()
        if rs is None:
            rs = contract.insert_rate_script(sess, quarter_start, {"records": {}})

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

    for record in api_records(log, s, "63e6a924-8829-4014-95a2-722e92662e5f"):
        period_start_str = record["Period_Start"]
        if len(period_start_str) == 0:
            continue
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

    for record in api_records(log, s, "a80f87c6-cf65-4f9d-9a1a-d78140f50779"):
        period_start = _parse_varying_date(record["Period Start"])

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
