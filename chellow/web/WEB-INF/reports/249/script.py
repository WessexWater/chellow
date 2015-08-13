from net.sf.chellow.monad import Monad
import db
import utils
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
RateScript = db.RateScript
form_date, UserException = utils.form_date, utils.UserException
NotFoundException = utils.NotFoundException
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        rate_script_id = inv.getLong('hhdc_rate_script_id')
        rate_script = RateScript.get_hhdc_by_id(sess, rate_script_id)
        templater.render(inv, template, {'rate_script': rate_script})
    else:
        db.set_read_write(sess)
        rate_script_id = inv.getLong('hhdc_rate_script_id')
        rate_script = RateScript.get_hhdc_by_id(sess, rate_script_id)
        contract = rate_script.contract
        if inv.hasParameter('delete'):
            contract.delete_rate_script(sess, rate_script)
            sess.commit()
            inv.sendSeeOther(
                '/reports/115/output/?hhdc_contract_id=' + str(contract.id))
        else:
            script = inv.getString('script')
            start_date = form_date(inv, 'start')
            has_finished = inv.getBoolean('has_finished')
            finish_date = form_date(inv, 'finish') if has_finished else None
            contract.update_rate_script(
                sess, rate_script, start_date, finish_date, script)
            sess.commit()
            inv.sendSeeOther(
                '/reports/173/output/?hhdc_rate_script_id=' +
                str(rate_script.id))
except NotFoundException, e:
    inv.sendNotFound(str(e))
finally:
    if sess is not None:
        sess.close()
