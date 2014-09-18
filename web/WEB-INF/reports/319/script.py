from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'RateScript', 'set_read_write', 'session'], 
        'utils': ['UserException', 'NotFoundException', 'form_date'],
        'templater': ['render']})


sess = None
try:
    sess = session()
    if inv.getRequest().getMethod() == 'GET':
        rate_script_id = inv.getLong('supplier_rate_script_id')
        rate_script = RateScript.get_supplier_by_id(sess, rate_script_id)
        render(inv, template, {'rate_script': rate_script})
    else:
        set_read_write(sess)
        rate_script_id = inv.getLong('supplier_rate_script_id')
        rate_script = RateScript.get_supplier_by_id(sess, rate_script_id)
        contract = rate_script.contract
        if inv.hasParameter('delete'):
            contract.delete_rate_script(sess, rate_script)
            sess.commit()
            inv.sendSeeOther('/reports/77/output/?supplier_contract_id='
                + str(contract.id))
        else:
            script = inv.getString('script')
            start_date = form_date(inv, 'start')
            has_finished = inv.getBoolean('has_finished')
            finish_date = form_date(inv, 'finish') if has_finished else None
            contract.update_rate_script(sess, rate_script, start_date, finish_date, script)
            sess.commit()
            inv.sendSeeOther('/reports/79/output/?supplier_rate_script_id='
                    + str(rate_script.id))
except NotFoundException, e:
    inv.sendNotFound(str(e))
finally:
    sess.close()