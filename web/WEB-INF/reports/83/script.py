from net.sf.chellow.monad import Monad
import db
import templater
import utils
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
RateScript = db.RateScript
render = templater.render
form_date, UserException = utils.form_date, utils.UserException
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        rate_script_id = inv.getLong('mop_rate_script_id')
        rate_script = RateScript.get_mop_by_id(sess, rate_script_id)
        render(inv, template, {'rate_script': rate_script})
    else:
        db.set_read_write(sess)
        rate_script_id = inv.getLong('mop_rate_script_id')
        rate_script = RateScript.get_mop_by_id(sess, rate_script_id)
        contract = rate_script.contract
        if inv.hasParameter('delete'):
            contract.delete_rate_script(sess, rate_script)
            sess.commit()
            inv.sendSeeOther(
                '/reports/107/output/?mop_contract_id=' + str(contract.id))
        else:
            try:
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
                    '/reports/205/output/?mop_rate_script_id=' +
                    str(rate_script.id))
            except UserException, e:
                render(
                    inv, template, {
                        'rate_script': rate_script, 'messages': [str(e)]}, 400)
finally:
    sess.close()
