from net.sf.chellow.monad import Monad
import templater
import db
import utils
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
render = templater.render
RateScript = db.RateScript
UserException, form_date = utils.UserException, utils.form_date
inv, template = globals()['inv'], globals()['template']
sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        rate_script_id = inv.getLong('dno_rate_script_id')
        rate_script = RateScript.get_dno_by_id(sess, rate_script_id)
        render(inv, template, {'rate_script': rate_script})
    else:
        db.set_read_write(sess)
        rate_script_id = inv.getLong('dno_rate_script_id')
        rate_script = RateScript.get_dno_by_id(sess, rate_script_id)
        contract = rate_script.contract
        if inv.hasParameter('delete'):
            contract.delete_rate_script(sess, rate_script)
            sess.commit()
            inv.sendSeeOther(
                '/reports/67/output/?dno_contract_id=' + str(contract.id))
        else:
            script = inv.getString('script')
            start_date = form_date(inv, 'start')
            if inv.hasParameter('has_finished'):
                finish_date = form_date(inv, 'finish')
            else:
                finish_date = None
            contract.update_rate_script(
                sess, rate_script, start_date, finish_date, script)
            sess.commit()
            inv.sendSeeOther(
                '/reports/69/output/?dno_rate_script_id=' +
                str(rate_script.id))
except UserException as e:
    render(
        inv, template, {'rate_script': rate_script, 'messages': [str(e)]}, 400)
finally:
    if sess is not None:
        sess.close()
