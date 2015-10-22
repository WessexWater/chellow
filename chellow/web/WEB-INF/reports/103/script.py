from net.sf.chellow.monad import Monad
import datetime
import os
import shutil
import io
import tarfile
import templater
import dloads
import utils

Monad.getUtils()['impt'](globals(), 'utils', 'templater', 'dloads')
render = templater.render
inv, template = globals()['inv'], globals()['template']


def make_fields(lib_path, message=None):
    messages = [] if message is None else [str(message)]
    files = []
    for fl in sorted(os.listdir(lib_path)):
        full_file = os.path.join(lib_path, fl)
        statinfo = os.stat(full_file)
        files.append(
            {
                'name': fl,
                'last_modified': datetime.datetime.utcfromtimestamp(
                    statinfo.st_mtime),
                'size': statinfo.st_size,
                'creation_date': datetime.datetime.utcfromtimestamp(
                    statinfo.st_ctime)})
    mem_items = dloads.get_mem_items()
    mem_keys = sorted(mem_items.keys())
    return {
        'files': files, 'messages': messages, 'mem_items': mem_items,
        'mem_keys': mem_keys}

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
            f = io.StringIO()
            bt = stream.read()
            while bt != -1:
                f.write(chr(bt))
                bt = stream.read()
            f.seek(0)
            t = tarfile.open(name=None, mode='r:gz', fileobj=f)
            t.extractall(lib_path)
            t.close()
            inv.sendSeeOther("/reports/103/output/")
except utils.UserException as e:
    render(inv, template, make_fields(lib_path, e))
