from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'RateScript', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    rate_script_id = inv.getLong('dno_rate_script_id')
    rate_script = RateScript.get_dno_by_id(sess, rate_script_id)
    render(inv, template, {'rate_script': rate_script})
finally:
    sess.close()