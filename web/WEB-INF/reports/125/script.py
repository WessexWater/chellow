from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Ssc, MeasurementRequirements = db.Ssc, db.MeasurementRequirements
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    sscs = sess.query(Ssc).options(
        joinedload_all(MeasurementRequirements.tpr)).order_by(Ssc.code).all()
    render(inv, template, {'sscs': sscs})
finally:
    if sess is not None:
        sess.close()
