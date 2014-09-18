from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'MeterPaymentType', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    meter_payment_types = sess.query(MeterPaymentType).from_statement("""select * from meter_payment_type order by code""").all()
    render(inv, template, {'meter_payment_types': meter_payment_types})
finally:
    sess.close()