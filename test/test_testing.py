from collections import deque

import chellow.testing
from chellow.models import MarketRole, Participant
from chellow.utils import ct_datetime, to_utc


def test_run_supplier_contract(sess):
    from_date = to_utc(ct_datetime(2000, 1, 1))
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    supplier_party = participant.insert_party(
        sess, market_role_X, "Fusion Ltc", from_date, None, None
    )
    contract = supplier_party.insert_contract(
        sess,
        "Fusion Supplier 2000",
        "a = db_id",
        {},
        from_date,
        None,
        {},
    )
    sess.commit()
    messages = deque()
    chellow.testing.test_contract(messages, sess, contract)
