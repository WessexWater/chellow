from net.sf.chellow.monad import Monad
import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_
import pytz

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'computer', 'duos', 'triad')

Era, Supply, Source, Pc, Site = db.Era, db.Supply, db.Source, db.Pc, db.Site
SiteEra = db.SiteEra
HH = utils.HH

caches = {}

sess = None
try:
    sess = db.session()
    inv.getResponse().setContentType("text/csv")
    inv.getResponse().setHeader('Content-Disposition', 'attachment; filename="supplies_triad.csv"')

    year = inv.getInteger('year')
    pw = inv.getResponse().getWriter()
    year_finish = datetime.datetime(year, 4, 1, tzinfo=pytz.utc) - HH
    year_start = datetime.datetime(year, 4, 1, tzinfo=pytz.utc) - relativedelta(years=1)

    def triad_csv(supply_source):
        if supply_source is None or supply_source.mpan_core.startswith('99'):
            return [''] * 19

        duos.duos_vb(supply_source)
        triad.triad_bill(supply_source)

        bill = supply_source.supplier_bill
        values = [supply_source.mpan_core]
        for i in range(1, 4):
            triad_prefix = 'triad-actual-' + str(i)
            for suffix in ['-date', '-msp-kw', '-status', '-laf', '-gsp-kw']:
                #supply_source.pw.println("looking for " + triad_prefix + suffix)
                values.append(bill[triad_prefix + suffix])
        #supply_source.pw.println("values so far" + str(values))
    
        values += [bill['triad-actual-' + suf] for suf in ['gsp-kw', 'rate', 'gbp']]
        return values


    pw.println("Site Code, Site Name, Supply Name, Source, Generator Type, Import MPAN Core, Import T1 Date, Import T1 MSP kW, Import T1 Status, Import T1 LAF, Import T1 GSP kW, Import T2 Date, Import T2 MSP kW, Import T2 Status, Import T2 LAF, Import T2 GSP kW, Import T3 Date, Import T3 MSP kW, Import T3 Status, Import T3 LAF, Import T3 GSP kW, Import GSP kW, Import Rate GBP / kW, Import GBP, Export MPAN Core, Export T1 Date, Export T1 MSP kW, Export T1 Status, Export T1 LAF, Export T1 GSP kW, Export T2 Date, Export T2 MSP kW, Export T2 Status, Export T2 LAF, Export T2 GSP kW, Export T3 Date, Export T3 MSP kW, Export T3 Status, Export T3 LAF, Export T3 GSP kW, Export GSP kW, Export Rate GBP / kW, Export GBP")
    pw.flush()

    forecast_date = computer.forecast_date()
    eras = sess.query(Era).join(Supply).join(Source).join(Pc).filter(Era.start_date<=year_finish, or_(Era.finish_date==None, Era.finish_date>=year_finish), Source.code.in_(('net', 'gen-net')), Pc.code=='00').order_by(Supply.id)

    if inv.hasParameter('supply_id'):
        supply_id = inv.getLong('supply_id')
        eras = eras.filter(Supply.id==supply_id)

    for era in eras:
        site = sess.query(Site).join(SiteEra).filter(SiteEra.is_physical==True, SiteEra.era_id==era.id).one()
        supply = era.supply
        pw.print(site.code + ',"' + site.name + '","' + supply.name + '",' + supply.source.code)
        pw.flush()

        imp_mpan_core = era.imp_mpan_core
        if imp_mpan_core is None:
            imp_supply_source = None
        else:
            imp_supply_source = computer.SupplySource(sess, year_finish, year_finish, forecast_date, era, True, pw, caches)

        exp_mpan_core = era.exp_mpan_core
        if exp_mpan_core is None:
            exp_supply_source = None
        else:
            exp_supply_source = computer.SupplySource(sess, year_finish, year_finish, forecast_date, era, False, pw, caches)
        
        gen_type = supply.generator_type
        gen_type = '' if gen_type is None else gen_type.code
        #pw.println("imp csv" + str(triad_csv(imp_supply_source)))
        for value in [gen_type] + triad_csv(imp_supply_source) + triad_csv(exp_supply_source):
            pw.print(',"' + str(value) + '"')
        pw.println('')
        pw.flush()
    pw.close()
finally:
    if sess is not None:
        sess.close()