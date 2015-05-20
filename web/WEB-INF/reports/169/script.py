import traceback
import zipfile
from sqlalchemy import or_
from sqlalchemy.sql.expression import null
from net.sf.chellow.monad import Monad
import db
import os
import utils
import threading
import dloads

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater', 'dloads')
Channel, Supply, HhDatum, Era = db.Channel, db.Supply, db.HhDatum, db.Era
form_date, HH, form_bool = utils.form_date, utils.HH, utils.form_bool
form_str = utils.form_str
inv = globals()['inv']

start_date = form_date(inv, 'start')
finish_date = form_date(inv, 'finish')
imp_related = form_bool(inv, 'imp_related')
channel_type = form_str(inv, 'channel_type')
is_zipped = form_bool(inv, 'is_zipped')

base_name = ["supplies_hh_data", finish_date.strftime('%Y%m%d%H%M')]

if inv.hasParameter('supply_id'):
    supply_id = inv.getLong('supply_id')
else:
    supply_id = None

if inv.hasParameter('mpan_cores'):
    mpan_cores_str = form_str(inv, 'mpan_cores')
    mpan_cores = mpan_cores_str.splitlines()
    if len(mpan_cores) == 0:
        mpan_cores = None
    else:
        for i in range(len(mpan_cores)):
            mpan_cores[i] = utils.parse_mpan_core(mpan_cores[i])
else:
    mpan_cores = None

zf = None
tf = None


def content():
    sess = None
    try:
        sess = db.session()

        supplies = sess.query(Supply).join(Era).filter(
            or_(Era.finish_date == null(), Era.finish_date >= start_date),
            Era.start_date <= finish_date).order_by(Supply.id).distinct()
        if supply_id is not None:
            supply = Supply.get_by_id(sess, supply_id)
            supplies = supplies.filter(Supply.id == supply.id)
            first_era = sess.query(Era).filter(
                Era.supply == supply,
                or_(
                    Era.finish_date == null(), Era.finish_date >= start_date),
                Era.start_date <= finish_date).order_by(Era.start_date).first()
            if first_era.imp_mpan_core is None:
                name_core = first_era.exp_mpan_core
            else:
                name_core = first_era.imp_mpan_core
            base_name.append("supply_" + name_core.replace(' ', '_'))

        if mpan_cores is not None:
            supplies = supplies.filter(
                or_(
                    Era.imp_mpan_core.in_(mpan_cores),
                    Era.exp_mpan_core.in_(mpan_cores)))
            base_name.append('filter')

        outs = []
        titles = "MPAN Core,Date," + ','.join(map(str, range(48)))

        running_name, finished_name = dloads.make_names(
            '_'.join(base_name) + ('.zip' if is_zipped else '.csv'))
        if is_zipped:
            zf = zipfile.ZipFile(running_name, "w", zipfile.ZIP_DEFLATED)
        else:
            tf = open(running_name, "w")
            outs.append(titles)

        for supply in supplies:
            era = supply.find_era_at(sess, finish_date)
            if era is None or era.imp_mpan_core is None:
                mpan_core_str = "NA"
            else:
                mpan_core_str = era.imp_mpan_core

            current_date = start_date
            hh_data = iter(
                sess.query(HhDatum).join(Channel).join(Era).filter(
                    Era.supply == supply, HhDatum.start_date >= start_date,
                    HhDatum.start_date <= finish_date,
                    Channel.imp_related == imp_related,
                    Channel.channel_type == channel_type
                ).order_by(HhDatum.start_date))

            try:
                datum = hh_data.next()
            except StopIteration:
                datum = None

            while not current_date > finish_date:
                if current_date.hour == 0 and current_date.minute == 0:
                    outs.append(
                        "\n" + mpan_core_str + "," +
                        current_date.strftime('%Y-%m-%d'))
                outs.append(",")

                if datum is not None and datum.start_date == current_date:
                    outs.append(str(datum.value))
                    try:
                        datum = hh_data.next()
                    except StopIteration:
                        datum = None
                current_date += HH
            if is_zipped:
                fname = mpan_core_str + '_' + str(supply.id) + '.csv'
                zf.writestr(fname.encode('ascii'), titles + ''.join(outs))
            else:
                tf.write(''.join(outs))
            outs = []
        if is_zipped:
            zf.close()
        else:
            tf.close()

    except:
        msg = traceback.format_exc()
        if is_zipped:
            zf.writestr('error.txt', msg)
            zf.close()
        else:
            tf.write(msg)
    finally:
        os.rename(running_name, finished_name)
        if sess is not None:
            sess.close()

threading.Thread(target=content).start()
inv.sendSeeOther("/reports/251/output/")
