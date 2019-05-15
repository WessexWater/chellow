from datetime import datetime as Datetime
from sqlalchemy import or_
from sqlalchemy.sql.expression import null, true
import traceback
from chellow.models import Era, Supply, Source, Pc, Site, SiteEra, Session
import chellow.duos
import chellow.triad
import chellow.computer
from chellow.utils import HH, hh_format, req_int, utc_datetime
from flask import request, g
import chellow.dloads
import csv
import sys
import os
from chellow.views import chellow_redirect
import threading


def _make_eras(sess, year_start, year_finish, supply_id):
    eras = sess.query(Era).join(Supply).join(Source).join(Pc).filter(
        Era.start_date <= year_finish, or_(
            Era.finish_date == null(), Era.finish_date >= year_start),
        Source.code.in_(('net', 'gen-net')),
        Pc.code == '00').order_by(Supply.id)

    if supply_id is not None:
        eras = eras.filter(Supply.id == supply_id)

    return eras


def content(year, supply_id, user):
    caches = {}
    sess = f = writer = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            'supplies_triad.csv', user)
        f = open(running_name, mode='w', newline='')
        writer = csv.writer(f, lineterminator='\n')

        march_start = utc_datetime(year, 3, 1)
        march_finish = utc_datetime(year, 4, 1) - HH
        financial_year_start = utc_datetime(year - 1, 4, 1)

        def triad_csv(supply_source):
            if supply_source is None or \
                    supply_source.mpan_core.startswith('99'):
                return [''] * 19

            chellow.duos.duos_vb(supply_source)
            chellow.triad.hh(supply_source)
            chellow.triad.bill(supply_source)
            bill = supply_source.supplier_bill
            for rname, rset in supply_source.supplier_rate_sets.items():
                if len(rset) == 1:
                    bill[rname] = rset.pop()
            values = [supply_source.mpan_core]
            for i in range(1, 4):
                triad_prefix = 'triad-actual-' + str(i)
                for suffix in [
                        '-date', '-msp-kw', '-status', '-laf', '-gsp-kw']:
                    values.append(bill[triad_prefix + suffix])

            suffixes = ['gsp-kw', 'rate', 'gbp']
            values += [bill['triad-actual-' + suf] for suf in suffixes]
            return values

        writer.writerow(
            (
                "Site Code", "Site Name", "Supply Name", "Source",
                "Generator Type", "Import MPAN Core", "Import T1 Date",
                "Import T1 MSP kW", "Import T1 Status", "Import T1 LAF",
                "Import T1 GSP kW", "Import T2 Date", "Import T2 MSP kW",
                "Import T2 Status", "Import T2 LAF", "Import T2 GSP kW",
                "Import T3 Date", "Import T3 MSP kW", "Import T3 Status",
                "Import T3 LAF", "Import T3 GSP kW", "Import GSP kW",
                "Import Rate GBP / kW", "Import GBP", "Export MPAN Core",
                "Export T1 Date", "Export T1 MSP kW", "Export T1 Status",
                "Export T1 LAF", "Export T1 GSP kW", "Export T2 Date",
                "Export T2 MSP kW", "Export T2 Status", "Export T2 LAF",
                "Export T2 GSP kW", "Export T3 Date", "Export T3 MSP kW",
                "Export T3 Status", "Export T3 LAF", "Export T3 GSP kW",
                "Export GSP kW", "Export Rate GBP / kW", "Export GBP"))

        forecast_date = chellow.computer.forecast_date()
        eras = _make_eras(sess, financial_year_start, march_finish, supply_id)

        for era in eras:
            site = sess.query(Site).join(SiteEra).filter(
                SiteEra.is_physical == true(), SiteEra.era == era).one()
            supply = era.supply

            imp_mpan_core = era.imp_mpan_core
            if imp_mpan_core is None:
                imp_supply_source = None
            else:
                imp_supply_source = chellow.computer.SupplySource(
                    sess, march_start, march_finish, forecast_date, era, True,
                    caches)

            exp_mpan_core = era.exp_mpan_core
            if exp_mpan_core is None:
                exp_supply_source = None
            else:
                exp_supply_source = chellow.computer.SupplySource(
                    sess, march_start, march_finish, forecast_date, era, False,
                    caches)

            gen_type = supply.generator_type
            gen_type = '' if gen_type is None else gen_type.code
            vals = []
            for value in [
                    site.code, site.name, supply.name, supply.source.code,
                    gen_type] + triad_csv(imp_supply_source) + triad_csv(
                        exp_supply_source):
                if isinstance(value, Datetime):
                    vals.append(hh_format(value))
                else:
                    vals.append(str(value))
            writer.writerow(vals)

            # Avoid a long-running transaction
            sess.rollback()
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        writer.writerow([msg])
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_get(sess):
    year = req_int('year')
    supply_id = req_int('supply_id') if 'supply_id' in request.values else None
    threading.Thread(target=content, args=(year, supply_id, g.user)).start()
    return chellow_redirect("/downloads", 303)
