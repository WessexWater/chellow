from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'templater', 'db')
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    config = db.Contract.get_non_core_by_name(sess, 'configuration')
    templater.render(inv, template, {'properties': config.make_properties()})
finally:
    if sess is not None:
        sess.close()
