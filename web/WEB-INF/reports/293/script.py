from net.sf.chellow.monad import Monad
import tempfile
import StringIO
import sys

Monad.getUtils()['impt'](
    globals(), 'db', 'utils', 'templater', 'general_import')
UserException = utils.UserException
render = templater.render


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
        f = StringIO.StringIO()
        if sys.platform.startswith('java'):
            from java.io import InputStreamReader
            stream = InputStreamReader(file_item.getInputStream(), 'utf-8')
            bt = stream.read()
            while bt != -1:
                f.write(chr(bt))
                bt = stream.read()
        else:
            f.writelines(file_item.f.stream)

        f.seek(0)
        id = general_import.start_general_process(f)
        inv.sendSeeOther("/reports/295/output/?process_id=" + str(id))
except UserException, e:
    render(inv, template, make_fields(sess, e))
finally:
    if sess is not None:
        sess.close()
