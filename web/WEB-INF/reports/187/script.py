import traceback
from net.sf.chellow.monad import Monad
from sqlalchemy import or_
from sqlalchemy.sql.expression import null, true
import db
import utils
import StringIO
import zipfile

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
HhDatum, Channel, Era, Supply = db.HhDatum, db.Channel, db.Era, db.Supply
Site, SiteEra = db.Site, db.SiteEra
hh_format, UserException = utils.hh_format, utils.UserException
form_str, form_bool = utils.form_str, utils.form_bool
inv = globals()['inv']

start_date = utils.form_date(inv, 'start')
finish_date = utils.form_date(inv, 'finish')

method = inv.getRequest().getMethod()

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

if finish_date < start_date:
    raise UserException("The finish date can't be before the start date.")

is_zipped = form_bool(inv, 'is_zipped')

if is_zipped:
    mimetype = 'application/zip'
    file_extension = ".zip"
    bffr = StringIO.StringIO()
    zf = zipfile.ZipFile(bffr, 'w')
else:
    mimetype = 'text/csv'
    file_extension = ".csv"

file_name = "hh_data_row_" + start_date.strftime("%Y%m%d%H%M") + file_extension

titles = ','.join('"' + v + '"' for v in (
    "Site Code", "Imp MPAN Core", "Exp Mpan Core", "Start Date",
    "Import ACTIVE", "Import ACTIVE Status", "Import REACTIVE_IMP",
    "Import REACTIVE_IMP Status", "Import REACTIVE_EXP",
    "Import REACTIVE_EXP Status", "Export ACTIVE",
    "Export ACTIVE Status", "Export REACTIVE_IMP",
    "Export REACTIVE_IMP Status", "Export REACTIVE_EXP",
    "Export REACTIVE_EXP Status")) + "\n"


def content():
    sess = None
    try:
        sess = db.session()
        if method == 'GET':
            eras = sess.query(Site, Era).join(SiteEra).join(Era).filter(
                Era.start_date <= finish_date,
                or_(
                    Era.finish_date == null(), Era.finish_date >= start_date),
                SiteEra.is_physical == true()).order_by(
                Era.supply_id, Era.start_date)
            if supply_id is not None:
                sup = Supply.get_by_id(sess, supply_id)
                eras = eras.filter(Era.supply == sup)

            if mpan_cores is not None:
                eras = eras.filter(
                    or_(
                        Era.imp_mpan_core.in_(mpan_cores),
                        Era.exp_mpan_core.in_(mpan_cores)))

            if not is_zipped:
                yield titles

            eras = eras.all()

            for i, (site, era) in enumerate(eras):
                imp_mpan_core = era.imp_mpan_core
                imp_mpan_core_str = '' if imp_mpan_core is None \
                    else imp_mpan_core
                exp_mpan_core = era.exp_mpan_core
                exp_mpan_core_str = '' if exp_mpan_core is None \
                    else exp_mpan_core

                outs = []

                for hh_start_date, imp_active, imp_active_status, \
                    imp_reactive_imp, imp_reactive_imp_status, \
                    imp_reactive_exp, imp_reactive_exp_status, \
                    exp_active, exp_active_status, exp_reactive_imp, \
                    exp_reactive_imp_status, exp_reactive_exp, \
                    exp_reactive_exp_status in sess.execute("""
    select hh_base.start_date, max(imp_active.value), max(imp_active.status),
        max(imp_reactive_imp.value), max(imp_reactive_imp.status),
        max(imp_reactive_exp.value), max(imp_reactive_exp.status),
        max(exp_active.value), max(exp_active.status),
        max(exp_reactive_imp.value), max(imp_reactive_imp.status),
        max(exp_reactive_imp.value), max(imp_reactive_exp.status)
    from hh_datum hh_base
        join channel on hh_base.channel_id = channel.id
        left join hh_datum imp_active
            on (imp_active.id = hh_base.id and channel.imp_related is true and
                channel.channel_type = 'ACTIVE')
        left join hh_datum imp_reactive_imp
            on (imp_reactive_imp.id = hh_base.id
                and channel.imp_related is true and
                channel.channel_type = 'REACTIVE_IMP')
        left join hh_datum imp_reactive_exp
            on (imp_reactive_exp.id = hh_base.id
                and channel.imp_related is true and
                channel.channel_type = 'REACTIVE_EXP')
        left join hh_datum exp_active
            on (exp_active.id = hh_base.id and channel.imp_related is false and
                channel.channel_type = 'ACTIVE')
        left join hh_datum exp_reactive_imp
                    on (exp_reactive_imp.id = hh_base.id
                        and channel.imp_related is
                    false and channel.channel_type = 'REACTIVE_IMP')
        left join hh_datum exp_reactive_exp
                    on (exp_reactive_exp.id = hh_base.id
                    and channel.imp_related is false
                    and channel.channel_type = 'REACTIVE_EXP')
    where era_id = :era_id
        and hh_base.start_date between :start_date and :finish_date
    group by hh_base.start_date
    order by hh_base.start_date
        """, params={
                        'era_id': era.id, 'start_date': start_date,
                        'finish_date': finish_date}):
                    outs.append(','.join(
                        '"' + ('' if v is None else str(v)) + '"' for v in (
                            site.code, imp_mpan_core_str, exp_mpan_core_str,
                            hh_format(hh_start_date), imp_active,
                            imp_active_status, imp_reactive_imp,
                            imp_reactive_imp_status, imp_reactive_exp,
                            imp_reactive_exp_status, exp_active,
                            exp_active_status, exp_reactive_imp,
                            exp_reactive_imp_status, exp_reactive_exp,
                            exp_reactive_exp_status)) + '\n')
                if is_zipped:
                    zf.writestr(
                        (
                            "hh_data_row_" + str(era.id) + "_" +
                            str(era.imp_mpan_core) + "_" +
                            str(era.exp_mpan_core)).replace(' ', '') + '.csv',
                        titles + ''.join(outs))

                    if i == len(eras) - 1:
                        zf.close()
                    yield bffr.getvalue()
                    bffr.truncate()
                else:
                    yield ''.join(outs)
    except:
        msg = traceback.format_exc()
        if is_zipped:
            zf.writestr('error.txt', msg)
            zf.close()
            yield bffr.getValue()
            bffr.truncate()
        else:
            yield msg
    finally:
        if sess is not None:
            sess.close()

utils.send_response(inv, content, file_name=file_name, mimetype=mimetype)
