from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'GeneratorType', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    generator_types = sess.query(GeneratorType).order_by(GeneratorType.code)
    render(inv, template, {'generator_types': generator_types})
finally:
    sess.close()