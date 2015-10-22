from net.sf.chellow.monad import Monad
import templater
import db
import utils
import general_import
Monad.getUtils()['impt'](
    globals(), 'db', 'utils', 'templater', 'general_import')
render = templater.render
UserException = utils.UserException
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    proc_id = inv.getLong('process_id')
    proc = general_import.get_general_process(proc_id)
    fields = proc.get_fields()
    fields['is_alive'] = proc.isAlive()
    fields['process_id'] = proc_id
    render(inv, template, fields)
except UserException as e:
    render(inv, template, {'messages': [str(e)], 'process_id': proc_id})
finally:
    if sess is not None:
        sess.close()
