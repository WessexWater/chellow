import sys
import pg8000
import os
import datetime
import pytz

'''
con = pg8000.connect(
    user=username, password=password, database=database, host=hostname)
'''
pg8000.paramstyle = 'named'
con = pg8000.connect(
    user='postgres', password='postgres', database='chellow')
root_path = '/home/tlocke/workspace/chellow/web/WEB-INF'
cursor = con.cursor()

def set_read_write():
    cursor.execute("rollback")
    cursor.execute("set transaction isolation level serializable read write")

def read_file(pth, fname, attr):
        f = open(os.path.join(pth, fname), 'r')
        contents = f.read()
        f.close()
        if attr is None:
            return eval(contents)
        else:
            return {attr: contents}

reports_path = os.path.join(root_path, 'reports')
for report_id_str in os.listdir(reports_path):
    report_path = os.path.join(reports_path, report_id_str)
    params = {'id': int(report_id_str)}
    set_read_write()
    for fname, attr in (
            ('script.py', 'script'),
            ('template.txt', 'template'),
            ('meta.py', None)):
        params.update(read_file(report_path, fname, attr))
    cursor.execute(
        "insert into report (id, name, script, template) "
        "  values (:id, :name, :script, :template)", params)
    con.commit()

for path_name, role_code in (
        ('non_core_contracts', 'Z'),
        ('dno_contracts', 'R')):
    contracts_path = os.path.join(root_path, path_name)
    cursor.execute(
        "select id from market_role where code = :code", {'code': role_code})
    market_role_id = cursor.fetchone()[0]

    for contract_name in sorted(os.listdir(contracts_path)):
        contract_path = os.path.join(contracts_path, contract_name)
        params = {'role_id': market_role_id, 'name': contract_name}
        for fname, attr in (
                ('charge_script.py', 'charge_script'),
                ('meta.py', None),
                ('properties.py', 'properties'),
                ('state.py', 'state')):
            params.update(read_file(contract_path, fname, attr))
        cursor.execute(
            "select party.id "
            "  from party "
            "    join participant on (party.participant_id = participant.id) "
            "    join market_role on (party.market_role_id = market_role.id) "
            "  where participant.code = :code "
            "  and market_role.code = :market_role_code",
            {
                'code': params['participant_code'],
                'market_role_code': role_code})
        params['party_id'] = cursor.fetchone()[0]
        del params['participant_code']
        params['market_role_id'] = market_role_id
        set_read_write()
        cursor.execute(
            "insert into contract (market_role_id, is_core, name, "
            "  charge_script, properties, state, start_rate_script_id, "
            "  finish_rate_script_id, party_id) "
            "  values (:market_role_id, :is_core, :name, :charge_script, "
            "  :properties, :state, null, null, :party_id) returning id",
            params)
        contract_id = cursor.fetchone()[0]

        rscripts_path = os.path.join(contract_path, 'rate_scripts')
        for rscript_fname in sorted(os.listdir(rscripts_path)):
            start_str, finish_str = rscript_fname.split('.')[0].split('_')
            start_date = datetime.datetime.strptime(
                start_str, "%Y%m%d%H%M").replace(tzinfo=pytz.utc)
            if finish_str == 'ongoing':
                finish_date = None
            else:
                finish_date = datetime.datetime.strptime(
                    finish_str, "%Y%m%d%H%M").replace(tzinfo=pytz.utc)
            rparams = {
                'start_date': start_date,
                'finish_date': finish_date,
                'contract_id': contract_id}
            rparams.update(read_file(rscripts_path, rscript_fname, 'script'))
            cursor.execute(
                "insert into rate_script " +
                "  (contract_id, start_date, finish_date, script) "
                "  values (:contract_id, :start_date, :finish_date, :script)",
                rparams)
        # Assign first rate script
        cursor.execute(
            "select id from rate_script "
            "where contract_id = :contract_id order by start_date",
            {'contract_id': contract_id})
        scripts = cursor.fetchall()
        cursor.execute(
            "update contract "
            "  set start_rate_script_id = :start_rate_script_id, " +
            "    finish_rate_script_id = :finish_rate_script_id " +
            "  where id = :id",
            {
                'id': contract_id,
                'start_rate_script_id': scripts[0][0],
                'finish_rate_script_id': scripts[-1][0]})
        con.commit()
con.close()
