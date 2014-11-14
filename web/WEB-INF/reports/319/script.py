from net.sf.chellow.monad import Monad

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
RateScript = db.RateScript
form_date, NotFoundException = utils.form_date, utils.NotFoundException

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        rate_script_id = inv.getLong('supplier_rate_script_id')
        rate_script = RateScript.get_supplier_by_id(sess, rate_script_id)
        render(inv, template, {'rate_script': rate_script})
    else:
        db.set_read_write(sess)
        rate_script_id = inv.getLong('supplier_rate_script_id')
        rate_script = RateScript.get_supplier_by_id(sess, rate_script_id)
        contract = rate_script.contract
        if inv.hasParameter('delete'):
            contract.delete_rate_script(sess, rate_script)
            sess.commit()
            inv.sendSeeOther(
                '/reports/77/output/?supplier_contract_id=' + str(contract.id))
        else:
            script = inv.getString('script')
            start_date = form_date(inv, 'start')
            has_finished = inv.getBoolean('has_finished')
            finish_date = form_date(inv, 'finish') if has_finished else None
            contract.update_rate_script(
                sess, rate_script, start_date, finish_date, script)
            sess.commit()
            inv.sendSeeOther(
                '/reports/79/output/?supplier_rate_script_id=' +
                str(rate_script.id))
except NotFoundException, e:
    inv.sendNotFound(str(e))
finally:
    if sess is not None:
        sess.close()
