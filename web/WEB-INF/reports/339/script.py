from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'Source', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    source_id = inv.getLong('source_id')
    source = Source.get_by_id(sess, source_id)
    render(inv, template, {'source': source})
finally:
    sess.close()