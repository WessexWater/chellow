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
from chellow.models import Contract, Era, Session, Site, SiteEra
from chellow.views import chellow_redirect


def _process_sites(sess, file_like, writer, props):

    ASSET_KEY = "asset_comparison"
    try:
        asset_props = props[ASSET_KEY]
    except KeyError:
        raise BadRequest(
            f"The property {ASSET_KEY} cannot be found in the configuration "
            f"properties."
        )

    if not isinstance(asset_props, dict):
        raise BadRequest("The {ASSET_KEY} property must be a map.")

    for key in ("ignore_site_codes",):
        try:
            asset_props[key]
        except KeyError:
            raise BadRequest(
                f"The property {key} cannot be found in the '{ASSET_KEY}' section "
                f"of the configuration properties."
            )

    ignore_site_codes = asset_props["ignore_site_codes"]

    site_codes_select = (
        select(Site.code)
        .filter(Site.code.notin_(ignore_site_codes))
        .order_by(Site.code)
    )
    site_codes = [s[0] for s in sess.execute(site_codes_select)]

    titles = (
        "Site Code",
        "Asset Status",
        "Chellow Status",
        "Problem",
    )
    writer.writerow(titles)

    parser = iter(csv.reader(file_like))
    next(parser)  # Skip titles

    for values in parser:
        if len(values) == 0:
            continue

        problem = ""
        asset_code = values[0].strip()
        asset_status = values[3].strip()

        if asset_code in ignore_site_codes:
            continue

        eras = sess.execute(
            select(Era)
            .join(SiteEra)
            .join(Site)
            .filter(Site.code == asset_code, Era.finish_date == null())
            .options(joinedload(Era.energisation_status))
        ).all()

        current_chell = len(eras) > 0

        if asset_status in ("IN USE / IN SERVICE", "STORED SPARE"):
            current_asset = True
        elif asset_status in (
            "DEMOLISHED",
            "SOLD",
            "ABANDONED",
        ):
            current_asset = False
        elif asset_status in (
            "OUT OF SERVICE",
            "SITE BEING CHECKED",
            "UNKNOWN",
            "UNADOPTED",
            "UNDER CONSTRUCTION",
            "EMERGENCY",
            "",
        ):
            if asset_code in site_codes:
                site_codes.remove(asset_code)
            continue
        else:
            raise BadRequest(f"Asset status '{asset_status}' not recognized.")

        problem = ""

        if asset_code in site_codes:
            site_codes.remove(asset_code)
            if current_chell:
                energised_eras = [
                    r for r in eras if r[0].energisation_status.code == "E"
                ]
                is_deenergized = len(energised_eras) == 0

                if is_deenergized:
                    if current_asset:
                        problem += (
                            "De-energised in Chellow, but current in the "
                            "asset database. "
                        )
                    else:
                        problem += (
                            "De-energised in Chellow, but not current in the "
                            "asset database. "
                        )
                else:
                    if not current_asset:
                        problem += (
                            "Energised in Chellow, but not current in the asset "
                            "database. "
                        )

            else:
                if current_asset:
                    pass
                    """
                    problem += (
                        "No current supply in Chellow, but current in the asset "
                        "database. "
                    )
                    """

        else:
            pass
            """
            if current_asset:
                problem += "In asset data as current, but site not in Chellow"
            """

        if len(problem) > 0:
            row = [asset_code, asset_status, current_chell, problem]
            writer.writerow(row)
        sess.expunge_all()

    for site_code in site_codes:
        eras = sess.execute(
            select(Era)
            .join(SiteEra)
            .join(Site)
            .filter(Site.code == site_code, Era.finish_date == null())
            .options(joinedload(Era.energisation_status))
        ).all()

        current_chell = len(eras) > 0
        if current_chell:
            writer.writerow(
                [
                    site_code,
                    "",
                    True,
                    "Current in Chellow but not present in asset data.",
                ]
            )


def content(user, file_like):
    sess = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            "asset_comparison.csv", user
        )
        f = open(running_name, mode="w", newline="")
        writer = csv.writer(f, lineterminator="\n")

        props = Contract.get_non_core_by_name(sess, "configuration").make_properties()

        _process_sites(sess, file_like, writer, props)
    except BaseException:
        msg = traceback.format_exc()
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

    args = user, StringIO(file_item.read().decode("utf8"))
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
