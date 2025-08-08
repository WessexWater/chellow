import csv
import sys
import threading
import traceback

from flask import g, redirect

import requests

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import null, or_

from werkzeug.exceptions import BadRequest

from chellow.dloads import open_file
from chellow.models import (
    Contract,
    Era,
    MtcParticipant,
    Party,
    ReportRun,
    Session,
    Source,
    Supply,
    User,
)
from chellow.utils import csv_make_val, req_bool, utc_datetime_now


FNAME = "ecoes_comparison"


def _parse_date(date_str):
    if len(date_str) > 0:
        day, month, year = date_str.split("/")
        return f"{year}-{month}-{day} 00:00"
    else:
        return date_str


def content(user_id, show_ignored, report_run_id):
    f = report_run = None
    try:
        with Session() as sess:
            user = User.get_by_id(sess, user_id)
            f = open_file(f"{FNAME}.csv", user, mode="w", newline="")
            report_run = ReportRun.get_by_id(sess, report_run_id)

            props = Contract.get_non_core_by_name(
                sess, "configuration"
            ).make_properties()

            ECOES_KEY = "ecoes"
            try:
                ecoes_props = props[ECOES_KEY]
            except KeyError:
                raise BadRequest(
                    f"The property {ECOES_KEY} cannot be found in the configuration "
                    f"properties."
                )

            for key in (
                "user_name",
                "password",
                "exclude_mpan_cores",
                "ignore_mpan_cores_msn",
            ):
                try:
                    ecoes_props[key]
                except KeyError:
                    raise BadRequest(
                        f"The property {key} cannot be found in the 'ecoes' section of "
                        f"the configuration properties."
                    )

            exclude_mpan_cores = ecoes_props["exclude_mpan_cores"]
            ignore_mpan_cores_msn = ecoes_props["ignore_mpan_cores_msn"]
            url_prefix = "https://www.ecoes.co.uk/"

            proxies = props.get("proxies", {})
            s = requests.Session()
            s.verify = False
            r = s.get(url_prefix, proxies=proxies)
            data = {
                "Username": ecoes_props["user_name"],
                "Password": ecoes_props["password"],
            }
            login_j = s.post(url_prefix, data=data, allow_redirects=False).json()
            if not login_j["Success"]:
                raise BadRequest(f"Login to ECOES failed: {login_j['Messages']}")
            elif "RedirectUrl" in login_j and "SetPassword" in login_j["RedirectUrl"]:
                raise BadRequest(
                    "Login to ECOES failed, it looks like the password needs to be "
                    "changed"
                )

            r = s.get(
                f"{url_prefix}PortfolioAccess/ExportPortfolioMPANs?fileType=csv",
                proxies=proxies,
            )

            _process(
                sess,
                r.text.splitlines(True),
                exclude_mpan_cores,
                ignore_mpan_cores_msn,
                f,
                show_ignored,
                report_run,
            )
            report_run.update("finished")
            sess.commit()

    except BadRequest as e:
        msg = e.description
        if report_run is not None:
            report_run.update("interrupted")
            report_run.insert_row(sess, "", ["problem"], {"problem": msg}, {})
            sess.commit()
        if f is not None:
            f.write(msg)
        raise e
    except BaseException as e:
        msg = traceback.format_exc()
        if report_run is not None:
            report_run.update("interrupted")
            report_run.insert_row(sess, "", ["problem"], {"problem": msg}, {})
            sess.commit()
        sys.stderr.write(msg)
        if f is not None:
            f.write(msg)
        raise e
    finally:
        if f is not None:
            f.close()


