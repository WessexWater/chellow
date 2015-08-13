from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'templater', 'db')
MeterType, Party = db.MeterType, db.Party
inv, template = globals()['inv'], globals()['template']
sess = None
try:
    sess = db.session()
    meter_type_id = inv.getLong('meter_type_id')
    meter_type = MeterType.get_by_id(sess, meter_type_id)
    templater.render(inv, template, {'meter_type': meter_type})
finally:
    if sess is not None:
        sess.close()
