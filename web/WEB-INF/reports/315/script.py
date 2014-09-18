from net.sf.chellow.monad import Monad

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'session', 'Party', 'Participant', 'set_read_write', 'MarketRole'],
        'utils': ['UserException', 'prev_hh', 'next_hh', 'hh_after', 'hh_before', 'HH', 'form_date', 'validate_hh_start'],
        'templater': ['render']})


def make_fields(sess, message=None):
    contracts = sess.query(Contract).join(MarketRole).filter(MarketRole.code == 'X').order_by(Contract.name)
    parties = sess.query(Party).join(MarketRole, Participant).filter(MarketRole.code == 'X').order_by(Participant.code)
    messages = [] if message is None else [str(e)]
    return {'contracts': contracts, 'messages': messages, 'parties': parties}

sess = None
try:
    sess = session()
    if inv.getRequest().getMethod() == 'GET':
        render(inv, template, make_fields(sess))
    else:
        set_read_write(sess)
        participant_id = inv.getLong("participant_id")
        participant = Participant.get_by_id(sess, participant_id)
        name = inv.getString("name")
        start_date = form_date(inv, "start")
        validate_hh_start(start_date)
        contract = Contract.insert_supplier(sess, name, participant, '', '{}', start_date, None, '{}')
        sess.commit()
        inv.sendSeeOther("/reports/77/output/?supplier_contract_id=" + str(contract.id))
except UserException, e:
    sess.rollback()
    render(inv, template, make_fields(sess, e), 400)
finally:
    if sess is not None:
        sess.close()