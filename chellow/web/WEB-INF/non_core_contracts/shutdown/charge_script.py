from net.sf.chellow.monad import Monad
import time
import traceback
import utils
import db
import hh_importer
import bsuos
import system_price
import bank_holidays
import rcrc
import tlms
Monad.getUtils()['impt'](
    globals(), 'utils', 'hh_importer', 'bsuos', 'rcrc', 'tlms', 'db',
    'system_price', 'bank_holidays')

UserException = utils.UserException


def on_shut_down(ctx):
    messages = []
    sess = None
    try:
        sess = db.session()
        for md in (
                hh_importer, bsuos, system_price, rcrc, tlms, bank_holidays):
            try:
                md.shutdown()
            except UserException, e:
                time.sleep(2)
                try:
                    md.shutdown()
                except UserException, e:
                    messages.append(str(e))
            except:
                messages.append(
                    "Problem with module " + str(md.db_id) +
                    traceback.format_exc())
        if len(messages) > 0:
            raise UserException(' '.join(messages))
    finally:
        if sess is not None:
            sess.close()
        try:
            db.engine.dispose()
        except TypeError:
            pass
