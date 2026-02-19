import csv
import sys
import threading
import traceback

from flask import g, redirect, render_template, request

from sqlalchemy import Integer, any_, cast, select
from sqlalchemy.dialects.postgresql import JSONB, array

from chellow.dloads import open_file
from chellow.gas.issues import make_issue_bundles
from chellow.models import (
    GIssue,
    RSession,
    User,
)
from chellow.utils import (
    csv_make_val,
    req_checkbox,
)


def _make_bundles(sess, contract_ids, owner_ids, supply_ids, is_opens, limit=None):
    q = select(GIssue).order_by(GIssue.is_open.desc(), GIssue.date_created)
    if limit is not None:
        q = q.limit(limit)
    if len(contract_ids) > 0:
        q = q.where(GIssue.g_contract_id.in_(contract_ids))
    if len(owner_ids) > 0:
        q = q.where(cast(GIssue.properties["owner_id"], Integer).in_(owner_ids))
    if len(supply_ids) > 0:
        ids_jsonb = array([cast([sid], JSONB) for sid in supply_ids])
        q = q.where(GIssue.properties["supply_ids"].op("@>")(any_(ids_jsonb)))
    if len(is_opens) > 0:
        q = q.where(GIssue.is_open.in_(is_opens))
    issues = sess.scalars(q)
    return make_issue_bundles(sess, issues)


def _make_vals(sess, contract_ids, owner_ids, supply_ids, is_opens):
    for bundle in _make_bundles(sess, contract_ids, owner_ids, supply_ids, is_opens):
        issue = bundle["issue"]
        props = issue.properties
        owner = bundle["owner"]
        contract = issue.g_contract
        values = {
            "issue_id": issue.id,
            "contract_name": contract.name,
            "date_created": issue.date_created,
            "owner": None if owner is None else owner.email_address,
            "status": "open" if issue.is_open else "closed",
            "subject": props.get("subject"),
            "mprn_core": None,
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
                site = supply_bundle["site"]
                values["mprn"] = supply_bundle["supply"].mprn
                values["site_code"] = site.code
                values["site_name"] = site.name
                yield values


def content(user_id, contract_ids, owner_ids, supply_ids, is_opens):
    f = writer = None
    try:
        with RSession() as sess:
            user = User.get_by_id(sess, user_id)
            f = open_file("issues.csv", user, mode="w", newline="")
            writer = csv.writer(f, lineterminator="\n")
            titles = (
                "issue_id",
                "contract_name",
                "date_created",
                "owner",
                "status",
                "subject",
                "mprn",
                "site_code",
                "site_name",
                "latest_entry_timestamp",
                "latest_entry_markdown",
            )
            writer.writerow(titles)
            for vals in _make_vals(sess, contract_ids, owner_ids, supply_ids, is_opens):
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
    is_opens = [x == "true" for x in request.values.getlist("is_open")]
    as_csv = req_checkbox("as_csv")

    if as_csv:
        args = (g.user.id, contract_ids, owner_ids, supply_ids, is_opens)
        threading.Thread(target=content, args=args).start()
        return redirect("/downloads", 303)
    else:
        issue_bundles = _make_bundles(
            sess, contract_ids, owner_ids, supply_ids, is_opens, limit=LIMIT
        )
        return render_template(
            "reports/g_issues.html",
            contract_ids=contract_ids,
            owner_ids=owner_ids,
            supply_ids=supply_ids,
            is_opens=is_opens,
            limit=LIMIT,
            issue_bundles=issue_bundles,
        )
