import datetime
from dateutil.relativedelta import relativedelta
import pytz
from sqlalchemy import or_
from sqlalchemy.sql.expression import null
import traceback
from chellow.models import (
    Session, Contract, Site, SiteEra, Era, Supply, Source)
from chellow.utils import HH, hh_format, req_int, send_response
import chellow.computer


def content(contract_id, end_year, end_month, months):
    caches = {}
    sess = None
    try:
        sess = Session()

        yield ','.join(
            (
                'Site Code', 'Site Name', 'Associated Site Ids', 'From', 'To',
                'Gen Types', 'CHP kWh', 'LM kWh', 'Turbine kWh', 'PV kWh'))

        finish_date = datetime.datetime(
            end_year, end_month, 1, tzinfo=pytz.utc) + \
            relativedelta(months=1) - HH

        start_date = datetime.datetime(
            end_year, end_month, 1, tzinfo=pytz.utc) - \
            relativedelta(months=months-1)

        forecast_date = chellow.computer.forecast_date()

        contract = Contract.get_supplier_by_id(sess, contract_id)
        sites = sess.query(Site).join(SiteEra).join(Era).join(Supply). \
            join(Source).filter(
                or_(Era.finish_date == null(), Era.finish_date >= start_date),
                Era.start_date <= finish_date,
                or_(
                    Source.code.in_(('gen', 'gen-net')),
                    Era.exp_mpan_core != null())).distinct()
        bill_titles = chellow.computer.contract_func(
            caches, contract, 'displaced_virtual_bill_titles', None)()

        for title in bill_titles:
            if title == 'total-msp-kwh':
                title = 'total-displaced-msp-kwh'
            yield ',' + title
        yield '\n'

        for site in sites:
            month_start = start_date
            month_finish = month_start + relativedelta(months=1) - HH
            while not month_finish > finish_date:
                for site_group in site.groups(
                        sess, month_start, month_finish, True):
                    if site_group.start_date > month_start:
                        chunk_start = site_group.start_date
                    else:
                        chunk_start = month_start
                    if site_group.finish_date > month_finish:
                        chunk_finish = month_finish
                    else:
                        chunk_finish = site_group.finish_date

                    displaced_era = chellow.computer.displaced_era(
                        sess, site_group, chunk_start, chunk_finish)
                    if displaced_era is None:
                        continue
                    supplier_contract = displaced_era.imp_supplier_contract
                    if contract is not None and contract != supplier_contract:
                        continue

                    linked_sites = ','.join(
                        a_site.code for a_site in site_group.sites
                        if not a_site == site)
                    generator_types = ' '.join(
                        sorted(
                            [
                                supply.generator_type.code for supply in
                                site_group.supplies
                                if supply.generator_type is not None]))

                    yield ','.join(
                        '"' + value + '"' for value in [
                            site.code, site.name, linked_sites,
                            hh_format(chunk_start), hh_format(chunk_finish),
                            generator_types])

                    total_gen_breakdown = {}

                    results = iter(
                        sess.execute(
                            "select supply.id, hh_datum.value, "
                            "hh_datum.start_date, channel.imp_related, "
                            "source.code, generator_type.code as "
                            "gen_type_code from hh_datum, channel, source, "
                            "era, supply left outer join generator_type on "
                            "supply.generator_type_id = generator_type.id "
                            "where hh_datum.channel_id = channel.id and "
                            "channel.era_id = era.id and era.supply_id = "
                            "supply.id and supply.source_id = source.id and "
                            "channel.channel_type = 'ACTIVE' and not "
                            "(source.code = 'net' and channel.imp_related "
                            "is true) and hh_datum.start_date >= "
                            ":chunk_start and hh_datum.start_date "
                            "<= :chunk_finish and "
                            "supply.id = any(:supply_ids) order "
                            "by hh_datum.start_date, supply.id",
                            params={
                                'chunk_start': chunk_start,
                                'chunk_finish': chunk_finish,
                                'supply_ids': [
                                    s.id for s in site_group.supplies]}))
                    try:
                        res = next(results)
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
                                if (imp_related and source_code == 'gen') or \
                                        (not imp_related and
                                            source_code == 'gen-net'):
                                    gen_breakdown[gen_type] = \
                                        gen_breakdown.setdefault(
                                            gen_type, 0) + hhChannelValue

                                if (
                                        not imp_related and
                                        source_code == 'gen') or (
                                        imp_related and
                                        source_code == 'gen-net'):
                                    gen_breakdown[gen_type] = \
                                        gen_breakdown.setdefault(
                                            gen_type, 0) - hhChannelValue

                                try:
                                    res = next(results)
                                    source_code = res.code
                                    hhChannelValue = res.value
                                    hhChannelStartDate = res.start_date
                                    imp_related = res.imp_related
                                    gen_type = res.gen_type_code
                                except StopIteration:
                                    hhChannelStartDate = None

                            displaced = sum(gen_breakdown.itervalues()) - \
                                exported
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

                    for title in ['chp', 'lm', 'turb', 'pv']:
                        yield ',' + str(total_gen_breakdown.get(title, ''))

                    site_ds = chellow.computer.SiteSource(
                        sess, site, chunk_start, chunk_finish, forecast_date,
                        None, caches, displaced_era)
                    disp_func = chellow.computer.contract_func(
                        caches, supplier_contract, 'displaced_virtual_bill',
                        None)
                    disp_func(site_ds)
                    bill = site_ds.supplier_bill
                    for title in bill_titles:
                        if title in bill:
                            val = bill[title]
                            if isinstance(val, datetime.datetime):
                                val = hh_format(val)
                            else:
                                val = str(val)
                            yield ',"' + val + '"'
                            del bill[title]
                        else:
                            yield ',""'

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


def do_get(sess):
    end_year = req_int('finish_year')
    end_month = req_int('finish_month')
    months = req_int('months')
    contract_id = req_int('supplier_contract_id')
    return send_response(
        content, args=(contract_id, end_year, end_month, months),
        file_name='displaced.csv')
