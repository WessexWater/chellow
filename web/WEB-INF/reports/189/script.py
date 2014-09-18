from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
from sqlalchemy.sql.expression import text
from datetime import datetime
import pytz

Monad.getUtils()['imprt'](globals(), {
        'db': ['Bill', 'BillType', 'ReadType', 'Tpr', 'set_read_write', 'session'], 
        'utils': ['UserException', 'form_date', 'form_decimal'],
        'templater': ['render']})


def make_fields(sess, bill, message=None):
    read_types = sess.query(ReadType).from_statement("select * from read_type order by code")
    tprs = sess.query(Tpr).from_statement("select * from tpr order by code")
    messages = [] if message is None else [str(message)]
    return {'bill': bill, 'read_types': read_types, 'tprs': tprs, 'messages': messages}

sess = None
try:
    sess = session()
    if inv.getRequest().getMethod() == 'GET':
        bill_id = inv.getLong('supplier_bill_id')
        bill = Bill.get_by_id(sess, bill_id)
        render(inv, template, make_fields(sess, bill))
    else:
        set_read_write(sess)
        bill_id = inv.getLong('supplier_bill_id')
        bill = Bill.get_by_id(sess, bill_id)
        tpr_id = inv.getLong("tpr_id")
        tpr = Tpr.get_by_id(sess, tpr_id)
        coefficient = form_decimal(inv, "coefficient")
        units_str = inv.getString("units")
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

        bill.insert_read(sess, tpr, coefficient, units_str, msn, mpan_str, previous_date, previous_value, previous_type, present_date, present_value, present_type)
        sess.commit()
        inv.sendSeeOther("/reports/105/output/?supplier_bill_id=" +
                    str(bill.id))
except UserException, e:
    render(inv, template, make_fields(sess, bill, e))
finally:
    sess.close()