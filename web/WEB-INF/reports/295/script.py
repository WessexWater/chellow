from net.sf.chellow.monad import Monad
from java.lang import System
import tempfile

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'session', 'Batch', 'set_read_write'],
        'utils': ['UserException', 'prev_hh', 'next_hh', 'hh_after', 'hh_before', 'HH'],
        'templater': ['render'],
        'general_import': ['start_general_process', 'get_general_process_ids', 'get_general_process']})


sess = None
try:
    sess = session()
    proc_id = inv.getLong('process_id')
    proc = get_general_process(proc_id)
    fields = proc.get_fields()
    fields['is_alive'] = proc.isAlive()
    fields['process_id'] = proc_id
    render(inv, template, fields)
except UserException, e:
    render(inv, template, {'messages': [str(e)], 'process_id': proc_id})
finally:
    if sess is not None:
        sess.close()