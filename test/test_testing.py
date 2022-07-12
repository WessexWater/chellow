from chellow.models import Contract, MarketRole, Participant
from chellow.testing import _test_contract
from chellow.utils import ct_datetime, to_utc


def test_run_supplier_contract(sess):
    from_date = to_utc(ct_datetime(2000, 1, 1))
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_X, "Fusion Ltc", from_date, None, None)
    contract = Contract.insert_supplier(
        sess,
        "Fusion Supplier 2000",
        participant,
        "a = db_id",
        {},
        from_date,
        None,
        {},
    )
    sess.commit()
    log = []
    logger = log.append
    _test_contract(logger, sess, contract)
