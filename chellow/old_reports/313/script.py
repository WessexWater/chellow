from net.sf.chellow.monad import Monad
import db
import utils
import templater

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Batch, BillType, Bill, Supply = db.Batch, db.BillType, db.Bill, db.Supply
render = templater.render
UserException, parse_mpan_core = utils.UserException, utils.parse_mpan_core
form_date, validate_hh_start = utils.form_date, utils.validate_hh_start
form_decimal = utils.form_decimal

inv, template = globals()['inv'], globals()['template']


def make_fields(sess, batch, message=None):
    bill_types = sess.query(BillType).order_by(BillType.code)
    bills = sess.query(Bill).filter(Bill.batch == batch).order_by(
        Bill.start_date)
    messages = [] if message is None else [str(e)]
    return {
        'batch': batch, 'bill_types': bill_types, 'messages': messages,
        'bills': bills}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        batch_id = inv.getLong('supplier_batch_id')
        batch = Batch.get_by_id(sess, batch_id)
        render(inv, template, make_fields(sess, batch))
    else:
        db.set_read_write(sess)
        batch_id = inv.getLong('supplier_batch_id')
        batch = Batch.get_by_id(sess, batch_id)
        mpan_core = inv.getString("mpan_core")
        mpan_core = parse_mpan_core(mpan_core)
        account = inv.getString("account")
        reference = inv.getString("reference")
        issue_date = form_date(inv, "issue")
        start_date = form_date(inv, "start")
        validate_hh_start(start_date)
        finish_date = form_date(inv, "finish")
        validate_hh_start(finish_date)
        kwh = form_decimal(inv, "kwh")
        net = form_decimal(inv, "net")
        vat = form_decimal(inv, "vat")
        gross = form_decimal(inv, "gross")
        bill_type_id = inv.getLong("bill_type_id")
        bill_type = BillType.get_by_id(sess, bill_type_id)
        breakdown_str = inv.getString("breakdown")

        breakdown = eval(breakdown_str)
        bill_type = BillType.get_by_id(sess, bill_type_id)
        bill = batch.insert_bill(
            sess, account, reference, issue_date, start_date, finish_date, kwh,
            net, vat, gross, bill_type, breakdown,
            Supply.get_by_mpan_core(sess, mpan_core))
        sess.commit()
        inv.sendSeeOther(
            "/reports/105/output/?supplier_bill_id=" + str(bill.id))

except UserException as e:
    sess.rollback()
    render(inv, template, make_fields(sess, batch, e), 400)
finally:
    if sess is not None:
        sess.close()
