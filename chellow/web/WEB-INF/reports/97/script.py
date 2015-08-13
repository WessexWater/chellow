from net.sf.chellow.monad import Monad
import templater
import db

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Tpr, ClockInterval = db.Tpr, db.ClockInterval
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    tpr_id = inv.getLong('tpr_id')
    tpr = Tpr.get_by_id(sess, tpr_id)
    clock_intervals = sess.query(ClockInterval).filter(
        ClockInterval.tpr_id == tpr.id).order_by(ClockInterval.id)
    render(inv, template, {'tpr': tpr, 'clock_intervals': clock_intervals})
finally:
    if sess is not None:
        sess.close()
