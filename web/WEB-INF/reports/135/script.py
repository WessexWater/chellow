from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['MeterPaymentType', 'Ssc', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    meter_payment_type_id = inv.getLong('meter_payment_type_id')
    meter_payment_type = MeterPaymentType.get_by_id(sess, meter_payment_type_id)
    render(inv, template, {'meter_payment_type': meter_payment_type})
finally:
    sess.close()