from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'templater', 'db')
MeterType, Party = db.MeterType, db.Party
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    meter_types = sess.query(MeterType).order_by(MeterType.code)
    templater.render(inv, template, {'meter_types': meter_types})
finally:
    if sess is not None:
        sess.close()
