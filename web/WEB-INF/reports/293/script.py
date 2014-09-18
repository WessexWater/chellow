from net.sf.chellow.monad import Monad
from java.lang import System
from java.io import InputStreamReader
import tempfile
import StringIO

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'session', 'Batch', 'set_read_write'],
        'utils': ['UserException', 'prev_hh', 'next_hh', 'hh_after', 'hh_before', 'HH'],
        'templater': ['render'],
        'general_import': ['start_general_process', 'get_general_process_ids', 'get_general_process']})


def make_fields(sess, message=None):
    messages = [] if message is None else [str(e)]
    return {'messages': messages, 'process_ids': sorted(get_general_process_ids(), reverse=True)}

sess = None
try:
    sess = session()
    if inv.getRequest().getMethod() == 'GET':
        render(inv, template, make_fields(sess))
    else:
        file_item = inv.getFileItem("import_file")
        file_name = file_item.getName()
        if not file_name.endswith('.csv'):
            raise UserException("The file name should have the extension .csv.")
        stream = InputStreamReader(file_item.getInputStream(), 'utf-8')
        f = StringIO.StringIO()
        bt = stream.read()
        while bt != -1:
            f.write(chr(bt))
            bt = stream.read()
        id = start_general_process(f)
        inv.sendSeeOther("/reports/295/output/?process_id=" + str(id))
except UserException, e:
    render(inv, template, make_fields(sess, e))
finally:
    if sess is not None:
        sess.close()