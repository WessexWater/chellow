from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
render = templater.render
GeneratorType = db.GeneratorType
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    generator_types = sess.query(GeneratorType).order_by(GeneratorType.code)
    render(inv, template, {'generator_types': generator_types})
finally:
    if sess is not None:
        sess.close()
