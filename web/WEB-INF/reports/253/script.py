import os
import traceback
import sys
from net.sf.chellow.monad import Monad
import utils
Monad.getUtils()['impt'](globals(), 'computer', 'db', 'utils', 'triad', 'duos')
UserException = utils.UserException
inv = globals()['inv']

name = inv.getString("name")
head, name = os.path.split(os.path.normcase(os.path.normpath(name)))

if sys.platform.startswith('java'):
    download_path = Monad.getContext().getRealPath("/downloads")
else:
    download_path = os.path.join(os.environ['CHELLOW_HOME'], 'downloads')

full_name = os.path.join(download_path, name)
method = inv.getRequest().getMethod()

if method == 'GET':
    def content():
        fl = None
        try:
            fl = open(full_name)

            for line in fl:
                yield line

        except:
            yield traceback.format_exc()
        finally:
            fl.close()

    utils.send_response(inv, content, file_name=name)
elif method == 'POST':
    os.remove(full_name)
    inv.sendSeeOther("/reports/251/output/")
else:
    raise UserException("Don't recognize the method: " + method)
