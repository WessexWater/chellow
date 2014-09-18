from net.sf.chellow.monad import Monad

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'session', 'Batch', 'Supply', 'BillType', 'Bill', 'set_read_write'],
        'utils': ['UserException', 'prev_hh', 'next_hh', 'hh_after', 'hh_before', 'HH', 'parse_mpan_core', 'form_date', 'form_decimal', 'validate_hh_start'],
        'templater': ['render']})


def make_fields(sess, batch, message=None):
    bill_types = sess.query(BillType).order_by(BillType.code)
    bills = sess.query(Bill).filter(Bill.batch == batch).order_by(Bill.start_date)
    messages = [] if message is None else [str(e)]
    return {'batch': batch, 'bill_types': bill_types, 'messages': messages, 'bills': bills}

sess = None
try:
    sess = session()
    if inv.getRequest().getMethod() == 'GET':
        batch_id = inv.getLong('mop_batch_id')
        batch = Batch.get_by_id(sess, batch_id)
        render(inv, template, make_fields(sess, batch))
    else:
        set_read_write(sess)
        batch_id = inv.getLong('mop_batch_id')
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
        bill = batch.insert_bill(sess, account, reference, issue_date, start_date, finish_date, kwh, net, vat, gross, bill_type, breakdown, Supply.get_by_mpan_core(sess, mpan_core))
        sess.commit()
        inv.sendSeeOther("/reports/359/output/?mop_bill_id=" + str(bill.id))

except UserException, e:
    sess.rollback()
    render(inv, template, make_fields(sess, batch, e), 400)
finally:
    if sess is not None:
        sess.close()