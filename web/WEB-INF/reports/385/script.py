from net.sf.chellow.monad import Monad
from java.lang import Thread
from sqlalchemy.orm import joinedload_all
import sys

Monad.getUtils()['impt'](globals(), 'utils', 'templater', 'db', 'system_price_elexon')

Contract = db.Contract
render = templater.render

sess = None
importer = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == "GET":
        importer = system_price_elexon.get_importer()
        contract = Contract.get_non_core_by_name(sess, 'system_price_elexon')
        render(inv, template, {'importer': importer, 'contract': contract})
    else:
        importer = system_price_elexon.get_importer()
        contract = Contract.get_non_core_by_name(sess, 'system_price_elexon')
        importer.go()
        inv.sendSeeOther("/reports/385/output/")
except utils.UserException, e:
    sess.rollback()
    render(inv, template, {'messages': [str(e)], 'importer': importer,
        'contract': contract})
finally:
    if sess is not None:
        sess.close()