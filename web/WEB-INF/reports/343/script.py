from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'GeneratorType', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    generator_type_id = inv.getLong('generator_type_id')
    generator_type = GeneratorType.get_by_id(sess, generator_type_id)
    render(inv, template, {'generator_type': generator_type})
finally:
    sess.close()