from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
from datetime import datetime
import pytz

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
render = templater.render
UserException = utils.UserException
MarketRole, Participant = db.MarketRole, db.Participant

def make_fields(sess, message=None):
    initial_date = datetime.utcnow().replace(tzinfo=pytz.utc)
    initial_date = datetime(initial_date.year, initial_date.month, 1)
    parties = sess.query(db.Party).join(MarketRole).join(Participant).filter(
        MarketRole.code == 'C').order_by(Participant.code).all()
    return {
        'initial_date': initial_date, 'parties': parties,
        'messages': None if message is None else [str(message)]}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        render(inv, template, make_fields(sess))
    else:
        db.set_read_write(sess)
        participant_id = inv.getLong('participant_id')
        name = inv.getString('name')
        start_date = utils.form_date(inv, 'start')
        participant = db.Participant.get_by_id(sess, participant_id)
        contract = db.Contract.insert_hhdc(
            sess, name, participant, '{}', '{}', start_date, None, '{}')
        sess.commit()
        inv.sendSeeOther('/reports/115/output/?hhdc_contract_id=' +
            str(contract.id))
except UserException, e:
    render(inv, template, make_fields(sess, e))
finally:
    if sess is not None:
        sess.close()
