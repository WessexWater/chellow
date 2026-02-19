from sqlalchemy import select

from chellow.models import GSupply, User


def make_issue_bundles(sess, issues):
    return [make_issue_bundle(sess, issue) for issue in issues]


def make_issue_bundle(sess, issue):
    props = issue.properties
    supply_bundles = []
    if "owner_id" in props:
        owner = User.get_by_id(sess, props["owner_id"])
    else:
        owner = None
    bundle = {
        "issue": issue,
        "latest_entry": None if len(issue.g_entries) == 0 else issue.g_entries[0],
        "supplies": supply_bundles,
        "owner": owner,
    }
    for supply in sess.scalars(
        select(GSupply)
        .where(GSupply.id.in_(props.get("supply_ids", [])))
        .order_by(GSupply.id)
    ).all():
        era = supply.g_eras[-1]
        site = era.get_physical_site(sess)
        supply_bundles.append({"supply": supply, "era": era, "site": site})
    return bundle
