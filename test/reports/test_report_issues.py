import csv
from io import StringIO

from utils import match, match_tables

from chellow.models import (
    Contract,
    MarketRole,
    Participant,
    User,
    UserRole,
)
from chellow.reports.report_issues import content
from chellow.utils import ct_datetime, to_utc


def test_do_get_as_csv(mocker, sess, client):
    mock_Thread = mocker.patch("chellow.reports.report_issues.threading.Thread")
    vf = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_C = MarketRole.insert(sess, "C", "DC")
    participant.insert_party(sess, market_role_C, "Fusion", vf, None, None)
    contract = Contract.insert_dc(sess, "Fusion DC", participant, "", {}, vf, None, {})
    contract.insert_issue(sess, vf, {})
    contract.insert_issue(sess, to_utc(ct_datetime(1997, 1, 1)), {})
    sess.commit()

    query_string = {"contract_id": contract.id, "as_csv": "true"}
    response = client.get("/reports/issues", query_string=query_string)
    match(response, 303)

    args = (1, [2], [], [])
    mock_Thread.assert_called_with(target=content, args=args)


def test_content(mocker, sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_C = MarketRole.insert(sess, "C", "DC")
    participant.insert_party(sess, market_role_C, "Fusion", vf, None, None)
    contract = Contract.insert_dc(sess, "Fusion DC", participant, "", {}, vf, None, {})
    contract.insert_issue(sess, vf, {})
    contract.insert_issue(sess, to_utc(ct_datetime(1997, 1, 1)), {})
    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    user_id = user.id
    contract_ids = [contract.id]
    sess.commit()

    f = StringIO()
    f.close = mocker.Mock()
    mocker.patch("chellow.reports.report_issues.open_file", return_value=f)
    user_ids = []
    supply_ids = []
    content(user_id, contract_ids, user_ids, supply_ids)
    f.seek(0)
    actual = list(csv.reader(f))
    expected = [
        [
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
        ],
        [
            "1",
            "C",
            "Fusion DC",
            "1996-01-01 00:00",
            "",
            "open",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ],
        [
            "2",
            "C",
            "Fusion DC",
            "1997-01-01 00:00",
            "",
            "open",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ],
    ]
    match_tables(expected, actual)
