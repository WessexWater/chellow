from sqlalchemy.sql.expression import text
from datetime import datetime
import pytz
from net.sf.chellow.monad import Monad

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Batch = db.Batch
UserException = utils.UserException
render = templater.render

def make_fields(sess, batch, message=None):
    messages = [] if message is None else [str(message)]
    return {'batch': batch, 'messages': messages}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        batch_id = inv.getLong('hhdc_batch_id')
        batch = Batch.get_by_id(sess, batch_id)
        render(inv, template, make_fields(sess, batch))
    else:
        db.set_read_write(sess)
        batch_id = inv.getLong('hhdc_batch_id')
        batch = Batch.get_by_id(sess, batch_id)
        if inv.hasParameter('update'):
            reference = inv.getString('reference')
            description = inv.getString('description')
            batch.update(sess, reference, description)
            sess.commit()
            inv.sendSeeOther("/reports/203/output/?hhdc_batch_id=" +
                    str(batch.id))
        elif inv.hasParameter("delete"):
            contract = batch.contract
            batch.delete(sess)
            sess.commit()
            inv.sendSeeOther(
                "/reports/93/output/?hhdc_contract_id=" + str(contract.id))
except UserException, e:
    render(inv, template, make_fields(sess, batch, e))
finally:
    sess.close()
