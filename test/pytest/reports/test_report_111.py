import chellow.reports.report_111
from chellow.models import Contract, MarketRole, Participant
from chellow.utils import utc_datetime

from utils import match


# End to end tests


def test_ete_error_message_for_invalid_bill_id(client, sess):
    data = {
        "bill_id": "0",
    }
    response = client.get("/reports/111", data=data)

    match(response, 404)


# HTTP level tests


def test_http_supplier_batch_with_mpan_cores(mocker, client, sess):
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    participant = Participant.insert(sess, "hhak", "AK Industries")
    participant.insert_party(
        sess, market_role_X, "Fusion Ltc", utc_datetime(2000, 1, 1), None, None
    )
    supplier_contract = Contract.insert_supplier(
        sess,
        "Fusion Supplier 2000",
        participant,
        "",
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    batch = supplier_contract.insert_batch(sess, "005", "batch 5")
    sess.commit()
    MockThread = mocker.patch("chellow.reports.report_111.threading.Thread")

    data = {
        "batch_id": str(batch.id),
        "mpan_cores": "22 1065 3921 534",
    }
    response = client.get("/reports/111", data=data)

    match(response, 303)

    expected_args = (
        batch.id,
        None,
        None,
        None,
        None,
        None,
        ["22 1065 3921 534"],
        "_batch_005",
    )

    MockThread.assert_called_with(
        target=chellow.reports.report_111.content, args=expected_args
    )


# Worker level tests
