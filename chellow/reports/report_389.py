from datetime import datetime as Datetime
from dateutil.relativedelta import relativedelta
import pytz
import traceback
from chellow.models import Site, Era, SiteEra
from chellow.utils import HH, hh_format, req_int, send_response, hh_range
import chellow.computer
from sqlalchemy import or_, null


def content(end_year, end_month, months, site_id, sess):
    caches = {}
    try:
        finish_date = Datetime(end_year, end_month, 1, tzinfo=pytz.utc) + \
            relativedelta(months=1) - HH

        start_date = Datetime(end_year, end_month, 1, tzinfo=pytz.utc) - \
            relativedelta(months=months-1)

        forecast_date = chellow.computer.forecast_date()

        site = Site.get_by_id(sess, site_id)

        month_start = start_date
        month_finish = month_start + relativedelta(months=1) - HH
        while not month_finish > finish_date:
            displaced_era = chellow.computer.displaced_era(
                sess, caches, site, month_start, month_finish, forecast_date)
            if displaced_era is None:
                continue
            supplier_contract = displaced_era.imp_supplier_contract

            linked_sites = set()
            generator_types = set()
            for era in sess.query(Era).join(SiteEra).filter(
                    SiteEra.site == site, Era.start_date <= month_finish, or_(
                        Era.finish_date == null(),
                        Era.finish_date >= month_start)):
                for site_era in era.site_eras:
                    if site_era.site != site:
                        linked_sites.add(site_era.site.code)
                supply = era.supply
                if supply.generator_type is not None:
                    generator_types.add(supply.generator_type.code)

            supply_ids = {
                e.supply.id for e in sess.query(Era).join(SiteEra).filter(
                    SiteEra.is_physical, SiteEra.site == site,
                    Era.start_date <= month_finish, or_(
                        Era.finish_date == null(),
                        Era.finish_date >= month_start))}

            total_gen_breakdown = {}

            results = iter(
                sess.execute(
                    "select hh_datum.value, "
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
                    "true) and hh_datum.start_date >= :month_start and "
                    "hh_datum.start_date <= :month_finish and "
                    "supply.id = any(:supply_ids) order by "
                    "hh_datum.start_date, supply.id",
                    params={
                        'month_start': month_start,
                        'month_finish': month_finish,
                        'supply_ids': list(supply_ids)}))
            (
                val, hh_start, imp_related, source_code, gen_type_code) = next(
                    results, (None, None, None, None, None))

            for hh_date in hh_range(month_start, month_finish):
                gen_breakdown = {}
                exported = 0
                while hh_start == hh_date:
                    if not imp_related and source_code in (
                            'net', 'gen-net'):
                        exported += val
                    if (imp_related and source_code == 'gen') or (
                            not imp_related and source_code == 'gen-net'):
                        gen_breakdown[gen_type_code] = \
                            gen_breakdown.setdefault(gen_type_code, 0) + val

                    if (not imp_related and source_code == 'gen') or \
                            (imp_related and source_code == 'gen-net'):
                        gen_breakdown[gen_type_code] = \
                            gen_breakdown.setdefault(gen_type_code, 0) - val
                    (
                        val, hh_start, imp_related, source_code, gen_type_code
                        ) = next(results, (None, None, None, None, None))

                displaced = sum(gen_breakdown.values()) - exported
                added_so_far = 0
                for key in sorted(gen_breakdown.keys()):
                    kwh = gen_breakdown[key]
                    if kwh + added_so_far > displaced:
                        total_gen_breakdown[key] = \
                            total_gen_breakdown.get(key, 0) + displaced - \
                            added_so_far
                        break
                    else:
                        total_gen_breakdown[key] = \
                            total_gen_breakdown.get(key, 0) + kwh
                        added_so_far += kwh

            site_ds = chellow.computer.SiteSource(
                sess, site, month_start, month_finish, forecast_date, None,
                caches, displaced_era)
            disp_func = chellow.computer.contract_func(
                caches, supplier_contract, 'displaced_virtual_bill', None)
            disp_func(site_ds)
            bill = site_ds.supplier_bill

            bill_titles = chellow.computer.contract_func(
                caches, supplier_contract, 'displaced_virtual_bill_titles',
                None)()
            yield ','.join(
                [
                    'Site Code', 'Site Name', 'Associated Site Ids',
                    'From', 'To', 'Gen Types', 'CHP kWh', 'LM kWh',
                    'Turbine kWh', 'PV kWh'] + bill_titles) + '\n'

            yield ','.join('"' + str(value) + '"' for value in [
                site.code, site.name, ', '.join(sorted(list(linked_sites))),
                hh_format(month_start), hh_format(month_finish),
                ', '.join(sorted(list(generator_types)))] + [
                total_gen_breakdown.get(t, '') for t in [
                    'chp', 'lm', 'turb', 'pv']])

            for title in bill_titles:
                if title in bill:
                    v = bill[title]
                    if isinstance(v, Datetime):
                        val = hh_format(v)
                    else:
                        val = str(v)

                    del bill[title]
                else:
                    val = ''
                yield ',"' + val + '"'

            for k in sorted(bill.keys()):
                v = bill[k]
                if isinstance(v, Datetime):
                    val = hh_format(v)
                else:
                    val = str(v)
                yield ',"' + k + '","' + val + '"'
            yield '\n'

            month_start += relativedelta(months=1)
            month_finish = month_start + relativedelta(months=1) - HH

    except:
        yield traceback.format_exc()


def do_get(sess):
    end_year = req_int('finish_year')
    end_month = req_int('finish_month')
    months = req_int('months')
    site_id = req_int('site_id')
    return send_response(
        content, args=(end_year, end_month, months, site_id, sess),
        file_name='displaced.csv')
