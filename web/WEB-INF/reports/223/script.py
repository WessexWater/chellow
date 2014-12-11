from net.sf.chellow.monad import Monad
import db
import tlms
import templater
import utils
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater', 'tlms')
Contract = db.Contract
render = templater.render
UserException = utils.UserException
inv, template = globals()['inv'], globals()['template']

sess = None
importer = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == "GET":
        importer = tlms.get_tlm_importer()
        contract = Contract.get_non_core_by_name(sess, 'tlms')
        render(inv, template, {'importer': importer, 'contract': contract})
    else:
        importer = tlms.get_tlm_importer()
        contract = Contract.get_non_core_by_name(sess, 'tlms')
        importer.go()
        inv.sendSeeOther("/reports/223/output/")
except UserException, e:
    sess.rollback()
    render(
        inv, template, {
            'messages': [str(e)], 'importer': importer, 'contract': contract})
finally:
    if sess is not None:
        sess.close()
