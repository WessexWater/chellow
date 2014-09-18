from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
from datetime import datetime
import pytz

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Batch', 'Participant', 'set_read_write', 'session', 'Bill', 'Report'], 
        'utils': ['UserException', 'form_date'],
        'templater': ['render']})


sess = None
try:
    sess = session()
    if inv.getRequest().getMethod() == 'GET':
        batch_id = inv.getLong('mop_batch_id')
        batch = Batch.get_by_id(sess, batch_id)
        bills = sess.query(Bill).filter(Bill.batch_id==batch.id).order_by(Bill.reference).all()

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
    sess.close()