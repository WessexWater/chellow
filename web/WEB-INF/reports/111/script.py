from net.sf.chellow.monad import Monad
import collections
import operator
import pytz
import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_
import traceback

Monad.getUtils()['impt'](globals(), 'templater', 'db', 'computer', 'utils')

HH, hh_before, hh_format = utils.HH, utils.hh_before, utils.hh_format
Batch, Bill, Era, Site = db.Batch, db.Bill, db.Era, db.Site
SiteEra = db.SiteEra
caches = {}

forecast_date = datetime.datetime.max.replace(tzinfo=pytz.utc)

if inv.hasParameter('batch_id'):
    batch_id = inv.getLong("batch_id")
    bill_id = None
elif inv.hasParameter('bill_id'):
    bill_id = inv.getLong("bill_id")
    batch_id = None

def content():
    sess = None
    try:
        sess = db.session()

        if batch_id is not None:
            batch = Batch.get_by_id(sess, batch_id)
            bills = sess.query(Bill).filter(
                Bill.batch_id == batch.id).order_by(Bill.reference)
        elif bill_id is not None:
            bill_id = inv.getLong("bill_id")
            bill = Bill.get_by_id(sess, bill_id)
            bills = sess.query(Bill).filter(Bill.id == bill.id)
            batch = bill.batch
        else:
            raise UserException("The bill check needs a batch_id or bill_id.")

        contract = batch.contract
        market_role_code = contract.market_role.code

        vbf = computer.contract_func(caches, contract, 'virtual_bill', None)
        if vbf is None:
            raise UserException(
                'The contract ' + contract.name +
                " doesn't have a function virtual_bill.")

        virtual_bill_titles_func = computer.contract_func(
            caches, contract, 'virtual_bill_titles', None)
        if virtual_bill_titles_func is None:
            raise UserException(
                'The contract ' + contract.name +
                " doesn't have a function virtual_bill_titles.")
        virtual_bill_titles = virtual_bill_titles_func()

        yield "batch,bill-reference,bill-type,bill-kwh,bill-net-gbp," + \
            "bill-vat-gbp, bill-start-date,bill-finish-date," + \
            "bill-mpan-core,site-code,site-name,covered-from,covered-to," + \
            "covered-bills," + \
            ','.join(
                    'covered-' + val + ',virtual-' + val + (
                        ',difference-' +
                        val if val.endswith('-gbp') else '')
                    for val in virtual_bill_titles) + '\n'

        for bill in bills:
            problem = ''
            supply = bill.supply

            read_dict = {}
            for read in bill.reads:
                gen_start = read.present_date.replace(hour=0).replace(minute=0)
                gen_finish = gen_start + relativedelta(days=1) - HH
                msn_match = False
                read_msn = read.msn
                for read_era in supply.find_eras(sess, gen_start, gen_finish):
                    if read_msn == read_era.msn:
                        msn_match = True
                        break

                if not msn_match:
                    problem += "The MSN " + read_msn + \
                        " of the register read " + str(read.id) + \
                        " doesn't match the MSN of the era."

                for dt, type in [
                        (read.present_date, read.present_type),
                        (read.previous_date, read.previous_type)]:
                    key = str(dt) + "-" + read.msn
                    try:
                        if type != read_dict[key]:
                            problem += " Reads taken on " + str(dt) + \
                                " have differing read types."
                    except KeyError:
                        read_dict[key] = type        

            bill_start = bill.start_date
            bill_finish = bill.finish_date

            era = supply.find_era_at(sess, bill.finish_date)
            if era is None:
                yield "\n,,,,,,,,,,Extraordinary! There isn't a era for " + \
                    "this bill!"
                continue

            yield ','.join('"' + str(val) + '"' for val in [batch.reference, bill.reference, bill.bill_type.code, bill.kwh, bill.net, bill.vat, hh_format(bill_start), hh_format(bill_finish), era.imp_mpan_core]) + ","

            msn = era.msn

            covered_start = bill_start
            covered_finish = bill_finish
            covered_bill_ids = []
            covered_bdown = {'sum-msp-kwh': 0, 'net-gbp': 0, 'vat-gbp': 0}
            covered_primary_bill = None
            enlarged = True

            while enlarged:
                enlarged = False
                for covered_bill in sess.query(Bill).filter(
                        Bill.supply_id == supply.id,
                        Bill.start_date <= covered_finish,
                        Bill.finish_date>=covered_start).order_by(
                        Bill.issue_date.desc(), Bill.start_date):
                    if market_role_code != \
                            covered_bill.batch.contract.market_role.code:
                        continue

                    if covered_primary_bill is None and \
                            len(covered_bill.reads) > 0:
                        covered_primary_bill = covered_bill
                    if covered_bill.start_date < covered_start:
                        covered_start = covered_bill.start_date
                        enlarged = True
                        break
                    if covered_bill.finish_date > covered_finish:
                        covered_finish = covered_bill.finish_date
                        enlarged = True
                        break

            for covered_bill in sess.query(Bill).filter(
                    Bill.supply_id == supply.id,
                    Bill.start_date <= covered_finish,
                    Bill.finish_date >= covered_start).order_by(
                    Bill.issue_date.desc(), Bill.start_date):
                if market_role_code != \
                        covered_bill.batch.contract.market_role.code:
                    continue
                covered_bill_ids.append(covered_bill.id)
                covered_bdown['net-gbp'] += float(covered_bill.net)
                covered_bdown['vat-gbp'] += float(covered_bill.vat)
                covered_bdown['sum-msp-kwh'] += float(covered_bill.kwh)
                if len(covered_bill.breakdown) > 0:
                    covered_rates = collections.defaultdict(set)
                    for k, v in eval(covered_bill.breakdown, {}).iteritems():

                        if k.endswith('rate'):
                            covered_rates[k].add(v)
                        elif k != 'raw-lines':
                            try:
                                covered_bdown[k] += v
                            except KeyError:
                                covered_bdown[k] = v
                            except TypeError, detail:
                                raise UserException(
                                    "For key " + str(k) + " the value " +
                                    str(v) +
                                    " can't be added to the existing value " +
                                    str(covered_bdown[k]) + ". " + str(detail))
                    for k, v in covered_rates.iteritems():
                        covered_bdown[k] = v.pop() if len(v) == 1 else None

            virtual_bill = {}

            for era in sess.query(Era).filter(
                    Era.supply_id == supply.id, Era.imp_mpan_core != None,
                    Era.start_date <= covered_finish,
                    or_(
                        Era.finish_date == None,
                        Era.finish_date>=covered_start)).distinct():
                site = sess.query(Site).join(SiteEra).filter(
                    SiteEra.is_physical == True,
                    SiteEra.era_id == era.id).one()

                if covered_start > era.start_date:
                    chunk_start = covered_start
                else:
                    chunk_start = era.start_date

                if hh_before(covered_finish, era.finish_date):
                    chunk_finish = covered_finish
                else:
                    chunk_finish = era.finish_date

                data_source = computer.SupplySource(
                    sess, chunk_start, chunk_finish, forecast_date, era, True,
                    None, caches, covered_primary_bill)
                vbf(data_source)

                if market_role_code == 'X':
                    vb = data_source.supplier_bill
                elif market_role_code == 'C':
                    vb = data_source.dc_bill
                elif market_role_code == 'M':
                    vb = data_source.mop_bill
                else:
                    raise UserException("Odd market role.")

                for k, v in vb.iteritems():
                    try:
                        virtual_bill[k] += v
                    except KeyError:
                        virtual_bill[k] = v
                    except TypeError, detail:
                        raise UserException(
                            "For key " + str(k) + " and value " + str(v) +
                            ". " + str(detail))

            values = [
                site.code, site.name, hh_format(covered_start),
                hh_format(covered_finish),
                ';'.join(str(id).replace(',', '') for id in covered_bill_ids)]
            for title in virtual_bill_titles:
                try:
                    cov_val = covered_bdown[title]
                    values.append(cov_val)
                    del covered_bdown[title]
                except KeyError:
                    cov_val = None
                    values.append('')

                try:
                    virt_val = virtual_bill[title]
                    values.append(virt_val)
                    del virtual_bill[title]
                except KeyError:
                    virt_val = None
                    values.append('')

                if title.endswith('-gbp'):
                    if all(isinstance(val, (int, float)) for val in [
                            cov_val, virt_val]):
                        values.append(cov_val - virt_val)
                    else:
                        values.append('')

            for title in sorted(virtual_bill.keys()):
                values += ['virtual-' + title, virtual_bill[title]]
                if title in covered_bdown:
                    values += ['covered-' + title, covered_bdown[title]]
                else:
                    values += ['','']

            yield ','.join('"' + str(value) + '"' for value in values) + '\n' 
    except:
        yield traceback.format_exc()
    finally:
        if sess is not None:
            sess.close()

utils.send_response(inv, content, file_name='bill_check.csv')
