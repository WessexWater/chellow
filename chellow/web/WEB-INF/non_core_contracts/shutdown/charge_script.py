from net.sf.chellow.monad import Monad
import time
import traceback
import utils
import db
import hh_importer
import bsuos
import system_price_bmreports
import system_price_elexon
import system_price_unified
import rcrc
import tlms
Monad.getUtils()['impt'](
    globals(), 'utils', 'hh_importer', 'bsuos', 'rcrc', 'tlms', 'db',
    'system_price_bmreports', 'system_price_elexon', 'system_price_unified')

UserException = utils.UserException


def on_shut_down(ctx):
    messages = []
    sess = None
    try:
        sess = db.session()
        for md in (
                hh_importer, bsuos, system_price_bmreports,
                system_price_elexon, rcrc, tlms, system_price_unified):
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
