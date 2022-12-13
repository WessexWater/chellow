import traceback
from collections import defaultdict

from sqlalchemy import null, or_, select
from sqlalchemy.orm import joinedload

from chellow.dloads import put_mem_val
from chellow.e.computer import (
    SiteSource,
    SupplySource,
    contract_func,
    displaced_era,
    forecast_date,
)
from chellow.models import Era, Session, Site, SiteEra, Source, Supply
from chellow.utils import c_months_u, ct_datetime_now, hh_max, hh_min


def totals_runner(mem_id, site_id, start_date):
    CATS = ("imp_net", "exp_net", "used", "displaced")
    QUANTS = (
        "kwh",
        "gbp",
        "p_per_kwh",
        "triad_gbp",
        "duos_gbp",
        "red_duos_gbp",
        "md_kw",
    )
    sess = None
    titles = ["Quantity"]
    titles.extend(CATS)
    log_list = []
    problem = ""

    jval = {"titles": titles, "rows": [], "status": "running", "log": log_list}
    try:
        sess = Session()
        site = Site.get_by_id(sess, site_id)

        def log(msg):
            return
            log_list.append(msg)
            put_mem_val(mem_id, jval)

        log("started thread")
        f_date = forecast_date()
        report_context = {}
        vals = dict((cat, defaultdict(int)) for cat in CATS)

        if start_date is None:
            now = ct_datetime_now()
            start_year = now.year - 1
            start_month = now.month
        else:
            start_year = start_date.year
            start_month = start_date.month

        for progress, (month_start, month_finish) in enumerate(
            c_months_u(start_year=start_year, start_month=start_month, months=12)
        ):
            jval["progress"] = progress
            put_mem_val(mem_id, jval)

            for era in sess.execute(
                select(Era)
                .join(SiteEra)
                .join(Supply)
                .join(Source)
                .where(
                    SiteEra.site == site,
                    Era.start_date <= month_finish,
                    or_(Era.finish_date == null(), Era.finish_date >= month_start),
                    Era.imp_mpan_core != null(),
                    Source.code.in_(("net", "gen-net")),
                )
                .options(
                    joinedload(Era.imp_supplier_contract),
                    joinedload(Era.exp_supplier_contract),
                    joinedload(Era.mop_contract),
                    joinedload(Era.dc_contract),
                )
            ).scalars():

                chunk_start = hh_max(era.start_date, month_start)
                chunk_finish = hh_min(era.finish_date, month_finish)

                log("about to call first supplysource")
                supply_ds = SupplySource(
                    sess,
                    chunk_start,
                    chunk_finish,
                    f_date,
                    era,
                    True,
                    report_context,
                )

                supplier_contract = era.imp_supplier_contract
                import_vb_function = contract_func(
                    report_context, supplier_contract, "virtual_bill"
                )
                if import_vb_function is None:
                    raise Exception(
                        "Can't find the import_virtual_bill function in the "
                        "supplier contract. "
                    )
                else:
                    import_vb_function(supply_ds)
                    v_bill = supply_ds.supplier_bill

                    if "problem" in v_bill and len(v_bill["problem"]) > 0:
                        raise Exception("Supplier Problem: " + v_bill["problem"])

                    try:
                        vals["imp_net"]["gbp"] += v_bill["net-gbp"]
                        if "triad-gbp" in v_bill:
                            vals["imp_net"]["triad_gbp"] += v_bill["triad-gbp"]
                        if "duos-red-gbp" in v_bill:
                            vals["imp_net"]["red_duos_gbp"] += v_bill["duos-red-gbp"]
                        vals["imp_net"]["duos_gbp"] += sum(
                            v
                            for k, v in v_bill.items()
                            if k.endswith("-gbp") and k.startswith("duos-")
                        )
                    except KeyError:
                        raise Exception(
                            f"For the era {era.id} the virtual bill {v_bill} "
                            f"from the contract {supplier_contract} does not "
                            f"contain the net-gbp key."
                        )

                dc_contract = era.dc_contract
                supply_ds.contract_func(dc_contract, "virtual_bill")(supply_ds)
                dc_bill = supply_ds.dc_bill
                vals["imp_net"]["gbp"] += dc_bill["net-gbp"]
                if "problem" in dc_bill and len(dc_bill["problem"]) > 0:
                    problem += "DC Problem: " + dc_bill["problem"]

                mop_contract = era.mop_contract
                mop_bill_function = supply_ds.contract_func(
                    mop_contract, "virtual_bill"
                )
                mop_bill_function(supply_ds)
                mop_bill = supply_ds.mop_bill
                vals["imp_net"]["gbp"] += mop_bill["net-gbp"]
                if "problem" in mop_bill and len(mop_bill["problem"]) > 0:
                    problem += "MOP Problem: " + mop_bill["problem"]

                exp_supplier_contract = era.exp_supplier_contract
                if exp_supplier_contract is not None:
                    log("about to call second supply source")
                    exp_supply_ds = SupplySource(
                        sess,
                        chunk_start,
                        chunk_finish,
                        f_date,
                        era,
                        False,
                        report_context,
                    )
                    exp_vb_function = contract_func(
                        report_context, exp_supplier_contract, "virtual_bill"
                    )
                    if exp_vb_function is None:
                        problem += (
                            "Can't find the export_virtual_bill function in the "
                            "supplier contract. "
                        )
                    else:
                        exp_vb_function(exp_supply_ds)
                        v_bill = exp_supply_ds.supplier_bill

                        if "problem" in v_bill and len(v_bill["problem"]) > 0:
                            problem += f"Export supplier Problem: {v_bill['problem']}"

                        try:
                            vals["exp_net"]["gbp"] += v_bill["net-gbp"]
                            if "triad-gbp" in v_bill:
                                vals["exp_net"]["triad_gbp"] += v_bill["triad-gbp"]
                            if "duos-red-gbp" in v_bill:
                                vals["exp_net"]["red_duos_gbp"] += v_bill[
                                    "duos-red-gbp"
                                ]
                            vals["exp_net"]["duos_gbp"] += sum(
                                v
                                for k, v in v_bill.items()
                                if k.endswith("-gbp") and k.startswith("duos-")
                            )
                        except KeyError:
                            problem += (
                                f"For the era {era.id} the virtual bill "
                                f"{v_bill} from the contract "
                                f"{supplier_contract} does not contain the "
                                f"net-gbp key."
                            )
                            problem += v_bill["problem"]

            disp_era = displaced_era(
                sess, report_context, site, month_start, month_finish, f_date
            )
            log("about to call sitesource")
            site_ds = SiteSource(
                sess,
                site,
                month_start,
                month_finish,
                f_date,
                report_context,
                disp_era,
                exclude_virtual=False,
            )

            if disp_era is not None:
                disp_supplier_contract = disp_era.imp_supplier_contract
                disp_vb_function = contract_func(
                    report_context, disp_supplier_contract, "displaced_virtual_bill"
                )
                if disp_vb_function is None:
                    raise Exception(
                        f"The supplier contract {disp_supplier_contract} "
                        "doesn't have the displaced_virtual_bill() function."
                    )
                disp_vb_function(site_ds)
                disp_supplier_bill = site_ds.supplier_bill

                try:
                    vals["displaced"]["gbp"] += disp_supplier_bill["net-gbp"]
                except KeyError:
                    disp_supplier_bill["problem"] += (
                        f"For the supply {site_ds.mpan_core} the virtual bill "
                        f"{disp_supplier_bill} from the contract "
                        f"{disp_supplier_contract} does not contain the net-gbp "
                        f"key."
                    )
                log(str(disp_supplier_bill))
                if "triad-gbp" in disp_supplier_bill:
                    vals["displaced"]["triad_gbp"] += disp_supplier_bill["triad-gbp"]
                if "duos-red-gbp" in disp_supplier_bill:
                    vals["displaced"]["red_duos_gbp"] += disp_supplier_bill[
                        "duos-red-gbp"
                    ]
                vals["displaced"]["duos_gbp"] += sum(
                    v
                    for k, v in disp_supplier_bill.items()
                    if k.endswith("-gbp") and k.startswith("duos-")
                )

            for hh in site.hh_data(
                sess, month_start, month_finish, exclude_virtual=True
            ):
                for cat in CATS:
                    vals_cat = vals[cat]
                    vals_cat["md_kw"] = max(vals_cat["md_kw"], hh[cat] * 2)
                    vals_cat["kwh"] += float(hh[cat])

        for quant in ("gbp", "triad_gbp", "duos_gbp", "red_duos_gbp"):
            vals["used"][quant] += vals["imp_net"][quant] + vals["displaced"][quant]

        for cat in CATS:
            vals_cat = vals[cat]
            if vals_cat["kwh"] > 0:
                vals_cat["p_per_kwh"] = vals_cat["gbp"] / vals_cat["kwh"] * 100
            else:
                vals_cat["p_per_kwh"] = 0

        FORMAT_LOOKUP = {
            "kwh": "{:,.0f}",
            "gbp": "{:,.2f}",
            "p_per_kwh": "{:,.2f}",
            "triad_gbp": "{:,.2f}",
            "duos_gbp": "{:,.2f}",
            "red_duos_gbp": "{:,.2f}",
            "md_kw": "{:,.2f}",
        }

        for quant in QUANTS:
            row = [quant]
            fmt = FORMAT_LOOKUP[quant]
            for cat in CATS:
                row.append(fmt.format(vals[cat][quant]))
            jval["rows"].append(row)

    except BaseException:
        msg = traceback.format_exc()
        jval["problem"] = msg
    finally:
        try:
            if sess is not None:
                sess.close()
        except BaseException:
            jval["problem"] = "\nProblem closing session."
        finally:
            jval["status"] = "finished"
            put_mem_val(mem_id, jval)
