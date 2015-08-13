from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'templater', 'db')
ReadType = db.ReadType
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    read_type_id = inv.getLong('read_type_id')
    read_type = ReadType.get_by_id(sess, read_type_id)
    templater.render(inv, template, {'read_type': read_type})
finally:
    if sess is not None:
        sess.close()
