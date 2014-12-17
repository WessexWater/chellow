from net.sf.chellow.monad import Monad

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
import db
import templater
MeterPaymentType = db.MeterPaymentType
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    meter_payment_type_id = inv.getLong('meter_payment_type_id')
    meter_payment_type = MeterPaymentType.get_by_id(
        sess, meter_payment_type_id)
    render(inv, template, {'meter_payment_type': meter_payment_type})
finally:
    if sess is not None:
        sess.close()
