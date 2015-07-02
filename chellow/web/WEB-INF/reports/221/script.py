from net.sf.chellow.monad import Monad
import db
import templater
import utils
import bank_holidays
Monad.getUtils()['impt'](
    globals(), 'db', 'utils', 'templater', 'bank_holidays')
Contract = db.Contract
render = templater.render
UserException = utils.UserException
inv, template = globals()['inv'], globals()['template']

sess = None
importer = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == "GET":
        importer = bank_holidays.get_importer()
        contract = Contract.get_non_core_by_name(sess, 'bank_holidays')
        render(inv, template, {'importer': importer, 'contract': contract})
    else:
        importer = bank_holidays.get_importer()
        contract = Contract.get_non_core_by_name(sess, 'bank_holidays')
        importer.go()
        inv.sendSeeOther("/reports/221/output/")
except UserException, e:
    sess.rollback()
    render(
        inv, template, {
            'messages': [str(e)], 'importer': importer, 'contract': contract})
finally:
    if sess is not None:
        sess.close()
