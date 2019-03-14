import traceback
import csv
from sqlalchemy.sql.expression import null
from werkzeug.exceptions import BadRequest
import requests
from itertools import chain
from chellow.models import Contract, Era, Supply, Source, Session, Party
from chellow.views import chellow_redirect
import chellow.dloads
import sys
import os
import threading
from flask import g


def content(user):
    sess = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            'ecoes_comparison.csv', user)
        f = open(running_name, mode='w', newline='')
        writer = csv.writer(f, lineterminator='\n')

        props = Contract.get_non_core_by_name(sess, 'configuration'). \
            make_properties()

        ECOES_KEY = 'ecoes'
        try:
            ecoes_props = props[ECOES_KEY]
        except KeyError:
            raise BadRequest(
                "The property " + ECOES_KEY +
                " cannot be found in the configuration properties.")

        for key in ('user_name', 'password', 'prefix'):
            try:
                ecoes_props[key]
            except KeyError:
                raise BadRequest(
                    "The property " + key + " cannot be found in the " +
                    "'ecoes' section of the configuration properties.")

        proxies = props.get('proxies', {})
        s = requests.Session()
        r = s.get(ecoes_props['prefix'], proxies=proxies)
        r = s.post(
            ecoes_props['prefix'], data={
                'Username': ecoes_props['user_name'],
                'Password': ecoes_props['password'],
                }, allow_redirects=False)

        mpans = [
            v for (v,) in chain(
                sess.query(Era.imp_mpan_core).join(Supply, Source).
                join(Supply.dno).filter(
                    Party.dno_code.notin_(('88', '99')),
                    Era.finish_date == null(), Source.code != '3rd-party',
                    Era.imp_mpan_core != null()).distinct().order_by(
                    Era.imp_mpan_core),
                sess.query(Era.exp_mpan_core).join(Supply, Source)
                .join(Supply.dno).filter(
                    Party.dno_code.notin_(('88', '99')),
                    Era.finish_date == null(), Source.code != '3rd-party',
                    Era.exp_mpan_core != null()).distinct().order_by(
                    Era.exp_mpan_core))]
        r = s.get(
            ecoes_props['prefix'] +
            'NonDomesticCustomer/ExportPortfolioMPANs?fileType=csv',
            proxies=proxies)

        writer.writerow(
            (
                "MPAN Core", "MPAN Core No Spaces", "ECOES PC", "Chellow PC",
                "ECOES MTC", "Chellow MTC", "ECOES LLFC", "Chellow LLFC",
                "ECOES SSC", "Chellow SSC", "ECOES Supplier",
                "Chellow Supplier", "ECOES DC", "Chellow DC", "ECOES MOP",
                "Chellow MOP", "ECOES GSP Group", "Chellow GSP Group",
                "ECOES MSN", "Chellow MSN", "ECOES Meter Type",
                "Chellow Meter Type", "Problem"))

        parser = iter(csv.reader(r.text.splitlines(True)))
        next(parser)  # Skip titles

        for values in parser:
            problem = ''

            ecoes_titles = [
                'mpan-core', 'address-line-1', 'address-line-2',
                'address-line-3', 'address-line-4', 'address-line-5',
                'address-line-6', 'address-line-7', 'address-line-8',
                'address-line-9', 'post-code', 'supplier', 'registration-from',
                'mtc', 'mtc-date', 'llfc', 'llfc-from', 'pc', 'ssc',
                'measurement-class', 'energisation-status', 'da', 'dc', 'mop',
                'mop-appoint-date', 'gsp-group', 'gsp-effective-from', 'dno',
                'msn', 'meter-install-date', 'meter-type', 'map-id']

            ecoes = dict(zip(ecoes_titles, values))

            mpan_spaces = ' '.join(
                (
                    ecoes['mpan-core'][:2], ecoes['mpan-core'][2:6],
                    ecoes['mpan-core'][6:10], ecoes['mpan-core'][-3:]))

            ecoes_energisation_status = ecoes['energisation-status']
            disconnected = ecoes_energisation_status == ''
            current_chell = mpan_spaces in mpans

            if disconnected and current_chell:
                problem += "Disconnected in ECOES, but current in Chellow. "
            elif not disconnected and not current_chell:
                if ecoes_energisation_status == 'D':
                    st = "de-energised"
                else:
                    st = "energised"
                problem += "In ECOES (as " + st + ") but not current " + \
                    "in Chellow. "

            if current_chell:
                mpans.remove(mpan_spaces)
                supply = Supply.get_by_mpan_core(sess, mpan_spaces)
                era = supply.find_era_at(sess, None)
                if era.imp_mpan_core == mpan_spaces:
                    supplier_contract = era.imp_supplier_contract
                    llfc = era.imp_llfc
                else:
                    supplier_contract = era.exp_supplier_contract
                    llfc = era.exp_llfc

                chellow_pc = era.pc.code
                try:
                    if int(ecoes['pc']) != int(chellow_pc):
                        problem += "The PCs don't match. "
                except ValueError:
                    problem += "Can't parse the PC. "

                chellow_mtc = era.mtc.code
                try:
                    if int(ecoes['mtc']) != int(chellow_mtc):
                        problem += "The MTCs don't match. "
                except ValueError:
                    problem += "Can't parse the MTC. "

                chellow_llfc = llfc.code
                try:
                    if int(ecoes['llfc']) != int(chellow_llfc):
                        problem += "The LLFCs don't match. "
                except ValueError:
                    problem += "Can't parse the LLFC. "

                chellow_ssc = era.ssc
                if chellow_ssc is None:
                    chellow_ssc = ''
                    chellow_ssc_int = None
                else:
                    chellow_ssc = chellow_ssc.code
                    chellow_ssc_int = int(chellow_ssc)

                if len(ecoes['ssc']) > 0:
                    ecoes_ssc_int = int(ecoes['ssc'])
                else:
                    ecoes_ssc_int = None

                if ecoes_ssc_int != chellow_ssc_int and not (
                        ecoes_ssc_int is None and chellow_ssc_int is None):
                    problem += "The SSCs don't match. "

                chellow_supplier = supplier_contract.party.participant.code
                if chellow_supplier != ecoes['supplier']:
                    problem += "The supplier codes don't match. "

                dc_contract = era.dc_contract
                if dc_contract is None:
                    chellow_dc = ''
                else:
                    chellow_dc = dc_contract.party.participant.code

                if chellow_dc != ecoes['dc']:
                    problem += "The DC codes don't match. "

                mop_contract = era.mop_contract
                if mop_contract is None:
                    chellow_mop = ''
                else:
                    chellow_mop = mop_contract.party.participant.code

                if chellow_mop != ecoes['mop']:
                    problem += "The MOP codes don't match. "

                chellow_gsp_group = supply.gsp_group.code
                if chellow_gsp_group != ecoes['gsp-group']:
                    problem += "The GSP group codes don't match. "

                chellow_msn = era.msn
                if chellow_msn is None:
                    chellow_msn = ''
                if chellow_msn != ecoes['msn']:
                    problem += "The meter serial numbers don't match. "

                chellow_meter_type = _meter_type(era)

                if chellow_meter_type != ecoes['meter-type']:
                    problem += "The meter types don't match. See " \
                        "http://dtc.mrasco.com/DataItem.aspx?" \
                        "ItemCounter=0483 "
            else:
                chellow_pc = ''
                chellow_mtc = ''
                chellow_llfc = ''
                chellow_ssc = ''
                chellow_supplier = ''
                chellow_dc = ''
                chellow_mop = ''
                chellow_gsp_group = ''
                chellow_msn = ''
                chellow_meter_type = ''

            if len(problem) > 0:
                writer.writerow(
                    [
                        mpan_spaces, ecoes['mpan-core'], ecoes['pc'],
                        chellow_pc, ecoes['mtc'], chellow_mtc,
                        ecoes['llfc'], chellow_llfc, ecoes['ssc'],
                        chellow_ssc, ecoes['supplier'], chellow_supplier,
                        ecoes['dc'], chellow_dc, ecoes['mop'], chellow_mop,
                        ecoes['gsp-group'], chellow_gsp_group,
                        ecoes['msn'], chellow_msn, ecoes['meter-type'],
                        chellow_meter_type, problem])
            sess.expunge_all()

        for mpan_core in mpans:
            supply = Supply.get_by_mpan_core(sess, mpan_core)
            era = supply.find_era_at(sess, None)
            if era.imp_mpan_core == mpan_core:
                supplier_contract = era.imp_supplier_contract
                llfc = era.imp_llfc
            else:
                supplier_contract = era.exp_supplier_contract
                llfc = era.exp_llfc

            ssc = '' if era.ssc is None else era.ssc.code

            dc_contract = era.dc_contract
            if dc_contract is None:
                dc = ''
            else:
                dc = dc_contract.party.participant.code

            mop_contract = era.mop_contract
            if mop_contract is None:
                mop = ''
            else:
                mop = mop_contract.party.participant.code

            msn = '' if era.msn is None else era.msn

            meter_type = _meter_type(era)

            writer.writerow(
                [
                    mpan_core, mpan_core.replace(' ', ''), '', era.pc.code,
                    '', era.mtc.code, '', llfc.code, '', ssc, '',
                    supplier_contract.party.participant.code, '', dc, '',
                    mop, '', supply.gsp_group.code, '', msn, '',
                    meter_type, 'In Chellow, but not in ECOES.'])
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


def _meter_type(era):
    props = era.props
    try:
        return props['meter_type']
    except KeyError:
        if era.pc.code == '00':
            return 'H'
        elif len(era.channels) > 0:
            return 'RCAMR'
        elif era.mtc.meter_type.code in ['UM', 'PH']:
            return ''
        else:
            return 'N'


def do_get(sess):
    threading.Thread(target=content, args=(g.user,)).start()
    return chellow_redirect("/downloads", 303)
