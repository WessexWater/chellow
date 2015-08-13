from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
render = templater.render
Source = db.Source
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    sources = sess.query(Source).order_by(Source.code).all()
    render(inv, template, {'sources': sources})
finally:
    if sess is not None:
        sess.close()
