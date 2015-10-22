from net.sf.chellow.monad import Monad
import db
import system_price_elexon
import templater
import utils
Monad.getUtils()['impt'](
    globals(), 'utils', 'templater', 'db', 'system_price_elexon')
Contract = db.Contract
render = templater.render
inv, template = globals()['inv'], globals()['template']

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
except utils.UserException as e:
    sess.rollback()
    render(
        inv, template, {
            'messages': [str(e)], 'importer': importer, 'contract': contract})
finally:
    if sess is not None:
        sess.close()
