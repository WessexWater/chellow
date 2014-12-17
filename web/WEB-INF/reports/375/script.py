from net.sf.chellow.monad import Monad
import db
import utils
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    utils.clog("hello")
    templater.render(inv, template, {'clogs': utils.clogs})
finally:
    if sess is not None:
        sess.close()
