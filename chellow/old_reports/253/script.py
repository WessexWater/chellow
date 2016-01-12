import os
import traceback
from net.sf.chellow.monad import Monad
import utils
import chellow

Monad.getUtils()['impt'](globals(), 'computer', 'db', 'utils', 'triad', 'duos')
UserException = utils.UserException
inv = globals()['inv']

name = inv.getString("name")
head, name = os.path.split(os.path.normcase(os.path.normpath(name)))

download_path = os.path.join(chellow.app.instance_path, 'downloads')

full_name = os.path.join(download_path, name)
method = inv.getRequest().getMethod()

if method == 'GET':
    def content():
        try:
            with open(full_name, 'rb') as fl:
                yield fl.read()
        except:
            yield traceback.format_exc()

    utils.send_response(inv, content, file_name=name)
elif method == 'POST':
    os.remove(full_name)
    inv.sendSeeOther("/reports/251/output/")
else:
    raise UserException("Don't recognize the method: " + method)
