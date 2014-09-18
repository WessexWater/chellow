from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'RateScript', 'set_read_write', 'session'], 
        'utils': ['UserException', 'form_date'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    if inv.getRequest().getMethod() == 'GET':
        rate_script_id = inv.getLong('dno_rate_script_id')
        rate_script = RateScript.get_dno_by_id(sess, rate_script_id)
        render(inv, template, {'rate_script': rate_script})
    else:
        set_read_write(sess)
        rate_script_id = inv.getLong('dno_rate_script_id')
        rate_script = RateScript.get_dno_by_id(sess, rate_script_id)
        contract = rate_script.contract
        if inv.hasParameter('delete'):
            contract.delete_rate_script(sess, rate_script)
            sess.commit()
            inv.sendSeeOther('/reports/67/output/?dno_contract_id='
                + str(contract.id))
        else:
            try:
                script = inv.getString('script')
                start_date = form_date(inv, 'start')
                if inv.hasParameter('has_finished'):
                    finish_date = form_date(inv, 'finish')
                else:
                    finish_date = None
                contract.update_rate_script(sess, rate_script, start_date, finish_date, script)
                sess.commit()
                inv.sendSeeOther('/reports/69/output/?dno_rate_script_id='
                        + str(rate_script.id))
            except UserException, e:
                render(inv, template, {'rate_script': rate_script, 'messages': [str(e)]}, 400)          
finally:
    sess.close()