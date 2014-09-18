from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'RateScript', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    party_id = inv.getLong('party_id')
    party = Party.get_by_id(sess, party_id)
    render(inv, template, {'party': party})
finally:
    sess.close()