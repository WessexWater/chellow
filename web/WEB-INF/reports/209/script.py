from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'templater', 'db')
inv, template = globals()['inv'], globals()['templater']

sess = None
try:
    sess = db.session()
    templater.render(inv, template, {})
finally:
    if sess is not None:
        sess.close()
