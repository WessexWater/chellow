from net.sf.chellow.monad import Monad
from java.lang import System
from sqlalchemy.orm import joinedload_all
import sys

Monad.getContext().getAttribute("net.sf.chellow.utils")['imprt'](globals(), {
        'db': ['Contract', 'Party', 'RateScript', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render'],
        'rcrc': ['get_rcrc_importer']})


sess = None
importer = None
try:
    sess = session()
    if inv.getRequest().getMethod() == "GET":
        importer = get_rcrc_importer()
        contract = Contract.get_non_core_by_name(sess, 'rcrc')
        render(inv, template, {'importer': importer, 'contract': contract})
    else:
        importer = get_rcrc_importer()
        contract = Contract.get_non_core_by_name(sess, 'rcrc')
        importer.go()
        inv.sendSeeOther("/reports/225/output/")
except UserException, e:
    sess.rollback()
    render(inv, template, {'messages': [str(e)], 'importer': importer,
        'contract': contract})
finally:
    sess.close()