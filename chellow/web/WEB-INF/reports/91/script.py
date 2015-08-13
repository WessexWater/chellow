from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Batch, Bill, Contract, Report = db.Batch, db.Bill, db.Contract, db.Report
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        batch_id = inv.getLong('supplier_batch_id')
        if batch_id is None:
            batch_id = inv.getLong('batch-id')
        batch = Batch.get_by_id(sess, batch_id)
        bills = sess.query(Bill).filter(Bill.batch == batch).order_by(
            Bill.reference, Bill.start_date).all()
        config_contract = Contract.get_non_core_by_name(sess, 'configuration')
        properties = config_contract.make_properties()
        fields = {'batch': batch, 'bills': bills}
        if 'batch_reports' in properties:
            batch_reports = []
            for report_id in properties['batch_reports']:
                batch_reports.append(Report.get_by_id(sess, report_id))
            fields['batch_reports'] = batch_reports
        render(inv, template, fields)
finally:
    if sess is not None:
        sess.close()
