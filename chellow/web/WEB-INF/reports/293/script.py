from net.sf.chellow.monad import Monad
import io
import utils
import templater
import general_import
import db
Monad.getUtils()['impt'](
    globals(), 'db', 'utils', 'templater', 'general_import')
UserException = utils.UserException
render = templater.render
inv, template = globals()['inv'], globals()['template']


def make_fields(sess, message=None):
    messages = [] if message is None else [str(e)]
    return {
        'messages': messages,
        'process_ids': sorted(
            general_import.get_general_process_ids(), reverse=True)}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        render(inv, template, make_fields(sess))
    else:
        file_item = inv.getFileItem("import_file")
        file_name = file_item.getName()
        if not file_name.endswith('.csv'):
            raise UserException(
                "The file name should have the extension .csv.")
        f = io.StringIO(str(file_item.f.stream.read(), 'utf-8'))
        f.seek(0)
        id = general_import.start_general_process(f)
        inv.sendSeeOther("/reports/295/output/?process_id=" + str(id))
except UserException as e:
    render(inv, template, make_fields(sess, e))
finally:
    if sess is not None:
        sess.close()
