from net.sf.chellow.monad import Monad
import db
import utils
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Contract, MarketRole, Participant = db.Contract, db.MarketRole, db.Participant
Party = db.Party
UserException, form_date = utils.UserException, utils.form_date
validate_hh_start = utils.validate_hh_start
inv, template = globals()['inv'], globals()['template']


def make_fields(sess, message=None):
    contracts = sess.query(Contract).join(MarketRole).filter(
        MarketRole.code == 'X').order_by(Contract.name)
    parties = sess.query(Party).join(MarketRole, Participant).filter(
        MarketRole.code == 'X').order_by(Participant.code)
    messages = [] if message is None else [str(e)]
    return {'contracts': contracts, 'messages': messages, 'parties': parties}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        templater.render(inv, template, make_fields(sess))
    else:
        db.set_read_write(sess)
        participant_id = inv.getLong("participant_id")
        participant = Participant.get_by_id(sess, participant_id)
        name = inv.getString("name")
        start_date = form_date(inv, "start")
        validate_hh_start(start_date)
        charge_script = inv.getString("charge_script")
        properties = inv.getString("properties")

        contract = Contract.insert_supplier(
            sess, name, participant, charge_script, properties, start_date,
            None, '{}')
        sess.commit()
        inv.sendSeeOther(
            "/reports/77/output/?supplier_contract_id=" + str(contract.id))
except UserException as e:
    sess.rollback()
    templater.render(inv, template, make_fields(sess, e), 400)
finally:
    if sess is not None:
        sess.close()
