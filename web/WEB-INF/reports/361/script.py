from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
from datetime import datetime
import pytz

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'Participant', 'set_read_write', 'session', 'MarketRole'], 
        'utils': ['UserException', 'form_date'],
        'templater': ['render']})

def make_fields(sess, message=None):
    initial_date = datetime.utcnow().replace(tzinfo=pytz.utc)
    initial_date = datetime(initial_date.year, initial_date.month, 1)
    parties = sess.query(Party).join(MarketRole).join(Participant).filter(MarketRole.code=='C').order_by(Participant.code).all()
    return {'initial_date': initial_date, 'parties': parties, 'messages': None if message is None else [str(message)]}

sess = None
try:
    sess = session()
    if inv.getRequest().getMethod() == 'GET':
        render(inv, template, make_fields(sess))
    else:
        set_read_write(sess)
        participant_id = inv.getLong('participant_id')
        name = inv.getString('name')
        start_date = form_date(inv, 'start')
        participant = Participant.get_by_id(sess, participant_id)
        contract = Contract.insert_mop(sess, name, participant, '{}', '{}',
            start_date, None, '{}')
        sess.commit()
        inv.sendSeeOther('/reports/107/output/?mop_contract_id=' +
            str(contract.id))
except UserException, e:
    render(inv, template, make_fields(sess, e))
finally:
    sess.close()