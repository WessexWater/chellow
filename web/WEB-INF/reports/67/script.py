from net.sf.chellow.monad import Monad
from java.util import Properties
from java.io import StringReader
from net.sf.chellow.physical import Configuration
from net.sf.chellow.ui import Report
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'RateScript', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    contract_id = inv.getLong('dno_contract_id')
    contract = Contract.get_dno_by_id(sess, contract_id)
    rate_scripts = sess.query(RateScript).from_statement("select * from rate_script where rate_script.contract_id = :contract_id order by start_date desc").params(contract_id=contract_id).all()
    config = Configuration.getConfiguration()
    properties = Properties()
    properties.load(StringReader(config.getProperties()))

    reports = []
    for key in properties.propertyNames():
        if key.startswith('dno.report.'):
            dno_report_id = properties.get(key)
            if dno_report_id is not None:
                reports.append(Report.getReport(int(dno_report_id)))

    render(inv, template, {'contract': contract, 'rate_scripts': rate_scripts, 'reports': reports})
finally:
    if sess is not None:
        sess.close()