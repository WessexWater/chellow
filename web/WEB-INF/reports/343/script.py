from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
GeneratorType = db.GeneratorType
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    generator_type_id = inv.getLong('generator_type_id')
    generator_type = GeneratorType.get_by_id(sess, generator_type_id)
    render(inv, template, {'generator_type': generator_type})
finally:
    if sess is not None:
        sess.close()
