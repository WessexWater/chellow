from net.sf.chellow.monad import Monad
import datetime
import pytz
from sqlalchemy import func
from dateutil.relativedelta import relativedelta

Monad.getUtils()['impt'](globals(), 'templater', 'db', 'utils')

HH = utils.HH
Supply, HhDatum, Channel, Era = db.Supply, db.HhDatum, db.Channel, db.Era

sess = None
try:
    sess = db.session()
    supply_id = inv.getLong("supply_id")
    supply = Supply.get_by_id(sess, supply_id)

    is_import = inv.getBoolean("is_import")

    year = inv.getInteger('year')
    years = inv.getInteger('years')

    month_start = datetime.datetime(year - years + 1, 1, 1, tzinfo=pytz.utc)
    months = []
    for i in range(12 * years):
        next_month_start = month_start + relativedelta(months=1)
        month_finish = next_month_start - HH
    
        month_data = {}
        months.append(month_data)

        era = supply.find_era_at(sess, month_finish)
        if era != None:
            mpan_core = era.imp_mpan_core if is_import else era.exp_mpan_core
            if mpan_core != None:
                month_data['mpan_core'] = mpan_core
                month_data['sc'] = era.imp_sc if is_import else era.exp_sc

        md_kvah = 0
        for kwh, kvarh, hh_date in sess.execute("select cast(max(hh_ac.value) as double precision), cast(max(hh_re.value) as double precision), hh_ac.start_date from hh_datum as hh_ac join channel as channel_ac on (hh_ac.channel_id = channel_ac.id) join era as era_ac on (channel_ac.era_id = era_ac.id) join hh_datum as hh_re on (hh_ac.start_date = hh_re.start_date) join channel as channel_re on (hh_re.channel_id = channel_re.id) join era as era_re on (channel_re.era_id = era_re.id) where era_ac.supply_id = :supply_id and era_re.supply_id = :supply_id and channel_ac.imp_related = :is_import and channel_re.imp_related = :is_import and channel_ac.channel_type = 'ACTIVE' and channel_re.channel_type in ('REACTIVE_IMP', 'REACTIVE_EXP') and hh_ac.start_date >= :month_start and hh_ac.start_date <= :month_finish and hh_re.start_date >= :month_start and hh_re.start_date <= :month_finish group by hh_ac.start_date", params={'month_start': month_start, 'month_finish': month_finish, 'is_import': is_import, 'supply_id': supply.id}):
            kvah = (kwh ** 2 + kvarh ** 2) ** 0.5
            if kvah > md_kvah:
                md_kvah = kvah
                month_data['md_kva'] = 2 * md_kvah
                month_data['md_kvar'] = kvarh * 2
                month_data['md_kw'] = kwh * 2
                month_data['md_pf'] = float(kwh) / kvah
                month_data['md_date'] = hh_date

        total_kwh = sess.query(func.sum(HhDatum.value)).join(Channel).join(Era).filter(Era.supply_id==supply.id, Channel.channel_type=='ACTIVE', Channel.imp_related==is_import, HhDatum.start_date>=month_start, HhDatum.start_date<=month_finish).one()[0]

        if total_kwh != None:
            month_data['total_kwh'] = float(total_kwh)

        month_data['start_date'] = month_start
        month_start = next_month_start

    templater.render(inv, template, {'supply': supply, 'months': months, 'is_import': is_import, 'now': datetime.datetime.now(pytz.utc)})
finally:
    if sess is not None:
        sess.close()
