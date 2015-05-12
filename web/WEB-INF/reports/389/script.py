from net.sf.chellow.monad import Monad
import datetime
from dateutil.relativedelta import relativedelta
import pytz
import traceback
import utils
import db
import computer
Monad.getUtils()['impt'](globals(), 'utils', 'db', 'computer')

HH, hh_format = utils.HH, utils.hh_format
Site, Era, SiteEra, Supply = db.Site, db.Era, db.SiteEra, db.Supply
Source, Contract = db.Source, db.Contract
inv = globals()['inv']

caches = {}
end_year = inv.getInteger('finish_year')
end_month = inv.getInteger('finish_month')
months = inv.getInteger('months')
site_id = inv.getLong('site_id')


def content():
    sess = None
    try:
        sess = db.session()

        finish_date = datetime.datetime(
            end_year, end_month, 1, tzinfo=pytz.utc) + \
            relativedelta(months=1) - HH

        start_date = datetime.datetime(
            end_year, end_month, 1, tzinfo=pytz.utc) - \
            relativedelta(months=months-1)

        forecast_date = computer.forecast_date()

        site = Site.get_by_id(sess, site_id)

        month_start = start_date
        month_finish = month_start + relativedelta(months=1) - HH
        while not month_finish > finish_date:
            for group in site.groups(sess, month_start, month_finish, True):
                if group.start_date > month_start:
                    chunk_start = group.start_date
                else:
                    chunk_start = month_start
                if group.finish_date > month_finish:
                    chunk_finish = month_finish
                else:
                    chunk_finish = group.finish_date

                displaced_era = computer.displaced_era(
                    sess, group, chunk_start, chunk_finish)
                if displaced_era is None:
                    continue
                supplier_contract = displaced_era.imp_supplier_contract

                linked_sites = ','.join(
                    a_site.code for a_site in group.sites
                    if not a_site == site)
                generator_types = ' '.join(
                    sorted(
                        [
                            supply.generator_type.code for
                            supply in group.supplies
                            if supply.generator_type is not None]))

                total_gen_breakdown = {}

                results = iter(
                    sess.execute(
                        "select supply.id, hh_datum.value, "
                        "hh_datum.start_date, channel.imp_related, "
                        "source.code, generator_type.code as gen_type_code "
                        "from hh_datum, channel, source, era, supply left "
                        "outer join generator_type on "
                        "supply.generator_type_id = generator_type.id where "
                        "hh_datum.channel_id = channel.id and "
                        "channel.era_id = era.id and era.supply_id = "
                        "supply.id and supply.source_id = source.id and "
                        "channel.channel_type = 'ACTIVE' and not "
                        "(source.code = 'net' and channel.imp_related is "
                        "true) and hh_datum.start_date >= :chunk_start and "
                        "hh_datum.start_date <= :chunk_finish and "
                        "supply.id = any(:supply_ids) order by "
                        "hh_datum.start_date, supply.id",
                        params={
                            'chunk_start': chunk_start,
                            'chunk_finish': chunk_finish,
                            'supply_ids': [s.id for s in group.supplies]}))
                try:
                    res = results.next()
                    hhChannelValue = res.value
                    hhChannelStartDate = res.start_date
                    imp_related = res.imp_related
                    source_code = res.code
                    gen_type = res.gen_type_code
                    hh_date = chunk_start

                    while hh_date <= finish_date:
                        gen_breakdown = {}
                        exported = 0
                        while hhChannelStartDate == hh_date:
                            if not imp_related and source_code in (
                                    'net', 'gen-net'):
                                exported += hhChannelValue
                            if (imp_related and source_code == 'gen') or (
                                    not imp_related and
                                    source_code == 'gen-net'):
                                gen_breakdown[gen_type] = \
                                    gen_breakdown.setdefault(gen_type, 0) + \
                                    hhChannelValue

                            if (not imp_related and source_code == 'gen') or \
                                    (imp_related and source_code == 'gen-net'):
                                gen_breakdown[gen_type] = \
                                    gen_breakdown.setdefault(gen_type, 0) - \
                                    hhChannelValue

                            try:
                                res = results.next()
                                source_code = res.code
                                hhChannelValue = res.value
                                hhChannelStartDate = res.start_date
                                imp_related = res.imp_related
                                gen_type = res.gen_type_code
                            except StopIteration:
                                hhChannelStartDate = None

                        displaced = sum(gen_breakdown.itervalues()) - exported
                        added_so_far = 0
                        for key in sorted(gen_breakdown.iterkeys()):
                            kwh = gen_breakdown[key]
                            if kwh + added_so_far > displaced:
                                total_gen_breakdown[key] = \
                                    total_gen_breakdown.get(key, 0) + \
                                    displaced - added_so_far
                                break
                            else:
                                total_gen_breakdown[key] = \
                                    total_gen_breakdown.get(key, 0) + kwh
                                added_so_far += kwh

                        hh_date += HH
                except StopIteration:
                    pass

                site_ds = computer.SiteSource(
                    sess, site, chunk_start, chunk_finish, forecast_date, None,
                    caches, displaced_era)
                disp_func = computer.contract_func(
                    caches, supplier_contract, 'displaced_virtual_bill', None)
                disp_func(site_ds)
                bill = site_ds.supplier_bill

                bill_titles = computer.contract_func(
                    caches, supplier_contract, 'displaced_virtual_bill_titles',
                    None)()
                yield ','.join(
                    [
                        'Site Code', 'Site Name', 'Associated Site Ids',
                        'From', 'To', 'Gen Types', 'CHP kWh', 'LM kWh',
                        'Turbine kWh', 'PV kWh'] + bill_titles) + '\n'

                yield ','.join('"' + str(value) + '"' for value in [
                    site.code, site.name, linked_sites, hh_format(chunk_start),
                    hh_format(chunk_finish), generator_types] + [
                    total_gen_breakdown.get(t, '') for t in [
                        'chp', 'lm', 'turb', 'pv']])

                for title in bill_titles:
                    if title in bill:
                        v = bill[title]
                        if isinstance(v, datetime.datetime):
                            val = hh_format(v)
                        else:
                            val = str(v)

                        del bill[title]
                    else:
                        val = ''
                    yield ',"' + val + '"'

                for k in sorted(bill.keys()):
                    yield ',"' + k + '","' + str(bill[k]) + '"'
                yield '\n'

            month_start += relativedelta(months=1)
            month_finish = month_start + relativedelta(months=1) - HH

    except:
        yield traceback.format_exc()
    finally:
        if sess is not None:
            sess.close()

utils.send_response(inv, content, file_name='displaced.csv')
