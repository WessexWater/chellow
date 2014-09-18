from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')

sess = None
try:
    sess = db.session()    
    inv.getResponse().setContentType('text/csv')
    inv.getResponse().addHeader('Content-Disposition', 'attachment; filename="notes.csv"')
    pw = inv.getResponse().getWriter()
    pw.println("Supply Id, Note Index, Category, Is Important?, Body")
    pw.flush()

    for supply in sess.query(db.Supply).order_by(db.Supply.id):
        try:
            supply_note = eval(supply.note)
        except SyntaxError:
            continue
        for i, note in enumerate(supply_note['notes']):
            vals = [supply.id, i, note['category'], note['is_important'], note['body']]
            vals = map(unicode, vals)
            for i, val in enumerate(vals):
                vals[i] = val.replace('"', '""')
            pw.println(','.join('"' + v + '"' for v in vals))
            pw.flush()
    pw.close()
finally:
    if sess is not None:
        sess.close()