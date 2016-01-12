import traceback
from net.sf.chellow.monad import Monad
import db
import utils
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
inv = globals()['inv']


def content():
    sess = None
    try:
        sess = db.session()
        yield "Supply Id, Note Index, Category, Is Important?, Body\n"

        for supply in sess.query(db.Supply).order_by(db.Supply.id):
            try:
                supply_note = eval(supply.note)
            except SyntaxError:
                continue
            for i, note in enumerate(supply_note['notes']):
                vals = [
                    supply.id, i, note['category'], note['is_important'],
                    note['body']]
                for i, val in enumerate(vals):
                    vals[i] = val.replace('"', '""')
                yield ','.join('"' + v + '"' for v in vals) + '\n'
    except:
        yield traceback.format_exc()
    finally:
        if sess is not None:
            sess.close()

utils.send_response(inv, content, file_name='notes.csv')
