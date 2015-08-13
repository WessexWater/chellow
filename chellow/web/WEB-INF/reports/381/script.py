from net.sf.chellow.monad import Monad
import db
import templater
import utils
import system_price_unified
Monad.getUtils()['impt'](
    globals(), 'db', 'utils', 'templater', 'system_price_unified')
Contract = db.Contract
render = templater.render
UserException = utils.UserException
inv, template = globals()['inv'], globals()['template']

sess = None
importer = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == "GET":
        importer = system_price_unified.get_importer()
        contract = Contract.get_non_core_by_name(sess, 'system_price_unified')
        render(inv, template, {'importer': importer, 'contract': contract})
    else:
        importer = system_price_unified.get_importer()
        contract = Contract.get_non_core_by_name(sess, 'system_price_unified')
        importer.go()
        inv.sendSeeOther("/reports/381/output/")
except UserException, e:
    sess.rollback()
    render(
        inv, template, {
            'messages': [str(e)], 'importer': importer, 'contract': contract})
finally:
    if sess is not None:
        sess.close()
