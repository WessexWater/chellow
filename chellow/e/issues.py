from sqlalchemy import select

from chellow.models import Supply, User


def make_issue_bundles(sess, issues):
    bundles = []
    for issue in issues:
        props = issue.properties
        supply_bundles = []
        if "owner_id" in props:
            owner = User.get_by_id(sess, props["owner_id"])
        else:
            owner = None
        bundle = {
            "issue": issue,
            "latest_entry": None if len(issue.entries) == 0 else issue.entries[-1],
            "supplies": supply_bundles,
            "owner": owner,
        }
        for supply in sess.scalars(
            select(Supply)
            .where(Supply.id.in_(props.get("supply_ids", [])))
            .order_by(Supply.id)
        ).all():
            era = supply.eras[0]
            site = era.get_physical_site(sess)
            supply_bundles.append(
                {"supply": supply, "era": supply.eras[0], "site": site}
            )
        bundles.append(bundle)
    return bundles
