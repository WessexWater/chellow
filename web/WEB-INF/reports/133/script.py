from net.sf.chellow.monad import Monad
import db
import templater

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
MeterPaymentType = db.MeterPaymentType
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    meter_payment_types = sess.query(MeterPaymentType).order_by(
        MeterPaymentType.code).all()
    render(inv, template, {'meter_payment_types': meter_payment_types})
finally:
    if sess is not None:
        sess.close()
