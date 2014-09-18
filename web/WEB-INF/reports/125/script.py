from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'Ssc', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    sscs = sess.query(Ssc).options(joinedload_all('measurement_requirements.tpr')).order_by(Ssc.code).all()
    render(inv, template, {'sscs': sscs})
finally:
    sess.close()