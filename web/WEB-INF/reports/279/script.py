from net.sf.chellow.monad import Monad
from sqlalchemy.sql.expression import text
from datetime import datetime
import pytz

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Party, MarketRole, Participant = db.Party, db.MarketRole, db.Participant
Contract = db.Contract
render = templater.render
UserException, form_date = utils.UserException, utils.form_date

def make_fields(sess, contract, message=None):
    parties = sess.query(Party).join(MarketRole).join(Participant).filter(
        MarketRole.code == 'C').order_by(Participant.code).all()
    initial_date = datetime.now(pytz.utc)
    messages = [] if message is None else [str(message)]
    return {
        'contract': contract, 'parties': parties,
        'initial_date': datetime(
            initial_date.year, initial_date.month, initial_date.day),
        'messages': messages}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        contract_id = inv.getLong('hhdc_contract_id')
        contract = Contract.get_hhdc_by_id(sess, contract_id)
        render(inv, template, make_fields(sess, contract))
    else:
        db.set_read_write(sess)
        contract_id = inv.getLong('hhdc_contract_id')
        contract = Contract.get_hhdc_by_id(sess, contract_id)
        if inv.hasParameter("update_state"):
            state = inv.getString("state")
            contract.state = state
            sess.commit()
            inv.sendSeeOther("/reports/115/output/?hhdc_contract_id=" +
                    str(contract.id))
        elif inv.hasParameter("ignore_snags"):
            ignore_date = form_date(inv, "ignore")
            sess.execute(text("""update snag set is_ignored = true from channel, era where snag.channel_id = channel.id and channel.era_id = era.id and era.hhdc_contract_id = :contract_id and snag.finish_date < :ignore_date"""), params=dict(contract_id=contract.id, ignore_date=ignore_date))
            sess.commit()
            inv.sendSeeOther("/reports/115/output/?hhdc_contract_id=" +
                    str(contract.id))
        elif inv.hasParameter("delete"):
            contract.delete(sess)
            sess.commit()
            inv.sendSeeOther("/reports/113/output/");
        else:
            party_id = inv.getLong("party_id")
            name = inv.getString("name")
            charge_script = inv.getString("charge_script")
            properties = inv.getString("properties")
            party = Party.get_by_id(sess, party_id)
            contract.update(sess, False, name, party, charge_script,
                    properties)
            sess.commit()
            inv.sendSeeOther("/reports/115/output/?hhdc_contract_id=" +
                    str(contract.id))
except UserException, e:
    render(inv, template, make_fields(sess, contract, e))
finally:
    if sess is not None:
        sess.close()
