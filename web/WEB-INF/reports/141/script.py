from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'templater', 'db')
ReadType = db.ReadType
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    read_types = sess.query(ReadType).order_by(ReadType.code).all()
    templater.render(inv, template, {'read_types': read_types})
finally:
    if sess is not None:
        sess.close()
