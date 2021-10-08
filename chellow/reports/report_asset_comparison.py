import csv
import os
import sys
import threading
import traceback
from io import StringIO

from flask import g, request

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import null

from werkzeug.exceptions import BadRequest

import chellow.dloads
from chellow.models import Contract, Era, ReportRun, Session, Site, SiteEra
from chellow.views import chellow_redirect

STATUSES_ACTIVE = ("IN USE / IN SERVICE", "STORED SPARE")
STATUSES_INACTIVE = ("DEMOLISHED", "SOLD", "ABANDONED")
STATUSES_IGNORE = (
    "OUT OF SERVICE",
    "SITE BEING CHECKED",
    "UNKNOWN",
    "UNADOPTED",
    "UNDER CONSTRUCTION",
    "EMERGENCY",
    "",
)


def _process_sites(sess, file_like, writer, props, report_run):

    ASSET_KEY = "asset_comparison"
    try:
        asset_props = props[ASSET_KEY]
    except KeyError:
        raise BadRequest(
            f"The property {ASSET_KEY} cannot be found in the configuration properties."
        )

    if not isinstance(asset_props, dict):
        raise BadRequest("The {ASSET_KEY} property must be a map.")

    for key in ("ignore_site_codes",):
        try:
            asset_props[key]
        except KeyError:
            raise BadRequest(
                f"The property {key} cannot be found in the '{ASSET_KEY}' section of "
                f"the configuration properties."
            )

    ignore_site_codes = asset_props["ignore_site_codes"]

    site_codes_select = (
        select(Site.code)
        .filter(Site.code.notin_(ignore_site_codes))
        .order_by(Site.code)
    )
    site_codes = [s[0] for s in sess.execute(site_codes_select)]

    titles = (
        "site_code",
        "asset_status",
        "chellow_status",
    )
    writer.writerow(titles)

    parser = iter(csv.reader(file_like))
    next(parser)  # Skip titles

    for values in parser:
        if len(values) == 0:
            continue

        asset_code = values[0].strip()
        asset_status = values[3].strip()

        if asset_code in ignore_site_codes:
            continue

        if asset_code in site_codes:
            site_codes.remove(asset_code)

        eras = sess.execute(
            select(Era)
            .join(SiteEra)
            .join(Site)
            .filter(Site.code == asset_code, Era.finish_date == null())
            .options(joinedload(Era.energisation_status))
        ).all()

        if len(eras) == 0:
            is_energised = None
            is_energised_str = "no supplies"
        else:
            energised_eras = [r for r in eras if r[0].energisation_status.code == "E"]
            is_energised = len(energised_eras) > 0
            is_energised_str = "energised" if is_energised is True else "de-energised"

        if asset_status in STATUSES_ACTIVE:
            active_asset = True
        elif asset_status in STATUSES_INACTIVE:
            active_asset = False
        elif asset_status in STATUSES_IGNORE:
            active_asset = None
        else:
            raise BadRequest(f"Asset status '{asset_status}' not recognized.")

        if active_asset is False and is_energised is not None:
            values = {
                "site_code": asset_code,
                "asset_status": asset_status,
                "chellow_status": is_energised_str,
            }
            writer.writerow([values[t] for t in titles])
            site = Site.find_by_code(sess, asset_code)
            values["site_id"] = None if site is None else site.id
            report_run.insert_row(sess, "", titles, values, {})
            sess.commit()

    for site_code in site_codes:
        eras = sess.execute(
            select(Era)
            .join(SiteEra)
            .join(Site)
            .filter(Site.code == site_code, Era.finish_date == null())
            .options(joinedload(Era.energisation_status))
        ).all()

        if len(eras) > 0:
            e_eras = [r for r in eras if r[0].energisation_status.code == "E"]
            is_energised_str = "energised" if len(e_eras) > 0 else "de-energised"
            values = {
                "site_code": site_code,
                "asset_status": None,
                "chellow_status": is_energised_str,
            }
            writer.writerow([values[t] for t in titles])
            site = Site.find_by_code(sess, site_code)
            values["site_id"] = None if site is None else site.id
            report_run.insert_row(sess, "", titles, values, {})
            sess.commit()


FNAME = "asset_comparison"


def content(user, file_like, report_run_id):
    sess = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(FNAME + ".csv", user)
        f = open(running_name, mode="w", newline="")
        writer = csv.writer(f, lineterminator="\n")
        report_run = ReportRun.get_by_id(sess, report_run_id)

        props = Contract.get_non_core_by_name(sess, "configuration").make_properties()

        _process_sites(sess, file_like, writer, props, report_run)
        report_run.update("finished")
        sess.commit()
    except BaseException:
        msg = traceback.format_exc()
        if report_run is not None:
            report_run.update("interrupted")
            report_run.insert_row(sess, "", ["error"], {"error": msg}, {})
            sess.commit()
        sys.stderr.write(msg)
        writer.writerow([msg])
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_post(sess):
    user = g.user
    file_item = request.files["asset_file"]

    report_run = ReportRun.insert(
        sess,
        FNAME,
        user,
        FNAME,
        {
            "STATUSES_ACTIVE": STATUSES_ACTIVE,
            "STATUSES_INACTIVE": STATUSES_INACTIVE,
            "STATUSES_IGNORE": STATUSES_IGNORE,
        },
    )
    sess.commit()
    args = user, StringIO(file_item.read().decode("utf8")), report_run.id
    threading.Thread(target=content, args=args).start()
    return chellow_redirect(f"/report_runs/{report_run.id}", 303)
