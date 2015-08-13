from net.sf.chellow.monad import Monad
import pytz
import datetime
from dateutil.relativedelta import relativedelta
import utils
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
form_str, form_int, HH = utils.form_str, utils.form_int, utils.HH
Supply, HhDatum, Channel, Era = db.Supply, db.HhDatum, db.Channel, db.Era
Era, Source = db.Era, db.Source
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    site_code = form_str(inv, 'site_code')
    site = db.Site.get_by_code(sess, site_code)

    year = form_int(inv, 'year')
    month = form_int(inv, 'month')
    start_date = datetime.datetime(year, month, 1, tzinfo=pytz.utc)
    finish_date = start_date + relativedelta(months=1) - HH
    groups = []

    for group in site.groups(sess, start_date, finish_date, True):
        sup_ids = sorted(supply.id for supply in group.supplies)
        group_dict = {
            'supplies': [Supply.get_by_id(sess, id) for id in sup_ids]}
        groups.append(group_dict)

        data = iter(
            sess.query(HhDatum).join(
                Channel, Era, Supply, Source).filter(
                Channel.channel_type == 'ACTIVE', Supply.id.in_(sup_ids),
                HhDatum.start_date >= group.start_date,
                HhDatum.start_date <= group.finish_date).order_by(
                HhDatum.start_date, Supply.id))
        try:
            datum = data.next()
        except StopIteration:
            datum = None

        hh_date = group.start_date

        hh_data = []
        group_dict['hh_data'] = hh_data

        while not hh_date > group.finish_date:
            sups = []
            hh_dict = {
                'start_date': hh_date, 'supplies': sups, 'export_kwh': 0,
                'import_kwh': 0, 'parasitic_kwh': 0, 'generated_kwh': 0,
                'third_party_import_kwh': 0, 'third_party_export_kwh': 0}
            hh_data.append(hh_dict)
            for sup_id in sup_ids:
                sup_hh = {}
                sups.append(sup_hh)
                while datum is not None and datum.start_date == hh_date and \
                        datum.channel.era.supply.id == sup_id:
                    channel = datum.channel
                    imp_related = channel.imp_related
                    hh_float_value = float(datum.value)
                    source_code = channel.era.supply.source.code

                    prefix = 'import_' if imp_related else 'export_'
                    sup_hh[prefix + 'kwh'] = datum.value
                    sup_hh[prefix + 'status'] = datum.status

                    if not imp_related and source_code in ('net', 'gen-net'):
                        hh_dict['export_kwh'] += hh_float_value
                    if imp_related and source_code in ('net', 'gen-net'):
                        hh_dict['import_kwh'] += hh_float_value
                    if (imp_related and source_code == 'gen') or \
                            (not imp_related and source_code == 'gen-net'):
                        hh_dict['generated_kwh'] += hh_float_value
                    if (not imp_related and source_code == 'gen') or \
                            (imp_related and source_code == 'gen-net'):
                        hh_dict['parasitic_kwh'] += hh_float_value
                    if (imp_related and source_code == '3rd-party') or \
                            (not imp_related and
                                source_code == '3rd-party-reverse'):
                        hh_dict['third_party_import'] += hh_float_value
                    if (not imp_related and source_code == '3rd-party') or \
                            (imp_related and
                                source_code == '3rd-party-reverse'):
                        hh_dict['third_party_export'] += hh_float_value
                    try:
                        datum = data.next()
                    except StopIteration:
                        datum = None

            hh_dict['displaced_kwh'] = hh_dict['generated_kwh'] - \
                hh_dict['export_kwh'] - hh_dict['parasitic_kwh']
            hh_dict['used_kwh'] = hh_dict['import_kwh'] + \
                hh_dict['displaced_kwh']
            hh_date = hh_date + HH

    render(inv, template, {'site': site, 'groups': groups})
finally:
    if sess is not None:
        sess.close()
