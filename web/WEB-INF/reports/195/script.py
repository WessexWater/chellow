from net.sf.chellow.monad import Monad
from java.lang import System
from org.apache.http.protocol import HTTP
from org.apache.http.client.entity import UrlEncodedFormEntity
from org.apache.http.util import EntityUtils
from org.apache.http import HttpHost
from org.apache.http.conn.params import ConnRoutePNames
from org.apache.http.impl.client import DefaultHttpClient
from org.apache.http.message import BasicNameValuePair
from org.apache.http.client.methods import HttpGet, HttpPost

import csv
import urllib
import StringIO

Monad.getUtils()['imprt'](globals(), {
        'db': ['Source', 'Era', 'Contract', 'HhDatum', 'Site', 'Supply', 'set_read_write', 'session'], 
        'utils': ['UserException', 'HH', 'form_date'],
        'templater': ['render']})

sess = None
try:
    sess = session()

    inv.getResponse().setContentType("text/csv")
    inv.getResponse().setHeader('Content-Disposition', 'attachment; filename="output.csv"')
    pw = inv.getResponse().getWriter()

    props = Contract.get_non_core_by_name(sess, 'configuration').make_properties()

    ECOES_USER_NAME_KEY = 'ecoes.user.name'
    try:
        user_name = props[ECOES_USER_NAME_KEY]
    except KeyError:
        raise UserException("The property " + ECOES_USER_NAME_KEY + " cannot be found in the configuration properties.")

    ECOES_PASSWORD_KEY = 'ecoes.password'
    try:
        password = props[ECOES_PASSWORD_KEY]
    except KeyError:
        raise UserException("The property " + ECOES_PASSWORD_KEY + " cannot be found in the configuration properties.")

    PROXY_HOST_KEY = 'proxy.host'
    PROXY_PORT_KEY = 'proxy.port'

    proxy_host = props.get(PROXY_HOST_KEY)

    client = DefaultHttpClient()
    if proxy_host is not None:
        proxy_port = props.get(PROXY_PORT_KEY)
        if proxy_port is None:
            raise UserException("The property " + PROXY_HOST_KEY + " is set, but the property " + PROXY_PORT_KEY + " is not.")

        proxy = HttpHost(proxy_host, int(proxy_port), "http")
        client.getParams().setParameter(ConnRoutePNames.DEFAULT_PROXY, proxy)

    http_get = HttpGet('http://www.ecoes.co.uk/')
    response = client.execute(http_get)
    EntityUtils.consume(response.getEntity())
    http_post = HttpPost("https://www.ecoes.co.uk/login.asp")
    http_post.setEntity(UrlEncodedFormEntity([BasicNameValuePair("username", user_name), BasicNameValuePair("password", password), BasicNameValuePair('beenHereBefore', '1'), BasicNameValuePair('forceLogout', '1')], HTTP.UTF_8))
    response = client.execute(http_post)
    location_header = response.getFirstHeader('Location')
    location = location_header.getValue()
    EntityUtils.consume(response.getEntity())
    guid = urllib.quote_plus(location[19:])

    mpans = sess.query(Era.imp_mpan_core).join(Supply, Source).join(Supply.dno_contract).filter(Contract.name!='99', Era.finish_date==None, Source.code!='3rd-party', Era.imp_mpan_core!=None).distinct().order_by(Era.imp_mpan_core).all() + sess.query(Era.exp_mpan_core).join(Supply, Source).join(Supply.dno_contract).filter(Contract.name!='99', Era.finish_date==None, Source.code!='3rd-party', Era.exp_mpan_core!=None).distinct().order_by(Era.exp_mpan_core).all()

    mpans = [v[0] for v in mpans]

    http_get = HttpGet('http://www.ecoes.co.uk/saveportfolioMpans.asp?guid=' + guid)

    pw.print("MPAN Core,MPAN Core No Spaces,ECOES PC,Chellow PC,ECOES MTC,Chellow MTC,ECOES LLFC,Chellow LLFC,ECOES SSC,Chellow SSC,ECOES Supplier, Chellow Supplier,ECOES DC,Chellow DC,ECOES MOP,Chellow MOP,ECOES GSP Group,Chellow GSP Group,ECOES MSN, Chellow MSN,ECOES Meter Type,Chellow Meter Type,Problem")
    pw.flush()

    entity = client.execute(http_get).getEntity()
    csv_is = entity.getContent()
    f = StringIO.StringIO()
    bt = csv_is.read()
    while bt != -1:
        f.write(chr(bt))
        bt = csv_is.read()
    f.seek(0)
    parser = iter(csv.reader(f))
    parser.next()  # Skip titles

    for values in parser:
        problem = ''

        ecoes_titles = ['mpan-core', 'address-line-1', 'address-line-2', 'address-line-3', 'address-line-4', 'address-line-5', 'address-line-6', 'address-line-7', 'address-line-8', 'address-line-9', 'post-code', 'supplier', 'registration-from', 'mtc', 'mtc-date', 'llfc', 'llfc-from', 'pc', 'ssc', 'measurement-class', 'energisation-status', 'da', 'dc', 'mop', 'mop-appoint-date', 'gsp-group', 'gsp-effective-from', 'dno', 'msn', 'meter-install-date', 'meter-type', 'map-id']

        ecoes = dict(zip(ecoes_titles, values))

        mpan_spaces = ecoes['mpan-core'][:2] + ' ' + ecoes['mpan-core'][2:6] + ' ' + ecoes['mpan-core'][6:10] + ' ' + ecoes['mpan-core'][-3:]

        disconnected = len(ecoes['supplier']) == 0
        current_chell = mpan_spaces in mpans

        if disconnected and current_chell:
            problem += "Disconnected in ECOES, but current in Chellow. "
        elif not disconnected and not current_chell:
            problem += "In ECOES (energized or de-energized), but not current in Chellow. "

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

            ecoes_ssc_int = int(ecoes['ssc']) if len(ecoes['ssc']) > 0 else None

            if ecoes_ssc_int != chellow_ssc_int and not (ecoes_ssc_int is None and chellow_ssc_int is None):
                problem += "The SSCs don't match. "

            chellow_supplier = supplier_contract.party.participant.code
            if chellow_supplier != ecoes['supplier']:
                problem += "The supplier codes don't match. "

            hhdc_contract = era.hhdc_contract
            if hhdc_contract is None:
                chellow_dc = ''
            else:
                chellow_dc = hhdc_contract.party.participant.code

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

            if chellow_pc == '00':
                chellow_meter_type = 'H'
            elif len(era.channels) > 0:
                chellow_meter_type = 'RCAMR'
            elif era.mtc.meter_type.code in ['UM', 'PH']:
                chellow_meter_type = ''
            else:
                chellow_meter_type = 'N'

            if chellow_meter_type != ecoes['meter-type']:
                problem += "The meter types don't match. See http://dtc.mrasco.com/DataItem.aspx?ItemCounter=0483 "        
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
            pw.print('\n' + ','.join('"' + str(val) + '"' for val in [mpan_spaces, ecoes['mpan-core'], ecoes['pc'], chellow_pc, ecoes['mtc'], chellow_mtc, ecoes['llfc'], chellow_llfc, ecoes['ssc'], chellow_ssc, ecoes['supplier'], chellow_supplier, ecoes['dc'], chellow_dc, ecoes['mop'], chellow_mop, ecoes['gsp-group'], chellow_gsp_group, ecoes['msn'], chellow_msn, ecoes['meter-type'], chellow_meter_type, problem]))
        else:
            pw.print(' ')
        pw.flush()
        sess.expunge_all()

    EntityUtils.consume(entity)
    pw.println(str(mpans))
    for mpan_core in mpans:
        supply = Supply.get_by_mpan_core(sess, mpan_core)
        era = supply.find_era_at(sess, None)
        if era.imp_mpan_core == mpan_core:
            supplier_contract = era.imp_supplier_contract
            llfc = era.imp_llfc
        else:
            supplier_contract = era.exp_supplier_contract
            llfc = era.exp_llfc

        ssc = era.ssc
        ssc = '' if ssc is None else ssc.code

        hhdc_contract = era.hhdc_contract
        if hhdc_contract is None:
            dc = ''
        else:
            dc = hhdc_contract.party.participant.code

        mop_contract = era.mop_contract
        if mop_contract is None:
            mop = ''
        else:
            mop = mop_contract.party.participant.code

        msn = era.msn
        if msn is None:
            msn = ''

        if era.pc.code == '00':
            meter_type = 'H'
        else:
            if len(era.channels) > 0:
                meter_type = 'RCAMR'
            else:
                meter_type = 'N'

        pw.print('\n' + ','.join('"' + str(val) + '"' for val in [mpan_core, mpan_core.replace(' ', ''), '', era.pc.code, '', era.mtc.code, '', llfc.code, '', ssc, '', supplier_contract.party.participant.code, '', dc, '', mop, '', supply.gsp_group.code, '', msn, '', meter_type, 'In Chellow, but not in ECOES.']))
        pw.flush()
    pw.close()
finally:
    if sess is not None:
        sess.close()