from sqlalchemy.orm import joinedload
import traceback
from chellow.models import Llfc, Session
from chellow.views import chellow_redirect
import chellow.dloads
import csv
from flask import g
import threading
import os
from chellow.utils import hh_format


def content(user):
    sess = f = writer = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            'llfcs.csv', user)
        f = open(running_name, mode='w', newline='')
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(
            (
                'Chellow Id', 'DNO Code', 'Code', 'Description',
                'Voltage Level', 'Is Substation?', 'Is Import?', 'Valid From',
                'Valid To'))

        for llfc in sess.query(Llfc).order_by(Llfc.id).options(
                joinedload(Llfc.dno), joinedload(Llfc.voltage_level)):
            writer.writerow(
                (
                    str(llfc.id), llfc.dno.dno_code, llfc.code,
                    llfc.description, llfc.voltage_level.code,
                    llfc.is_substation, llfc.is_import,
                    hh_format(llfc.valid_from), hh_format(llfc.valid_to)))
    except BaseException:
        writer.writerow([traceback.format_exc()])
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_get(sess):
    args = (g.user,)
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
