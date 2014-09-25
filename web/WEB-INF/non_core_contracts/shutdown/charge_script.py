from java.lang import System
from net.sf.chellow.monad import Monad
import time

Monad.getUtils()['impt'](globals(), 'utils', 'pre_db', 'hh_importer', 'bsuos', 'rcrc', 'tlms', 'db', 'system_price_bmreports', 'system_price_elexon')

UserException = utils.UserException

def on_shut_down(ctx):
    messages = []
    sess = None
    try:
        sess = db.session()
        for func in (hh_importer.shutdown, bsuos.shutdown, system_price_bmreports.shutdown, system_price_elexon.shutdown, rcrc.shutdown, tlms.shutdown):
            try:
                func()
            except UserException, e:
                time.sleep(2)
                try:
                    func()
                except UserException, e:
                    messages.append(str(e))
        if len(messages) > 0:
            raise UserException(' '.join(messages))
    finally:
        if sess is not None:
            sess.close()
        try:
            pre_db.engine.dispose()
        except TypeError:
            pass
