import csv
import os
import sys
import threading
import traceback

from flask import g

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import null

import chellow.dloads
from chellow.models import (
    Contract,
    Era,
    Party,
    ReportRun,
    Session,
    SiteEra,
    Source,
    Supply,
    User,
)
from chellow.views.home import chellow_redirect


FNAME = "supply_contacts"


def content(user_id, report_run_id):
    sess = f = report_run = None
    try:
        sess = Session()
        user = User.get_by_id(sess, user_id)
        running_name, finished_name = chellow.dloads.make_names(f"{FNAME}.csv", user)
        f = open(running_name, mode="w", newline="")
        report_run = ReportRun.get_by_id(sess, report_run_id)

        _process(sess, f, report_run)
        report_run.update("finished")
        sess.commit()

    except BaseException as e:
        msg = traceback.format_exc()
        print(msg)
        if report_run is not None:
            report_run.update("interrupted")
            report_run.insert_row(sess, "", ["problem"], {"problem": msg}, {})
            sess.commit()
        sys.stderr.write(msg)
        if f is not None:
            f.write(msg)
        raise e
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def _process(sess, f, report_run):
    writer = csv.writer(f, lineterminator="\n")

    titles = (
        "site",
        "dno_contact",
        "import_mpan_core",
        "import_supplier_contact",
        "problem",
    )
    writer.writerow(titles)

    configuration = Contract.get_non_core_by_name(sess, "configuration")
    props = configuration.make_properties()
    dno_contacts = props["dno_contacts"]
    dno_contact_message = props.get("dno_contact_message")
    run_data = report_run.data
    run_data["dno_contact_message"] = dno_contact_message
    report_run.update_data(run_data)
    sess.commit()

    for era in (
        sess.execute(
            select(Era)
            .join(Supply)
            .join(Supply.dno)
            .join(Source)
            .where(
                Era.finish_date == null(),
                Party.dno_code.notin_(("88", "99")),
                Era.finish_date == null(),
                Source.code != "3rd-party",
            )
            .order_by(Era.supply_id)
            .options(
                joinedload(Era.site_eras).joinedload(SiteEra.site),
                joinedload(Era.supply).joinedload(Supply.dno),
                joinedload(Era.imp_supplier_contract),
                joinedload(Era.mop_contract),
            )
        )
        .scalars()
        .unique()
    ):

        for site_era in era.site_eras:
            if site_era.is_physical:
                site = site_era.site

        dno = era.supply.dno

        imp_supplier_contract = era.imp_supplier_contract
        if imp_supplier_contract is None:
            imp_supplier_name = None
        else:
            imp_supplier_name = era.imp_supplier_contract.party.name

        values = {
            "site_code": site.code,
            "site_name": site.name,
            "dno_name": dno.name,
            "dno_contact": dno_contacts.get(dno.dno_code),
            "mop_name": era.mop_contract.party.name,
            "import_mpan_core": era.imp_mpan_core,
            "import_supplier_name": imp_supplier_name,
        }
        report_run.insert_row(sess, "", titles, values, {})
        sess.commit()


def do_get(sess):
    report_run = ReportRun.insert(
        sess,
        FNAME,
        g.user,
        FNAME,
        {},
    )
    sess.commit()
    threading.Thread(target=content, args=(g.user.id, report_run.id)).start()
    return chellow_redirect(f"/report_runs/{report_run.id}", 303)
