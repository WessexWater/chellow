import csv
import sys
import threading
import traceback

from flask import g, redirect, render_template, request

from sqlalchemy import Integer, any_, cast, select
from sqlalchemy.dialects.postgresql import JSONB, array

from chellow.dloads import open_file
from chellow.e.issues import make_issue_bundles
from chellow.models import (
    Issue,
    RSession,
    User,
)
from chellow.utils import (
    csv_make_val,
    req_checkbox,
)


def _make_bundles(
    sess,
    contract_ids,
    owner_ids,
    supply_ids,
    limit=None,
):
    q = select(Issue).order_by(Issue.is_open.desc(), Issue.date_created)
    if limit is not None:
        q = q.limit(limit)
    if len(contract_ids) > 0:
        q = q.where(Issue.contract_id.in_(contract_ids))
    if len(owner_ids) > 0:
        q = q.where(cast(Issue.properties["owner_id"], Integer).in_(owner_ids))
    if len(supply_ids) > 0:
        ids_jsonb = array([cast([sid], JSONB) for sid in supply_ids])
        q = q.where(Issue.properties["supply_ids"].op("@>")(any_(ids_jsonb)))
    issues = sess.scalars(q)
    return make_issue_bundles(sess, issues)


def _make_vals(sess, contract_ids, owner_ids, supply_ids):
    for bundle in _make_bundles(sess, contract_ids, owner_ids, supply_ids):
        issue = bundle["issue"]
        props = issue.properties
        owner = bundle["owner"]
        values = {
            "issue_id": issue.id,
            "contract_role": issue.contract.market_role.code,
            "contract_name": issue.contract.name,
            "date_created": issue.date_created,
            "owner": None if owner is None else owner.email_address,
            "status": "open" if issue.is_open else "closed",
            "subject": props.get("subject"),
            "imp_mpan_core": None,
            "exp_mpan_core": None,
            "site_code": None,
            "site_name": None,
        }
        latest_entry = bundle["latest_entry"]
        if latest_entry is None:
            values["latest_entry_timestamp"] = None
            values["latest_entry_markdown"] = None
        else:
            values["latest_entry_timestamp"] = latest_entry.timestamp
            values["latest_entry_markdown"] = latest_entry.markdown

        supplies = bundle["supplies"]
        if len(supplies) == 0:
            yield values
        else:
            for supply_bundle in supplies:
                values = values.copy()
                era = supply_bundle["era"]
                site = supply_bundle["site"]
                values["imp_mpan_core"] = era.imp_mpan_core
                values["exp_mpan_core"] = era.exp_mpan_core
                values["site_code"] = site.code
                values["site_name"] = site.name
                yield values


def content(user_id, contract_ids, owner_ids, supply_ids):
    f = writer = None
    try:
        with RSession() as sess:
            user = User.get_by_id(sess, user_id)
            f = open_file("issues.csv", user, mode="w", newline="")
            writer = csv.writer(f, lineterminator="\n")
            titles = (
                "issue_id",
                "contract_role",
                "contract_name",
                "date_created",
                "owner",
                "status",
                "subject",
                "imp_mpan_core",
                "exp_mpan_core",
                "site_code",
                "site_name",
                "latest_entry_timestamp",
                "latest_entry_markdown",
            )
            writer.writerow(titles)
            for vals in _make_vals(sess, contract_ids, owner_ids, supply_ids):
                writer.writerow(csv_make_val(vals[t]) for t in titles)

    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        writer.writerow([msg])
    finally:
        if f is not None:
            f.close()


LIMIT = 200


def do_get(sess):
    contract_ids = [int(x) for x in request.values.getlist("contract_id")]
    owner_ids = [int(x) for x in request.values.getlist("owner_id")]
    supply_ids = [int(x) for x in request.values.getlist("supply_id")]
    as_csv = req_checkbox("as_csv")

    if as_csv:
        args = (g.user.id, contract_ids, owner_ids, supply_ids)
        threading.Thread(target=content, args=args).start()
        return redirect("/downloads", 303)
    else:
        issue_bundles = _make_bundles(
            sess, contract_ids, owner_ids, supply_ids, limit=LIMIT
        )
        return render_template(
            "reports/issues.html",
            contract_ids=contract_ids,
            owner_ids=owner_ids,
            supply_ids=supply_ids,
            limit=LIMIT,
            issue_bundles=issue_bundles,
        )
