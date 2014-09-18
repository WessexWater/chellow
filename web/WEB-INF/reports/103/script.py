from net.sf.chellow.monad import Monad
import datetime
import pytz
import os
from java.lang import System
import shutil
import StringIO
import tarfile

Monad.getUtils()['impt'](globals(), 'utils', 'templater')


def make_fields(lib_path, message=None):
    messages = [] if message is None else [str(message)]
    files = []
    for fl in sorted(os.listdir(lib_path)):
        full_file = os.path.join(lib_path, fl)
        statinfo = os.stat(full_file)
        files.append({'name': fl, 'last_modified': datetime.datetime.utcfromtimestamp(statinfo.st_mtime), 'size': statinfo.st_size, 'creation_date': datetime.datetime.utcfromtimestamp(statinfo.st_ctime) })
    return {'files': files, 'messages': messages}

try:
    lib_path = Monad.getContext().getRealPath("/WEB-INF/lib-python")
    if inv.getRequest().getMethod() == 'GET':
        templater.render(inv, template, make_fields(lib_path))
    else:
        if inv.hasParameter("delete"):
            name = inv.getString("name")
            shutil.rmtree(os.path.join(lib_path, name))
            inv.sendSeeOther("/reports/103/output/")
        else:
            file_item = inv.getFileItem("import_file")
            stream = file_item.getInputStream()
            f = StringIO.StringIO()
            bt = stream.read()
            while bt != -1:
                f.write(chr(bt))
                bt = stream.read()
            f.seek(0)
            t = tarfile.open(name=None, mode='r:gz', fileobj=f)
            t.extractall(lib_path)
            t.close()
            inv.sendSeeOther("/reports/103/output/")
except utils.UserException, e:
    render(inv, template, make_fields(lib_path, e))