from net.sf.chellow.monad import Monad
from java.util import Properties
from java.io import StringReader
from net.sf.chellow.physical import Configuration
from net.sf.chellow.ui import Report
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Contract, RateScript = db.Contract, db.RateScript
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    contract_id = inv.getLong('dno_contract_id')
    contract = Contract.get_dno_by_id(sess, contract_id)
    rate_scripts = sess.query(RateScript).filter(
        RateScript.contract == contract).order_by(
        RateScript.start_date.desc()).all()
    config = Configuration.getConfiguration()
    properties = Properties()
    properties.load(StringReader(config.getProperties()))

    reports = []
    for key in properties.propertyNames():
        if key.startswith('dno.report.'):
            dno_report_id = properties.get(key)
            if dno_report_id is not None:
                reports.append(Report.getReport(int(dno_report_id)))

    render(
        inv, template, {
            'contract': contract, 'rate_scripts': rate_scripts,
            'reports': reports})
finally:
    if sess is not None:
        sess.close()
