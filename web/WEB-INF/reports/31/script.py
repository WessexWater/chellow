from net.sf.chellow.monad import Monad
import db
import templater
import utils
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
ReadType, Tpr, RegisterRead = db.ReadType, db.Tpr, db.RegisterRead
render = templater.render
UserException, form_decimal = utils.UserException, utils.form_decimal
form_date = utils.form_date
inv, template = globals()['inv'], globals()['template']


def make_fields(sess, read, message=None):
    read_types = sess.query(ReadType).order_by(ReadType.code).all()
    tprs = sess.query(Tpr).order_by(Tpr.code).all()

    messages = [] if message is None else [str(message)]
    return {
        'read': read, 'read_types': read_types, 'tprs': tprs,
        'messages': messages}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        read_id = inv.getLong('supplier_read_id')
        read = RegisterRead.get_by_id(sess, read_id)
        render(inv, template, make_fields(sess, read))
    else:
        db.set_read_write(sess)
        read_id = inv.getLong('supplier_read_id')
        read = RegisterRead.get_by_id(sess, read_id)
        if inv.hasParameter('update'):
            tpr_id = inv.getLong("tpr_id")
            tpr = Tpr.get_by_id(sess, tpr_id)
            coefficient = form_decimal(inv, "coefficient")
            units = inv.getString("units")
            msn = inv.getString("msn")
            mpan_str = inv.getString("mpan")
            previous_date = form_date(inv, "previous")
            previous_value = form_decimal(inv, "previous_value")
            previous_type_id = inv.getLong("previous_type_id")
            previous_type = ReadType.get_by_id(sess, previous_type_id)
            present_date = form_date(inv, "present")
            present_value = form_decimal(inv, "present_value")
            present_type_id = inv.getLong("present_type_id")
            present_type = ReadType.get_by_id(sess, present_type_id)

            read.update(
                tpr, coefficient, units, msn, mpan_str, previous_date,
                previous_value, previous_type, present_date, present_value,
                present_type)
            sess.commit()
            inv.sendSeeOther(
                "/reports/105/output/?supplier_bill_id=" + str(read.bill.id))
        elif inv.hasParameter("delete"):
            read.delete()
            sess.commit()
            inv.sendSeeOther(
                "/reports/105/output/?supplier_bill_id=" + str(read.bill.id))
except UserException, e:
    render(inv, template, make_fields(sess, read, e))
finally:
    sess.close()
