from net.sf.chellow.monad import Monad
import utils
import templater
import db

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
RateScript = db.RateScript
NotFoundException, form_int = utils.NotFoundException, utils.form_int
form_str, form_date, form_str = utils.form_str, utils.form_date, utils.form_str
render = templater.render
inv, template = globals()['inv'], globals()['template']


def make_vals(rate_script, msg=None):
    messages = None if msg is None else [str(msg)]
    return {
        'rate_script': rate_script,
        'messages': messages}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        rate_script_id = form_int(inv, 'rate_script_id')
        rate_script = RateScript.get_non_core_by_id(sess, rate_script_id)
        render(inv, template, make_vals(rate_script))
    else:
        db.set_read_write(sess)
        rate_script_id = form_int(inv, 'rate_script_id')
        rate_script = RateScript.get_non_core_by_id(sess, rate_script_id)
        contract = rate_script.contract
        if inv.hasParameter('delete'):
            contract.delete_rate_script(sess, rate_script)
            sess.commit()
            inv.sendSeeOther(
                '/reports/267/output/?non_core_contract_id=' +
                str(contract.id))
        else:
            script = form_str(inv, 'script')
            start_date = form_date(inv, 'start')
            if inv.hasParameter('has_finished'):
                finish_date = form_date(inv, 'finish')
            else:
                finish_date = None
            contract.update_rate_script(
                sess, rate_script, start_date, finish_date, script)
            sess.commit()
            inv.sendSeeOther(
                '/reports/271/output/?rate_script_id=' + str(rate_script.id))
except utils.UserException as e:
    sess.rollback()
    render(inv, template, make_vals(rate_script, e))
except NotFoundException as e:
    inv.sendNotFound(str(e))
finally:
    if sess is not None:
        sess.close()
