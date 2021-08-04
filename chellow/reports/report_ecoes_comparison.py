import csv
import os
import sys
import threading
import traceback

from flask import g

import requests

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import null, or_

from werkzeug.exceptions import BadRequest

import chellow.dloads
from chellow.models import Contract, Era, Mtc, Party, Session, Source, Supply
from chellow.utils import req_bool
from chellow.views import chellow_redirect


def content(user, show_ignored):
    sess = f = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            "ecoes_comparison.csv", user
        )
        f = open(running_name, mode="w", newline="")

        props = Contract.get_non_core_by_name(sess, "configuration").make_properties()

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
            "prefix",
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
        url_prefix = ecoes_props["prefix"]

        proxies = props.get("proxies", {})
        s = requests.Session()
        s.verify = False
        r = s.get(url_prefix, proxies=proxies)
        data = {
            "Username": ecoes_props["user_name"],
            "Password": ecoes_props["password"],
        }
        r = s.post(url_prefix, data=data, allow_redirects=False)
        r = s.get(
            f"{url_prefix}NonDomesticCustomer/ExportPortfolioMPANs?fileType=csv",
            proxies=proxies,
        )

        _process(
            sess,
            r.text.splitlines(True),
            exclude_mpan_cores,
            ignore_mpan_cores_msn,
            f,
            show_ignored,
        )

    except BaseException as e:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        f.write(msg)
        raise e
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def _process(
    sess, ecoes_lines, exclude_mpan_cores, ignore_mpan_cores_msn, f, show_ignored
):
    writer = csv.writer(f, lineterminator="\n")

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
            prev_row["meter_count"] += 1
        else:
            ecoes_row["meter_count"] = 1
            ecoes_mpans[mpan_spaces] = ecoes_row

    titles = (
        "MPAN Core",
        "MPAN Core No Spaces",
        "ECOES PC",
        "Chellow PC",
        "ECOES MTC",
        "Chellow MTC",
        "ECOES LLFC",
        "Chellow LLFC",
        "ECOES SSC",
        "Chellow SSC",
        "ECOES Energisation Status",
        "Chellow Energisation Status",
        "ECOES Supplier",
        "Chellow Supplier",
        "ECOES DC",
        "Chellow DC",
        "ECOES MOP",
        "Chellow MOP",
        "ECOES GSP Group",
        "Chellow GSP Group",
        "ECOES MSN",
        "Chellow MSN",
        "ECOES Meter Type",
        "Chellow Meter Type",
        "Ignored",
        "Problem",
    )
    writer.writerow(titles)

    for mpan_spaces, ecoes in sorted(ecoes_mpans.items()):
        problem = ""
        ignore = True

        try:
            ecoes_es = ecoes["energisation-status"]
        except KeyError as e:
            raise e

        ecoes_disconnected = ecoes_es == ""
        current_chell = mpan_spaces in mpans

        if ecoes["meter_count"] > 1:
            problem += (
                f"There are {ecoes['meter_count']} meters associated with this MPAN "
                f"core in ECOES, but Chellow only supports one meter per supply at the "
                f"moment. If there really should be multiple meters for this supply, "
                f"let me know and I'll add support for it in Chellow."
            )
            ignore = False

        if ecoes_disconnected and current_chell:
            problem += "Disconnected in ECOES, but current in Chellow. "
            ignore = False

        elif not ecoes_disconnected and not current_chell:
            problem += f"In ECOES (as {ecoes_es}) but disconnected in Chellow. "
            ignore = False

        if current_chell:
            mpans.remove(mpan_spaces)
            era = sess.execute(
                select(Era)
                .filter(
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
                    joinedload(Era.mtc).joinedload(Mtc.meter_type),
                    joinedload(Era.ssc),
                    joinedload(Era.energisation_status),
                    joinedload(Era.channels),
                )
            ).scalar()

            chellow_es = era.energisation_status.code
            if ecoes_es != chellow_es:
                problem += "The energisation statuses don't match. "
                ignore = False

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
                except ValueError:
                    problem += "Can't parse the PC. "
                    ignore = False

                chellow_mtc = era.mtc.code
                try:
                    if int(ecoes["mtc"]) != int(chellow_mtc):
                        problem += "The MTCs don't match. "
                        ignore = False
                except ValueError:
                    problem += "Can't parse the MTC. "
                    ignore = False

                chellow_llfc = llfc.code
                if ecoes["llfc"].zfill(3) != chellow_llfc:
                    problem += "The LLFCs don't match. "
                    ignore = False

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

                chellow_supplier = supplier_contract.party.participant.code
                if chellow_supplier != ecoes["supplier"]:
                    problem += "The supplier codes don't match. "
                    ignore = False

                dc_contract = era.dc_contract
                if dc_contract is None:
                    chellow_dc = ""
                else:
                    chellow_dc = dc_contract.party.participant.code

                if chellow_dc != ecoes["dc"]:
                    problem += "The DC codes don't match. "
                    ignore = False

                mop_contract = era.mop_contract
                if mop_contract is None:
                    chellow_mop = ""
                else:
                    chellow_mop = mop_contract.party.participant.code

                if chellow_mop != ecoes["mop"]:
                    problem += "The MOP codes don't match. "
                    ignore = False

                chellow_gsp_group = era.supply.gsp_group.code
                if chellow_gsp_group != ecoes["gsp-group"]:
                    problem += "The GSP group codes don't match. "
                    ignore = False

                chellow_msn = era.msn
                if chellow_msn is None:
                    chellow_msn = ""

                if chellow_msn != ecoes["msn"]:
                    problem += "The meter serial numbers don't match. "
                    if mpan_spaces not in ignore_mpan_cores_msn:
                        ignore = False
                elif mpan_spaces in ignore_mpan_cores_msn:
                    problem += (
                        "This MPAN core is in mpan_cores_ignore and yet the meter "
                        "serial numbers do match. "
                    )

                chellow_meter_type = _meter_type(era)

                if chellow_meter_type != ecoes["meter-type"]:
                    problem += (
                        "The meter types don't match. See "
                        "https://dtc.mrasco.com/DataItem.aspx?ItemCounter=0483 "
                    )
                    ignore = False
        else:
            chellow_pc = ""
            chellow_mtc = ""
            chellow_llfc = ""
            chellow_ssc = ""
            chellow_es = ""
            chellow_supplier = ""
            chellow_dc = ""
            chellow_mop = ""
            chellow_gsp_group = ""
            chellow_msn = ""
            chellow_meter_type = ""

        if len(problem) > 0 and not (not show_ignored and ignore):
            writer.writerow(
                [
                    mpan_spaces,
                    ecoes["mpan-core"],
                    ecoes["pc"],
                    chellow_pc,
                    ecoes["mtc"],
                    chellow_mtc,
                    ecoes["llfc"],
                    chellow_llfc,
                    ecoes["ssc"],
                    chellow_ssc,
                    ecoes["energisation-status"],
                    chellow_es,
                    ecoes["supplier"],
                    chellow_supplier,
                    ecoes["dc"],
                    chellow_dc,
                    ecoes["mop"],
                    chellow_mop,
                    ecoes["gsp-group"],
                    chellow_gsp_group,
                    ecoes["msn"],
                    chellow_msn,
                    ecoes["meter-type"],
                    chellow_meter_type,
                    ignore,
                    problem,
                ]
            )
        sess.expunge_all()

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

        meter_type = _meter_type(era)

        writer.writerow(
            [
                mpan_core,
                mpan_core.replace(" ", ""),
                "",
                era.pc.code,
                "",
                era.mtc.code,
                "",
                llfc.code,
                "",
                ssc,
                "",
                es,
                "",
                supplier_contract.party.participant.code,
                "",
                dc,
                "",
                mop,
                "",
                supply.gsp_group.code,
                "",
                msn,
                "",
                meter_type,
                False,
                "In Chellow, but not in ECOES.",
            ]
        )


def _meter_type(era):
    props = era.props
    try:
        return props["meter_type"]
    except KeyError:
        if era.pc.code == "00":
            return "H"
        elif len(era.channels) > 0:
            return "RCAMR"
        elif era.mtc.meter_type.code in ["UM", "PH"]:
            return ""
        else:
            return "N"


def do_get(sess):
    show_ignored = req_bool("show_ignored")
    threading.Thread(target=content, args=(g.user, show_ignored)).start()
    return chellow_redirect("/downloads", 303)