def _process(
    sess,
    ecoes_lines,
    exclude_mpan_cores,
    ignore_mpan_cores_msn,
    f,
    show_ignored,
    report_run,
):
    writer = csv.writer(f, lineterminator="\n")
    now = utc_datetime_now()

    mpans = []

    for exp in (Era.imp_mpan_core, Era.exp_mpan_core):
        for (v,) in sess.execute(
            select(exp)
            .join(Supply)
            .join(Source)
            .join(Supply.dno)
            .filter(
                Party.dno_code.notin_(("88", "99")),
                Era.finish_date == null(),
                Source.code != "3rd-party",
                exp.notin_(exclude_mpan_cores),
                exp != null(),
            )
            .distinct()
            .order_by(exp)
        ):
            mpans.append(v)

    ecoes_mpans = {}

    parser = iter(csv.reader(ecoes_lines))
    next(parser)  # Skip titles

    for values in parser:
        ecoes_titles = [
            "mpan-core",
            "address-line-1",
            "address-line-2",
            "address-line-3",
            "address-line-4",
            "address-line-5",
            "address-line-6",
            "address-line-7",
            "address-line-8",
            "address-line-9",
            "post-code",
            "supplier",
            "registration-from",
            "mtc",
            "mtc-date",
            "llfc",
            "llfc-from",
            "pc",
            "ssc",
            "measurement-class",
            "energisation-status",
            "da",
            "dc",
            "mop",
            "mop-appoint-date",
            "gsp-group",
            "gsp-effective-from",
            "dno",
            "msn",
            "meter-install-date",
            "meter-type",
            "map-id",
        ]

        ecoes_row = dict(zip(ecoes_titles, map(str.strip, values)))
        mpan_core = ecoes_row["mpan-core"]
        mpan_spaces = " ".join(
            (
                mpan_core[:2],
                mpan_core[2:6],
                mpan_core[6:10],
                mpan_core[-3:],
            )
        )
        if mpan_spaces in exclude_mpan_cores:
            continue

        ecoes_row["mpan_spaces"] = mpan_spaces
        if mpan_spaces in ecoes_mpans:
            prev_row = ecoes_mpans[mpan_spaces]
            msn = ecoes_row["msn"]
            if len(msn) > 0:
                prev_msns = prev_row["msn"].split(",")
                prev_msns.append(msn)
                prev_row["msn"] = ", ".join(prev_msns)
        else:
            ecoes_mpans[mpan_spaces] = ecoes_row

    titles = (
        "mpan_core",
        "mpan_core_no_spaces",
        "ecoes_pc",
        "chellow_pc",
        "ecoes_mtc",
        "ecoes_mtc_date",
        "chellow_mtc",
        "ecoes_llfc",
        "ecoes_llfc_from",
        "chellow_llfc",
        "ecoes_ssc",
        "chellow_ssc",
        "ecoes_es",
        "chellow_es",
        "ecoes_supplier",
        "ecoes_supplier_registration_from",
        "chellow_supplier",
        "chellow_supplier_contract_name",
        "ecoes_dc",
        "chellow_dc",
        "ecoes_mop",
        "ecoes_mop_appoint_date",
        "chellow_mop",
        "ecoes_gsp_group",
        "ecoes_gsp_effective_from",
        "chellow_gsp_group",
        "ecoes_msn",
        "ecoes_msn_install_date",
        "chellow_msn",
        "ecoes_meter_type",
        "chellow_meter_type",
        "ignored",
        "problem",
    )
    writer.writerow(titles)

    for mpan_spaces, ecoes in sorted(ecoes_mpans.items()):
        problem = ""
        chellow_pc = ""
        chellow_mtc = ""
        chellow_llfc = ""
        chellow_llfc_desc = ""
        chellow_ssc = ""
        chellow_es = ""
        chellow_supplier = ""
        chellow_supplier_contract_name = ""
        chellow_supplier_contract_id = None
        chellow_dc = ""
        chellow_mop = ""
        chellow_gsp_group = ""
        chellow_msn = ""
        chellow_meter_type = ""
        chellow_supply_id = None
        chellow_era_id = None
        ignore = True
        ecoes_dno_code = ecoes["mpan-core"][:2]
        ecoes_dno = Party.get_dno_by_code(sess, ecoes_dno_code, now)
        ecoes_llfc_desc = ""
        chellow_site_code = ""
        chellow_site_name = ""
        diffs = []

        try:
            ecoes_es = ecoes["energisation-status"]
        except KeyError as e:
            raise e

        ecoes_disconnected = ecoes_es == ""
        current_chell = mpan_spaces in mpans

        if ecoes_disconnected and current_chell:
            problem += "Disconnected in ECOES, but current in Chellow. "
            ignore = False

        elif not ecoes_disconnected and not current_chell:
            era = sess.execute(
                select(Era)
                .filter(
                    or_(
                        Era.imp_mpan_core == mpan_spaces,
                        Era.exp_mpan_core == mpan_spaces,
                    ),
                )
                .order_by(Era.start_date.desc())
                .limit(1)
            ).scalar_one_or_none()
            if era is None:
                problem += f"In ECOES (as {ecoes_es}) but not in Chellow. "
            else:
                problem += f"In ECOES (as {ecoes_es}) but disconnected in Chellow. "
                if era.imp_mpan_core == mpan_spaces:
                    supplier_contract = era.imp_supplier_contract
                else:
                    supplier_contract = era.exp_supplier_contract
                chellow_supplier_contract_name = supplier_contract.name
                chellow_supplier_contract_id = supplier_contract.id
                chellow_supply_id = era.supply.id
                chellow_era_id = era.id
            ignore = False

        if current_chell:
            mpans.remove(mpan_spaces)
            era = (
                sess.scalars(
                    select(Era)
                    .where(
                        Era.finish_date == null(),
                        or_(
                            Era.imp_mpan_core == mpan_spaces,
                            Era.exp_mpan_core == mpan_spaces,
                        ),
                    )
                    .options(
                        joinedload(Era.supply).joinedload(Supply.gsp_group),
                        joinedload(Era.mop_contract)
                        .joinedload(Contract.party)
                        .joinedload(Party.participant),
                        joinedload(Era.dc_contract)
                        .joinedload(Contract.party)
                        .joinedload(Party.participant),
                        joinedload(Era.imp_supplier_contract)
                        .joinedload(Contract.party)
                        .joinedload(Party.participant),
                        joinedload(Era.exp_supplier_contract)
                        .joinedload(Contract.party)
                        .joinedload(Party.participant),
                        joinedload(Era.pc),
                        joinedload(Era.imp_llfc),
                        joinedload(Era.exp_llfc),
                        joinedload(Era.mtc_participant).joinedload(
                            MtcParticipant.meter_type
                        ),
                        joinedload(Era.ssc),
                        joinedload(Era.energisation_status),
                        joinedload(Era.channels),
                    )
                )
                .unique()
                .one()
            )
            chellow_supply_id = era.supply.id
            chellow_era_id = era.id
            chellow_es = era.energisation_status.code
            if ecoes_es != chellow_es:
                problem += "The energisation statuses don't match. "
                ignore = False
                diffs.append("es")

            if not (ecoes_es == "D" and chellow_es == "D"):
                if era.imp_mpan_core == mpan_spaces:
                    supplier_contract = era.imp_supplier_contract
                    llfc = era.imp_llfc
                else:
                    supplier_contract = era.exp_supplier_contract
                    llfc = era.exp_llfc

                chellow_pc = era.pc.code
                try:
                    if int(ecoes["pc"]) != int(chellow_pc):
                        problem += "The PCs don't match. "
                        ignore = False
                        diffs.append("pc")
                except ValueError:
                    problem += "Can't parse the PC. "
                    ignore = False

                chellow_mtc = era.mtc_participant.mtc.code
                try:
                    if int(ecoes["mtc"]) != int(chellow_mtc):
                        problem += "The MTCs don't match. "
                        ignore = False
                        diffs.append("mtc")
                except ValueError:
                    problem += "Can't parse the MTC. "
                    ignore = False

                chellow_llfc = llfc.code
                chellow_llfc_desc = llfc.description
                ecoes_llfc_code = ecoes["llfc"].zfill(3)
                if ecoes_llfc_code != chellow_llfc:
                    problem += "The LLFCs don't match. "
                    ignore = False
                    diffs.append("llfc")

                ecoes_llfc = ecoes_dno.find_llfc_by_code(sess, ecoes_llfc_code, now)
                if ecoes_llfc is not None:
                    ecoes_llfc_desc = ecoes_llfc.description

                chellow_ssc = era.ssc
                if chellow_ssc is None:
                    chellow_ssc = ""
                    chellow_ssc_int = None
                else:
                    chellow_ssc = chellow_ssc.code
                    chellow_ssc_int = int(chellow_ssc)

                if len(ecoes["ssc"]) > 0:
                    ecoes_ssc_int = int(ecoes["ssc"])
                else:
                    ecoes_ssc_int = None

                if ecoes_ssc_int != chellow_ssc_int and not (
                    ecoes_ssc_int is None and chellow_ssc_int is None
                ):
                    problem += "The SSCs don't match. "
                    ignore = False
                    diffs.append("ssc")

                chellow_supplier = supplier_contract.party.participant.code
                chellow_supplier_contract_name = supplier_contract.name
                chellow_supplier_contract_id = supplier_contract.id
                if chellow_supplier != ecoes["supplier"]:
                    problem += "The supplier codes don't match. "
                    ignore = False
                    diffs.append("supplier")

                dc_contract = era.dc_contract
                chellow_dc_props = dc_contract.make_properties()
                if "nhh_participant" in chellow_dc_props:
                    chellow_dc = chellow_dc_props["nhh_participant"]
                else:
                    chellow_dc = dc_contract.party.participant.code

                if chellow_dc != ecoes["dc"]:
                    problem += "The DC codes don't match. "
                    ignore = False
                    diffs.append("dc")

                mop_contract = era.mop_contract
                if mop_contract is None:
                    chellow_mop = ""
                else:
                    chellow_mop = mop_contract.party.participant.code

                if chellow_mop != ecoes["mop"]:
                    problem += "The MOP codes don't match. "
                    ignore = False
                    diffs.append("mop")

                chellow_gsp_group = era.supply.gsp_group.code
                if chellow_gsp_group != ecoes["gsp-group"]:
                    problem += "The GSP group codes don't match. "
                    ignore = False
                    diffs.append("gsp_group")

                chellow_site = era.get_physical_site(sess)
                chellow_site_code = chellow_site.code
                chellow_site_name = chellow_site.name

                chellow_msn = era.msn

                if set([m.strip() for m in chellow_msn.split(",")]) != set(
                    [m.strip() for m in ecoes["msn"].split(",")]
                ):
                    problem += "The meter serial numbers don't match. "
                    diffs.append("msn")
                    if mpan_spaces not in ignore_mpan_cores_msn:
                        ignore = False
                elif mpan_spaces in ignore_mpan_cores_msn:
                    problem += (
                        "This MPAN core is in mpan_cores_ignore and yet the meter "
                        "serial numbers do match. "
                    )

                chellow_dtc_meter_type = era.dtc_meter_type
                if chellow_dtc_meter_type is None:
                    chellow_meter_type = ""
                else:
                    chellow_meter_type = chellow_dtc_meter_type.code

                if chellow_meter_type != ecoes["meter-type"]:
                    problem += "The DTC meter types don't match."
                    ignore = False
                    diffs.append("meter_type")

        if len(problem) > 0 and not (not show_ignored and ignore):
            address_lines = [ecoes[f"address-line-{i}"] for i in range(1, 10)]
            values = {
                "mpan_core": mpan_spaces,
                "mpan_core_no_spaces": ecoes["mpan-core"],
                "ecoes_pc": ecoes["pc"],
                "chellow_pc": chellow_pc,
                "ecoes_mtc": ecoes["mtc"],
                "ecoes_mtc_date": _parse_date(ecoes["mtc-date"]),
                "chellow_mtc": chellow_mtc,
                "ecoes_llfc": ecoes["llfc"],
                "ecoes_llfc_desc": ecoes_llfc_desc,
                "ecoes_llfc_from": _parse_date(ecoes["llfc-from"]),
                "chellow_llfc": chellow_llfc,
                "chellow_llfc_desc": chellow_llfc_desc,
                "ecoes_ssc": ecoes["ssc"],
                "chellow_ssc": chellow_ssc,
                "ecoes_es": ecoes["energisation-status"],
                "chellow_es": chellow_es,
                "ecoes_supplier": ecoes["supplier"],
                "ecoes_supplier_registration_from": _parse_date(
                    ecoes["registration-from"]
                ),
                "chellow_supplier": chellow_supplier,
                "chellow_supplier_contract_name": chellow_supplier_contract_name,
                "ecoes_dc": ecoes["dc"],
                "chellow_dc": chellow_dc,
                "ecoes_mop": ecoes["mop"],
                "ecoes_mop_appoint_date": _parse_date(ecoes["mop-appoint-date"]),
                "chellow_mop": chellow_mop,
                "ecoes_gsp_group": ecoes["gsp-group"],
                "ecoes_gsp_effective_from": _parse_date(ecoes["gsp-effective-from"]),
                "chellow_gsp_group": chellow_gsp_group,
                "ecoes_msn": ecoes["msn"],
                "chellow_msn": chellow_msn,
                "ecoes_msn_install_date": _parse_date(ecoes["meter-install-date"]),
                "ecoes_meter_type": ecoes["meter-type"],
                "chellow_meter_type": chellow_meter_type,
                "ignored": ignore,
                "problem": problem,
                "address": ", ".join(
                    [a for a in address_lines if len(a) > 0 and a != "NULL"]
                ),
                "chellow_site_code": chellow_site_code,
                "chellow_site_name": chellow_site_name,
            }
            writer.writerow(csv_make_val(values[t]) for t in titles)
            values["chellow_supplier_contract_id"] = chellow_supplier_contract_id
            values["chellow_supply_id"] = chellow_supply_id
            values["diffs"] = diffs
            values["chellow_era_id"] = chellow_era_id
            report_run.insert_row(sess, "", titles, values, {})
            sess.commit()

    for mpan_core in mpans:
        supply = Supply.get_by_mpan_core(sess, mpan_core)
        era = supply.find_era_at(sess, None)
        if era.imp_mpan_core == mpan_core:
            supplier_contract = era.imp_supplier_contract
            llfc = era.imp_llfc
        else:
            supplier_contract = era.exp_supplier_contract
            llfc = era.exp_llfc

        ssc = "" if era.ssc is None else era.ssc.code

        es = era.energisation_status.code

        dc_contract = era.dc_contract
        dc = "" if dc_contract is None else dc_contract.party.participant.code

        mop_contract = era.mop_contract
        mop = "" if mop_contract is None else mop_contract.party.participant.code

        msn = "" if era.msn is None else era.msn

        dtc_meter_type = era.dtc_meter_type
        meter_type = "" if dtc_meter_type is None else dtc_meter_type.code

        values = {
            "mpan_core": mpan_core,
            "mpan_core_no_spaces": mpan_core.replace(" ", ""),
            "ecoes_pc": "",
            "chellow_pc": era.pc.code,
            "ecoes_mtc": "",
            "ecoes_mtc_date": "",
            "chellow_mtc": era.mtc_participant.mtc.code,
            "ecoes_llfc": "",
            "ecoes_llfc_from": "",
            "chellow_llfc": llfc.code,
            "ecoes_ssc": "",
            "chellow_ssc": ssc,
            "ecoes_es": "",
            "chellow_es": es,
            "ecoes_supplier": "",
            "ecoes_supplier_registration_from": "",
            "chellow_supplier": supplier_contract.party.participant.code,
            "chellow_supplier_contract_name": supplier_contract.name,
            "ecoes_dc": "",
            "chellow_dc": dc,
            "ecoes_mop": "",
            "ecoes_mop_appoint_date": "",
            "chellow_mop": mop,
            "ecoes_gsp_group": "",
            "ecoes_gsp_effective_from": "",
            "chellow_gsp_group": supply.gsp_group.code,
            "ecoes_msn": "",
            "chellow_msn": msn,
            "ecoes_msn_install_date": "",
            "ecoes_meter_type": "",
            "chellow_meter_type": meter_type,
            "ignored": False,
            "problem": "In Chellow, but not in ECOES.",
        }
        writer.writerow(csv_make_val(values[t]) for t in titles)
        values["chellow_supplier_contract_id"] = supplier_contract.id
        values["chellow_supply_id"] = era.supply.id
        values["diffs"] = []
        values["chellow_era_id"] = era.id
        report_run.insert_row(sess, "", titles, values, {})


def do_get(sess):
    show_ignored = req_bool("show_ignored")
    report_run = ReportRun.insert(
        sess,
        FNAME,
        g.user,
        FNAME,
        {},
    )
    sess.commit()
    args = g.user.id, show_ignored, report_run.id
    threading.Thread(target=content, args=args).start()
    return redirect(f"/report_runs/{report_run.id}", 303)
