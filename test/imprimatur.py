[
    {
        'name': "View users' page",
        'port': '8080',
        'host': 'localhost',
        'path': '/users',
        'auth': ('admin@example.com', 'admin'),
        'status_code': 200,
        'regexes': [
            r'"/style"']},
    {
        'name': "Manipulating users",
        'path': '/users',
        'method': 'post',
        'data': {
            'email_address': "watkin\\s@example.com",
            'user_role_code': "editor",
            'password': "alan"},
        'status_code': 303,
        'tries': {},
        'regexes': [
            r"http://localhost:8080/users/2"]},
    {
        'path': '/users',
        'method': 'post',
        'data': {
            'email_address': "lydgate@localhost",
            'user_role_code': "editor",
            'password': "science"},
        'status_code': 303,
        'regexes': [
            r"/users/3"]},

    {
        'path': '/users/3',
        'regexes': [
            r'<form method="post" action="">\s*'
            r'<fieldset>\s*'
            r'<input type="hidden" name="change_password">\s*',
            r'<form action="">\s*'
            r'<fieldset>\s*'
            r'<input type="hidden" name="Delete this user">\s*'],
        'status_code': 200},

    {
        'name': "Check that a duplicate email gives a proper error message",
        'path': '/users',
        'method': 'post',
        'data': {
            'email_address': "lydgate@localhost",
            'user_role_code': "editor",
            'password': "science"},
        'regexes': [
            r"already a user with this email address"],
        'status_code': 400},

    # Test that we're able to change the password
    {
        'path': '/users/3',
        'method': 'post',
        'data': {
            'current_password': "science",
            'new_password': "rosamund",
            'confirm_new_password': "rosamund"},
        'regexes': [
            r'/users/3'],
        'status_code': 303},

    {
        'name': "Test that we can change the role",
        'path': '/users/3',
        'method': 'post',
        'data': {
            'email_address': "mary-ann-evans@example.com",
            'user_role_code': "editor"},
        'status_code': 303},

    {
        'name': " ...and change it back",
        'path': '/users/3',
        'method': 'post',
        'data': {
            'email_address': "lydgate@localhost",
            'user_role_code': "editor"},
        'status_code': 303},
    {
        'name': "Check that invalid email address gives unauthorized.",
        'path': '/chellow/reports/315/output/',
        'method': 'post',
        'auth': ('godel', 'dancer'),
        'data': {
            'participant_id': "222",

            # HYDE
            'name': "Non half-hourlies 2007",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'has_finished': "false"},
        'status_code': 401},

    {
        'name': "Insert local report",
        'auth': ('watkin\\s@example.com', 'alan'),
        'path': '/local_reports',
        'method': 'post',
        'data': {
            'name': "Minority Report"},
        'status_code': 303,
        'regexes': [
            r"/local_reports/1"]},

    {
        'name': "Delete a user",
        'path': '/users/3',
        'method': 'post',
        'data': {
            'delete': 'Delete'},
        'status_code': 303,
        'regexes': [
            r'/users"']},
    {
        'name': "View local reports",
        'path': '/local_reports',
        'status_code': 200,
        'regexes': [
            r"Minority Report",
            r'<a href="/local_reports/1">View</a>']},
    {
        'path': '/local_reports/1',
        'status_code': 200,
        'regexes': [
            r"Minority Report"]},
    {
        'name': "Check duplicate report name gives good error message",
        'path': '/local_reports',
        'method': 'post',
        'data': {
            'name': "Minority Report"},
        'status_code': 400,
        'regexes': [
            r"There's already a report with that name\."]},

    {
        'name': "General import of sites",
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/sites.csv'},
        'status_code': 303,
        'regexes': [
            r"/general_imports/0"]},

    {
        'path': '/general_imports/0',
        'tries': {'max': 10, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"The file has been imported successfully\."]},

    {
        'name': "Duplicates",
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/sites.csv'},
        'status_code': 303,
        'regexes': [
            r"/general_imports/1"]},
    {
        'path': '/general_imports/1',
        'tries': {'max': 10, 'period': 1},
        'regexes': [
            r"There&#39;s already a site with this code\."],
        'status_code': 200},

    {
        'name': "Delete a site",
        'path': '/sites/2/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'status_code': 303},

    {
        'name': "Show and add a site",
        'path': '/sites/add',
        'regexes': [
            r"Add a site"],
        'status_code': 200},
    {
        'path': '/sites/add',
        'method': 'post',
        'data': {
            'code': "CH017",
            'name': "Parbola"},
        'status_code': 303},

    {
        'name': "BSUoS",
        'path': '/non_core_contracts/3/edit',
        'method': 'post',
        'data': {
            'name': 'system_price',
            'properties': """
{
    'enabled': True,
    'url': 'http://127.0.0.1:8080/nationalgrid/sf_bsuos.xls'}
"""},
        'status_code': 303},
    {
        'name': "Do an 'import now'",
        'path': '/non_core_contracts/3/auto_importer',
        'method': 'post',
        'regexes': [
            '/non_core_contracts/3/auto_importer'],
        'status_code': 303},
    {
        'name': 'BSUoS',
        'path': '/non_core_contracts/3/auto_importer',
        'tries': {'max': 40, 'period': 1},
        'regexes': [
            r"Added new rate script\."],
        'status_code': 200},

    {
        'name': "Set configuration properties",
        'path': '/non_core_contracts/5/edit',
        'method': 'post',
        'data': {
            'properties': """
{
    'ips': {'127.0.0.1': 'implicit-user@localhost'},
    'site_links': [
        {'name': 'Google Maps', 'href': 'https://maps.google.com/maps?q='}],
    'elexonportal_scripting_key': 'xxx',
    'background_colour': 'aquamarine'}
"""},
        'status_code': 303},

    {
        'name': "Set up TLM downloader",
        'path': '/non_core_contracts/9/edit',
        'method': 'post',
        'data': {
            'properties': """
{
            'enabled': True,
            'url': 'http://127.0.0.1:8080/elexonportal/',
            'limit': True}
"""},
        'status_code': 303},
    {
        'name': "Do an 'import now' on TLM.",
        'path': '/non_core_contracts/9/auto_importer',
        'method': 'post',
        'data': {
            'now': 'Now'},
        'status_code': 303},
    {
        'name': "Check that an TLM import has happened.",
        'path': '/non_core_contracts/9/auto_importer',
        'tries': {},
        'regexes': [
            r"Added new rate script\."],
        'status_code': 200},

    {
        'name': "HHDC contracts",
        'path': '/hhdc_contracts/add',
        'method': 'post',
        'data': {
            'participant_id': "61",  # DASL
            'name': "HH contract",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'has_finished': "false"},
        'status_code': 303,
        'regexes': [
            r"/hhdc_contracts/29"]},

    {
        'name': "Update Contract",
        'path': '/hhdc_contracts/29/edit',
        'method': 'post',
        'data': {
            'party_id': "97",  # DASL HHDC
            'name': "HH contract",
            'charge_script': """
def virtual_bill_titles():
    return ['net-gbp', 'problem']

def virtual_bill(ds):
    bill = ds.dc_bill
    for hh in ds.hh_data:
        if hh['utc-is-month-end']:
            bill['net-gbp'] += 10
""",
            'properties': "{'mpan_map': {'maptest': '2292056799106'}}"},
        'status_code': 303},

    {
        'path': '/hhdc_contracts/29',
        'regexes': [
            r'HH contract\s*\[<a href="/hhdc_contracts/29/edit">edit</a>\]',
            r'<form action="/reports/81">'],
        'status_code': 200},

    {
        'name': "Check that we can see HHDC rate script okay. Contract 29.",
        'path': '/hhdc_rate_scripts/95',

        # Check that 'has_finished' field is there
        'regexes': [
            r'HH contract'],
        'status_code': 200},

    {
        'name': "Check that we can see the edit view of the HHDC rate "
        "script okay. Contract 29.",
        'path': '/hhdc_rate_scripts/95/edit',

        # Check that 'has_finished' field is there
        'regexes': [
            r"has_finished",

            # Check the hhdc_rate_script_id for update is there
            
            r'<input type="hidden" name="hhdc_rate_script_id" value="95">\s*'],
        'status_code': 200},

    {
        'name': "Check that we can update an HHDC rate script okay",
        'path': '/hhdc_rate_scripts/95/edit',
        'method': 'post',
        'data': {
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'script': "{}"},
        'status_code': 303},

    {
        'name': "Add another HHDC contract",
        'path': '/hhdc_contracts/add',
        'method': 'post',
        'data': {
            'participant_id': "61",  # DASL
            'name': "Dynamat data",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00"},
        'status_code': 303,
        'regexes': [
            r"/hhdc_contracts/30"]},

    {
        'name': "Update the newly added HHDC",
        'path': '/hhdc_contracts/30/edit',
        'method': 'post',
        'data': {
            'party_id': "97",  # DASL HHDC
            'name': "Dynamat data",
            'charge_script': """
def virtual_bill_titles():
    return ['net-gbp', 'problem']

def virtual_bill(ds):
    bill = ds.dc_bill
    for hh in ds.hh_data:
        if hh['utc-is-month-end']:
            bill['net-gbp'] += 7
""",
            'properties': '{"props": 1}'},
        'status_code': 303},

    {
        'name': "Update state of Dynamat HHDC",
        'path': '/hhdc_contracts/30/edit',
        'method': 'post',
        'data': {
            'update_state': "",
            'state': '{"stat": 2}'},
        'status_code': 303},

    {
        'name': "View edit Dynamat HHDC",
        'path': '/hhdc_contracts/30/edit',
        'status_code': 200,
        'regexes': [
            r'<textarea name="charge_script" rows="40" cols="80">\s*'
            'def virtual_bill_title',
            r'<textarea name="properties" rows="40" '
            'cols="80">\{&#34;props&#34;: 1\}</textarea>',
            r'<textarea name="state" rows="40" cols="80">'
            '\{&#34;stat&#34;: 2\}</textarea>']},
    {
        'name': "Check one can update the participant for an HHDC contract.",
        'path': '/hhdc_contracts/30/edit',
        'method': 'post',
        'data': {
            'party_id': "651",

            # UKDC
            'name': "Dynamat data",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'has_finished': "false",
            'charge_script': """
def virtual_bill_titles():
    return ['net-gbp', 'problem']

def virtual_bill(ds):
    bill = ds.dc_bill
    for hh in ds.hh_data:
        if hh['utc-is-month-end']:
            bill['net-gbp'] += 7
""",
            'properties': "{}"},
        'status_code': 303},

    {
        'name': "Check it's still there",
        'path': '/hhdc_contracts/30/edit',
        'status_code': 200,
        'regexes': [
            r'option value="651" selected']},

    # Check correct fields present for adding a supplier contract },
    {
        'name': "Manipulate supplier contracts",
        'path': '/supplier_contracts/add',
        'regexes': [
            r'name="start_year"'],
        'status_code': 200},

    {
        'name': "Create a new supplier contract",
        'path': '/supplier_contracts/add',
        'method': 'post',
        'data': {
            'participant_id': "28",  # BIZZ
            'name': "Half-hourlies 2007",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'charge_script': "",
            'properties': "{'hydrogen': 'sonata'}"},
        'regexes': [
            r"/supplier_contracts/31"]},

    {
        'name': "Check that it's displayed properly",
        'path': '/supplier_contracts/31/edit',
        'regexes': [
            r'<option value="22" selected>',
            r'<textarea name="properties" rows="20" '
            'cols="80">\{&#39;hydrogen&#39;: &#39;sonata&#39;\}</textarea>'],
        'status_code': 200},
    {
        'path': '/supplier_contracts/31',
        'regexes': [
            r'<legend>Download Displaced Virtual Bills</legend>\s*<br/>\s*'
            'For <input name="months" value="1" maxlength="2" size="2">\s*'
            'month\(s\) until the end of\s*'
            '<input name="finish_year" maxlength="4" size="4" '
            'value="201\d">',
            r'Rate Scripts\s*\[<a\s*'
            r'href="/supplier_contracts/31/add_rate_script"\s*>add</a>\]'],
        'status_code': 200},

    {
        'name': "Update the associated rate script. Supplier contract 31",
        'path': '/supplier_rate_scripts/97/edit',
        'method': 'post',
        'data': {
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'has_finished': "false",
            'script': """
def gsp_gbp_per_kwh():
    return {
        'winter-pk': 0.0193918,
        'winter-low-pk': 0.0501474,
        'winter-off-pk': 0.0062656,
        'summer-pk': 0.0062656,
        'night': 0.0062656,
        'other': 0.0062656}
"""},
        'status_code': 303},
    {
        'name': "View supplier rate script",
        'path': '/supplier_rate_scripts/97',
        'regexes': [
            r'"/supplier_rate_scripts/97/edit"'],
        'status_code': 200},
    {
        'name': "Edit view of supplier rate script",
        'path': '/supplier_rate_scripts/97/edit',
        'regexes': [
            r'"/supplier_rate_scripts/97"'],
        'status_code': 200},


    {
        'name': "View add MOP contract",
        'path': '/mop_contracts/add',
        'status_code': 200},

    {
        'name': "Insert MOP contract",
        'path': '/mop_contracts/add',
        'method': 'post',
        'data': {
            'participant_id': "409",  # LENG
            'name': "MOP Contract",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00"},
        'status_code': 303,
        'regexes': [
            r"/mop_contracts/32"]},

    {
        'name': "Update with a charge script",
        'path': '/mop_contracts/32/edit',
        'method': 'post',
        'data': {
            'party_id': "690",  # LENG
            'name': "MOP Contract",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'charge_script': """
def virtual_bill_titles():
    return ['net-gbp', 'problem']

def virtual_bill(ds):
    bill = ds.mop_bill
    bill['net-gbp'] = 0
    for hh in ds.hh_data:
        if hh['utc-is-month-end']:
            bill['net-gbp'] += 10
""",
            'properties': "{}"},
        'status_code': 303,
        'regexes': [
            r"/mop_contracts/32"]},

    {
        'name': "Check we can see the rate scripts",
        'path': '/mop_contracts/32',
        'status_code': 200},

    {
        'name': "Insert a modern supplier contract. Create a new supplier "
        "contract for 2013",
        'path': '/supplier_contracts/add',
        'method': 'post',
        'data': {
            'participant_id': "54",  # COOP
            'name': "Half-hourlies 2013",
            'start_year': "2013",
            'start_month': "01",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00",
            'charge_script': """
def virtual_bill_titles():
    return []
""",
            'properties': "{}", },
        'regexes': [
            r"/supplier_contracts/33"],
        'status_code': 303},
    {
        'name': "Update the associated rate script. Supplier contract 33",
        'path': '/supplier_rate_scripts/99/edit',
        'method': 'post',
        'data': {
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'has_finished': "false",
            'script': """
def gsp_gbp_per_kwh():
    return {
        'winter-pk': 0.0193918,
        'winter-low-pk': 0.0501474,
        'winter-off-pk': 0.0062656,
        'summer-pk': 0.0062656,
        'night': 0.0062656,
        'other': 0.0062656}
"""},
        'status_code': 303,
        'regexes': [
            r'/supplier_rate_scripts/99']},

    {
        'name': "Create a new supplier contract",
        'path': '/supplier_contracts/add',
        'method': 'post',
        'data': {
            'participant_id': "386",  # HYDE
            'name': "Non half-hourlies 2007",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'has_finished': "false",
            'charge_script': """
def virtual_bill_titles():
    return []
""",
            'properties': "{}", },
        'regexes': [
            r"/supplier_contracts/34"],
        'status_code': 303},

    # Give proper error if there are too few fields },
    {
        'name': "supplies",
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/supplies-too-few-fields.csv'},
        'regexes': [
            r"/general_imports/2"],
        'status_code': 303},
    {
        'path': '/general_imports/2',
        'tries': {},
        'regexes': [
            r"Another field called Supply Name needs to be added on the end"],
        'status_code': 200},

    {
        'name': "non-existent source code",
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/supplies_source.csv'},
        'regexes': [
            r"/general_imports/3"],
        'status_code': 303},
    {
        'path': '/general_imports/3',
        'tries': {},

        # check that it knows that the first line has a source code that is too
        # long
        'regexes': [
            r"There&#39;s no source with the code &#39;netlong&#39;", ],
        'status_code': 200},

    # Line 2 has a DNO that doesn't exist
    {
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/supplies_dno.csv'},
        'regexes': [
            r"/general_imports/4"],
        'status_code': 303},
    {
        'path': '/general_imports/4',
        'tries': {},

        # check that it knows that line 2 has a DNO that doesn't exist
        'regexes': [
            r"There isn&#39;t a DNO contract with the code &#39;79&#39;\."],
        'status_code': 200},

    # Check that it gives a sensible error message if a data is malformed
    {
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/supplies_date.csv'},
        'regexes': [
            r"/general_imports/5"],
        'status_code': 303},
    {
        'path': '/general_imports/5',
        'tries': {},

        # check that it knows that line 1 has a malformed date
        'regexes': [
            r"Can&#39;t parse the date: 2003-0/\*\*d8/03. It needs to be of "
            "the form yyyy-mm-dd hh:MM. invalid literal for int\(\) with base "
            "10: "],
        'status_code': 200},

    # Check for a sensible error message if the site doesn't exist
    {
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/supplies_no_site.csv'},
        'regexes': [
            r"/general_imports/6", ],
        'status_code': 303, },
    {
        'path': '/general_imports/6',
        'tries': {},

        # check that it knows that line 1 has a malformed date
        'regexes': [
            r"There isn&#39;t a site with the code zzznozzz\.", ],
        'status_code': 200, },

    # Valid import of supplies
    {
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/supplies.csv'},
        'status_code': 303,
        'regexes': [
            r"/general_imports/7"]},
    {
        'path': '/general_imports/7',
        'tries': {},

        # Check it's loaded ok
        'regexes': [
            r"The file has been imported successfully"],
        'status_code': 200},

    # Check that a supply with only an import MPAN is there
    {
        'path': '/sites/4/edit',
        'regexes': [
            r"22 6354 2983 570",

            # Check we the 'site_id' field is there
            r'<fieldset>\s*<input type="hidden" name="site_id" value="4">\s*'],
        'status_code': 200},

    # Can we see a site ok?
    {
        'path': '/sites/1/edit',

        # Is the era displayed?
        'regexes': [
            r"<tr>\s*<td>2003-08-03 00:00</td>\s*<td>Ongoing</td>\s*"
            "<td>gen</td>\s*<td>2</td>\s*<td>\s*</td>\s*<td>\s*"
            "22 7907 4116 080\s*</td>\s*</tr>",

            # Does it show the import MPAN?
            r"22 9813 2107 763"],
        'status_code': 200},

    # Can we see a supply ok?

    # View a supply in edit mode
    {
        'name': "view a supply",
        'path': '/supplies/2/edit',

        # Check table of existing eras is there
        'regexes': [
            r"<table>\s*<caption>Existing Eras</caption>",

            # Check reference to ongoing era
            r"<td>2003-08-03 00:00</td>\s*<td>\s*Ongoing", ],
        'status_code': 200},
    {
        'path': '/supplies/1/edit',
        'method': 'post',

        # Can we update a supply name?

        # Can we update a supply source?
        'data': {
            'name': "Hello",
            'source_id': "4",
            'generator_type_id': "1",
            'gsp_group_id': "11"},
        'regexes': [
            r"/supplies/1"],
        'status_code': 303},
    {
        'path': '/supplies/1/edit',
        'regexes': [
            r'value="Hello">',
            r'option value="1" selected>chp</option>'],
        'status_code': 200},
    {
        'path': '/supplies/1/edit',
        'method': 'post',

        # Change it back.
        'data': {
            'name': "1",
            'source_id': "1",
            'generator_type_id': "1",
            'gsp_group_id': "11"},
        'status_code': 303},

    {
        'name': "View era in edit mode. Supply 1",
        'path': '/eras/1/edit',

        # Check start date year is there
        'regexes': [
            r"start_year",
            r'<option value="29" selected>HH contract</option>',
            r'"imp_supplier_contract_id">\s*'
            '<option value="31" selected>Half-hourlies 2007',

            # Can we see the MOP account?
            r'"mc-22 9205 6799 106"'],

        'status_code': 200},

    # Supply 2
    {
        'path': '/eras/2/edit',

        # Check site code is correct
        'regexes': [
            r"<td>\s*CI004\s*</td>"],
        'status_code': 200},

    # Can we add a new era ok? },
    {
        'name': "Manipulating eras",
        'path': '/supplies/2/edit',
        'method': 'post',
        'data': {
            'start_year': "2006",
            'start_month': "07",
            'start_day': "20",
            'start_hour': "00",
            'start_minute': "00",
            'insert_era': "Insert", },
        'regexes': [
            r"/supplies/2"],
        'status_code': 303},

    # Let's check it's carried forward the import mpan. Supply 2
    {
        'path': '/eras/8/edit',
        'regexes': [
            r"22 9813 2107 763",
            r'name="mtc_code" value="845" size="3" maxlength="3"',

            # Form for deleting the era
            r'<form action="/eras/8/edit">\s*'
            r'<fieldset>\s*'
            r'<input type="submit" name="delete" value="Delete">'],
        'status_code': 200},

    # Can we delete the era ok? Supply 2
    {
        'path': '/eras/8/edit?delete=Delete',
        'regexes': [
            r"Are you sure you want to delete this"],
        'status_code': 200},

    # When a supply era is ended, check that the snags are updated. Supply 5
    {
        'path': '/eras/5/edit',
        'method': 'post',
        'data': {
            'start_year': "2003",
            'start_month': "08",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'is_ended': "true",
            'finish_year': "2003",
            'finish_month': "08",
            'finish_day': "13",
            'finish_hour': "23",
            'finish_minute': "30",
            'gsp_group_id': "11",
            'mop_contract_id': "32",
            'mop_account': "22 0883 6932 301",
            'hhdc_contract_id': "30",
            'hhdc_account': "22 0883 6932 301",
            'msn': "",
            'pc_id': "9",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'imp_llfc_code': "570",
            'imp_mpan_core': "22 0883 6932 301",
            'imp_sc': "350",
            'imp_supplier_contract_id': "31",
            'imp_supplier_account': "4341"},
        'status_code': 303},

    {
        'name': "Check it's correct in edit view",
        'path': '/eras/5/edit',

        # Check start day is correct
        'regexes': [
            r'option value="3" selected>03</option>',

            # Check the end date is right
            r'<input type="checkbox" name="is_ended" value="true" checked',
            r'option value="13" selected>13</option>',
            r'option value="23" selected>23</option>'],
        'status_code': 200},

    {
        'name': "Check it's correct in supply view",
        'path': '/supplies/5',
        'status_code': 200,

        # Check the end date is right
        'regexes': [
            r'<form action="/reports/219">\s*'
                r'<input type="hidden" name="supply_id" value="5">',
            r'<a title="2003-08-13 23:30">2003-08-13</a>',
            r'<form action="/reports/187" method="post">',
            r'<legend>TRIAD</legend>\s*<input type="hidden" name="supply_id"',
            r'<a href="/supplies/5/months\?'
            'is_import=true&amp;year=\d{4}&amp;years=1">Import</a>',
            r'<a href="/supplies/5/virtual_bill']},

    # Supply 5, Era 5
    {
        'path': '/channels/18',
        'status_code': 200,

        # Check the end date is right
        'regexes': [
            r"Channel Export\s*REACTIVE_EXP",
            r"<td>2003-08-03 00:00</td>\s*<td>2003-08-13 23:30</td>\s*"
            "<td>Missing</td>"]},

    # Check that if the hhdc contract is changed, the hhdc contract of the
    # snags change

    {
        'name': "Check the export supply capacity can be updated as well. "
        "Supply 5",
        'path': '/eras/5/edit',
        'method': 'post',
        'data': {
            'msn': "",
            'start_year': "2003",
            'start_month': "08",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'is_ended': "true",
            'finish_year': "2003",
            'finish_month': "08",
            'finish_day': "13",
            'finish_hour': "23",
            'finish_minute': "30",
            'mop_contract_id': "32",
            'mop_account': "22 0883 6932 301",
            'hhdc_contract_id': "29",
            'hhdc_account': "22 0883 6932 301",
            'pc_id': "9",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'imp_llfc_code': "570",
            'imp_mpan_core': "22 0883 6932 301",
            'imp_gsp_group_id': "11",
            'imp_sc': "430",
            'imp_supplier_contract_id': "31",
            'imp_supplier_account': "4341"},
        'status_code': 303},

    {
        'name': "Check the change is there in edit view",
        'path': '/eras/5/edit',
        'regexes': [
            r'<input name="imp_sc" value="430" size="9" maxlength="9">']},
    {
        'path': '/channels/18',
        'status_code': 200,
        'regexes': [
            r"Channel Export\s*REACTIVE_EXP",

            # Check the snag is there
            r"<td>2003-08-03 00:00</td>\s*<td>2003-08-13 23:30</td>\s*"
            "<td>Missing</td>"]},

    {
        'name': "Put it back to how it was. Supply 5",
        'path': '/eras/5/edit',
        'method': 'post',
        'data': {
            'msn': "",
            'start_year': "2003",
            'start_month': "08",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'is_ended': "false",
            'mop_contract_id': "32",
            'mop_account': "22 0883 6932 301",
            'hhdc_contract_id': "29",
            'hhdc_account': "22 0883 6932 301",
            'pc_id': "9",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'imp_llfc_code': "570",
            'imp_mpan_core': "22 0883 6932 301",
            'imp_sc': "350",
            'imp_supplier_contract_id': "31",
            'imp_supplier_account': "4341"},
        'status_code': 303},

    {
        'name': "View general imports",
        'path': '/general_imports',
        'status_code': 200,
        'regexes': [
            r'"/style"']},

    {
        'name': "Valid bulk update of supply eras",
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/era-update.csv'},
        'status_code': 303,
        'regexes': [
            r"/general_imports/8"]},
    {
        'path': '/general_imports/8',
        'tries': {},

        # Check it's loaded ok
        'regexes': [
            r"The file has been imported successfully"],
        'status_code': 200},
    {
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/supplies-bad-mpan.csv'},
        'status_code': 303,
        'regexes': [
            r"/general_imports/9"]},
    {
        'path': '/general_imports/9',
        'tries': {},

        # Check it's loaded ok
        'regexes': [
            r"The MPAN core 22 9813 2107 763 is already attached to another "
            "supply\."],
        'status_code': 200},

    {
        'name': "Attach another site to an era. Supply 2",
        'path': '/eras/2/edit',
        'method': 'post',
        'data': {
            'site_code': "CI005",
            'attach': "Attach"},
        'status_code': 303},

    # Check that we prevent mpan cores from changing without an overlapping
    # period. Supply 2
    {
        'path': '/eras/8/edit',
        'method': 'post',
        'data': {
            'msn': "",
            'start_year': "2006",
            'start_month': "07",
            'start_day': "20",
            'start_hour': "00",
            'start_minute': "00",
            'is_ended': "false",
            'mop_contract_id': "32",
            'mop_account': "mc-22 9813 2107 763",
            'hhdc_contract_id': "29",
            'hhdc_account': "01",
            'pc_id': "9",
            'mtc_code': "845",
            'cop_id': "3",
            'ssc_code': "",
            'imp_llfc_code': "570",
            'imp_mpan_core': "2276930477695",
            'imp_sc': "430",
            'imp_supplier_contract_id': "31",
            'imp_supplier_account': "01"},
        'status_code': 400,

        # Also, we've changed the CoP to be 3. Check that this is remembered
        # when there is an error.
        'regexes': [
            r'<option value="3" selected>3 CoP 3</option>',
            r"MPAN cores can&#39;t change without an overlapping period"]},

    # Check that we get a good error message if the LLFC is of the wrong
    # polarity. Supply 2
    {
        'path': '/eras/8/edit',
        'method': 'post',
        'data': {
            'msn': "",
            'start_year': "2006",
            'start_month': "07",
            'start_day': "20",
            'start_hour': "00",
            'start_minute': "00",
            'is_ended': "false",
            'mop_contract_id': "32",
            'mop_account': "mc-22 9813 2107 763",
            'hhdc_contract_id': "29",
            'hhdc_account': "01",
            'pc_id': "9",
            'mtc_code': "845",
            'cop_id': "3",
            'ssc_code': "",
            'imp_llfc_code': "521",
            'imp_mpan_core': "22 9813 2107 763",
            'imp_sc': "430",
            'imp_supplier_contract_id': "31",
            'imp_supplier_account': "01"},
        'status_code': 400,
        'regexes': [
            r"The imp line loss factor 521 is actually an exp one\."]},

    # Check it gives a sensible error message if the files doesn't start
    # with #F2
    {
        'name': "Import hh data",
        'path': '/hhdc_contracts/29/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/no_hash.df2'},
        'regexes': [
            r"/hhdc_contracts/29/hh_imports/0"],
        'status_code': 303},
    {
        'path': '/hhdc_contracts/29/hh_imports/0',
        'tries': {},
        'regexes': [
            r"The first line must be &#39;#F2&#39;"],
        'status_code': 200},

    {
        'name': "Import some hh Stark DF2 data",
        'path': '/hhdc_contracts/29/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/ftp/hh_data.df2'},
        'status_code': 303,
        'regexes': [
            r"/hhdc_contracts/29/hh_imports/1"]},
    {
        'path': '/hhdc_contracts/29/hh_imports/1',
        'tries': {},

        # Check it's loaded ok and has ignored the blank line and the #F2 line
        'regexes': [
            r"The import has completed.*successfully.",

            # Check link to hhdc is correct
            r"/hhdc_contracts/29"],
        'status_code': 200},

    {
        'name': 'Supply 1, era 1',
        'path': '/channels/4',
        'regexes': [
            r"Channel Export\s*REACTIVE_EXP",
            r'<tr>\s*<td>\s*'
            '<a href="/channel_snags/4">view</a>\s*'
            '</td>\s*<td>2003-08-03 00:00</td>\s*<td>Ongoing</td>\s*'
            '<td>Missing</td>'],
        'status_code': 200},

    {
        'name': "Check if more hh data imports ok",
        'path': '/hhdc_contracts/29/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh_data2.df2'},
        'status_code': 303},

    # This relies on the datum 15/11/2005,00:30,1.0,A being already loaded,
    # with a gap before it.
    {
        'name': "Detect if hh import still works if first hh datum is "
        "missing.",
        'path': '/hhdc_contracts/29/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/missing.df2'},
        'regexes': [
            r"/hhdc_contracts/29/hh_imports/3"],
        'status_code': 303},
    {
        'path': '/hhdc_contracts/29/hh_imports/3',
        'tries': {},
        'regexes': [
            r"The import has completed.*successfully."],
        'status_code': 200},

    # This relies on the default timezone being BST },
    {
        'name': "Do we handle BST ok?",
        'path': '/hhdc_contracts/29/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh_data_timezone.df2'},
        'regexes': [
            r"/hhdc_contracts/29/hh_imports/4"],
        'status_code': 303},
    {
        'path': '/hhdc_contracts/29/hh_imports/4',

        # Check it's loaded ok
        'tries': {},
        'regexes': [
            r"The import has completed.*successfully."],
        'status_code': 200},

    # Test that 3 non-actual reads in a row generate a single snag
    {
        'name': "Actual reads snags combined properly",
        'path': '/hhdc_contracts/29/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh_data_not_actual.df2'},
        'regexes': [
            r"/hhdc_contracts/29/hh_imports/5"],
        'status_code': 303},
    {
        'path': '/hhdc_contracts/29/hh_imports/5',
        'tries': {},
        'regexes': [
            r"The import has completed.*successfully."],
        'status_code': 200},

    {
        'name': "supply 1, era 1",
        'path': '/channels/3',
        'regexes': [
            r"Channel Export\s*ACTIVE",
            r'<td>\s*'
            '<a href="/channel_snags/45">view</a>\s*'
            '</td>\s*<td>2005-12-15 07:00</td>\s*<td>2005-12-15 08:00</td>\s*'
            '<td>Estimated</td>',
            r'<tr>\s*<td>\s*'
            '<a href="/channel_snags/3">view</a>\s*'
            '</td>\s*<td>2003-08-03 00:00</td>\s*<td>2005-12-15 06:30</td>\s*'
            '<td>Missing</td>'],
        'status_code': 200},
    {
        'path': '/hhdc_contracts/29/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh_data_not_actual2.df2'},
        'regexes': [
            r'/hhdc_contracts/29/hh_imports/6'],
        'status_code': 303},
    {
        'path': '/hhdc_contracts/29/hh_imports/6',
        'tries': {},
        'regexes': [
            r"The import has completed.*successfully."],
        'status_code': 200},

    {
        'name': "supply 1, era 1",
        'path': '/channels/3',
        'regexes': [
            r"Channel Export\s*ACTIVE",
            r'<td>\s*'
            '<a href="/channel_snags/45">view</a>\s*'
            '</td>\s*<td>2005-12-15 07:00</td>\s*<td>2005-12-15 09:30</td>\s*'
            '<td>Estimated</td>'],
        'status_code': 200},

    # Test if a CSV HH file can be imported },
    {
        'name': "Importing simple CSV data",
        'path': '/hhdc_contracts/29/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh_data.simple.csv'},
        'regexes': [
            r"/hhdc_contracts/29/hh_imports/7"],
        'status_code': 303},
    {
        'path': '/hhdc_contracts/29/hh_imports/7',
        'tries': {},
        'regexes': [
            r"The import has completed.*successfully."],
        'status_code': 200},

    {
        'name': "Check that the imported HH datum is correct for supply 1, "
        "era 1",
        'path': '/channels/3?start_year=2005&start_month=09',
        'regexes': [
            r"<td>2005-09-15 00:00</td>\s*<td>1.0</td>\s*<td>A</td>"]},

    # Check it gives a sensible error message if the comma after the value is
    # missing
    {
        'name': "Various DF2 tests.",
        'path': '/hhdc_contracts/29/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh_data_malformed.df2'},
        'regexes': [
            r"/hhdc_contracts/29/hh_imports/8"],
        'status_code': 303},
    {
        'path': '/hhdc_contracts/29/hh_imports/8',
        'tries': {},
        'regexes': [
            r"Problem at line number: 4"],
        'status_code': 200},

    # Check it gives a sensible error message if the first mpan is malformed
    {
        'path': '/hhdc_contracts/29/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh_data_bad_beginning.df2'},
        'regexes': [
            r"/hhdc_contracts/29/hh_imports/9"],
        'status_code': 303},
    {
        'path': '/hhdc_contracts/29/hh_imports/9',
        'tries': {},
        'regexes': [
            r"The MPAN core &#39;2204707514535,,,&#39; must contain exactly "
            "13 digits"],
        'status_code': 200},

    {
        'name': "Check sensible error message if header but no data",
        'path': '/hhdc_contracts/29/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh_data_header_but_no_data.df2'},
        'regexes': [
            r"/hhdc_contracts/29/hh_imports/10"],
        'status_code': 303},
    {
        'path': '/hhdc_contracts/29/hh_imports/10',
        'tries': {},
        'regexes': [
            r"The import has completed.*successfully\."],
        'status_code': 200},

    {
        'name': "Manipulate channels",
        'path': '/channels/19',
        'regexes': [
            r"Import\s*ACTIVE"],
        'status_code': 200},

    {
        'name': "View channel, supply 6, era 6",
        'path': '/channels/21',
        'regexes': [
            r"Export\s*REACTIVE_EXP"],
        'status_code': 200},
    {
        'name': "Check site level snag",
        'path': '/site_snags',
        'regexes': [
            r"CI004",

            # There's an hh where export to net is *less* than imported from
            # generator, check this doesn't show up.
            r'<td>\s*'
            '<a href="/site_snags/43">view</a>\s*'
            '\[<a href="/site_snags/43/edit">edit</a>\]\s*'
            r'</td>\s*<td>[^<]*</td>\s*'
            '<td>\s*'
            '<a href="/sites/1">CI004</a>\s*'
            '</td>\s*<td>Lower Treave</td>\s*'
            '<td>Export to net &gt; import from generators.</td>\s*'
            '<td>2005-10-29 23:30</td>\s*<td>\s*2005-10-30 01:00</td>\s*'
            '</tr>\s*</tbody>'],
        'status_code': 200},
    {
        'path': '/site_snags/edit',

        # Check that there's an 'ignore-year' parameter.
        'regexes': [
            r'name="ignore_year"'],
        'status_code': 200},

    # Supply 1, era 1 },
    {
        'name': "Check view of channel level snag",
        'path': '/channel_snags/1',
        'status_code': 200,
        'regexes': [
            r'<a href="/channel_snags\?hhdc_contract_id=29&amp;days_hidden=5">'
            r'Channel Snags</a>']},

    {
        'name': "Check edit view of channel level snag",
        'path': '/channel_snags/1/edit',
        'status_code': 200,
        'regexes': [
            r'<form action="" method="post">\s*'
            r'<fieldset style="border: none;">\s*'
            r'<input type="hidden" name="ignore" value="true">\s*'
            r'<input type="submit" value="Ignore">\s*'
            r'</fieldset>']},

    # Check that for a supply with multiple eras, a channel without any data
    # can be deleted. This test needs some hh data loaded somewhere. Supply 2,
    # era 8, exp active
    {
        'name': "Delete channel without data",
        'path': '/channels/25/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'status_code': 303},

    {
        'name': "Put it back to how it was before. Supply 2",
        'path': '/eras/8/add_channel',
        'method': 'post',
        'data': {
            'imp_related': "false",
            'channel_type': "ACTIVE"},
        'status_code': 303},

    # Check it gives an error if the hhdc contract is removed from a supply era
    # that has data. Supply 1
    {
        'path': '/eras/1/edit',
        'method': 'post',
        'data': {
            'start_year': "2003",
            'start_month': "08",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'is_ended': "false",
            'msn': "",
            'gsp_group_id': "11",
            'pc_id': "9",
            'hhdc_contract_id': "null",
            'hhdc_account': "01",
            'imp_mtc_code': "845",
            'imp_llfc_code': "550",
            'imp_mpan_core': "22 9205 6799 106",
            'imp_ssc_code': "",
            'imp_sc': "450",
            'imp_supplier_contract_id': "6",
            'imp_supplier_account': "11640077",
            'exp_mtc_code': "845",
            'exp_llfc_code': "581",
            'exp_mpan_core': "22 0470 7514 535",
            'exp_ssc_code': "",
            'exp_sc': "150",
            'exp_supplier_contract_id': "6",
            'exp_supplier_account': "01"},
        'status_code': 400},
    {
        'name': "View a snag",
        'path': '/site_snags/43',
        'status_code': 200,
        'regexes': [
            r"<th>Finish Date</th>\s*<td>2005-10-30 01:00</td>", ], },

    # Assumes various site snags are present at this stage },
    {
        'name': "site snags stay ignored",
        'path': '/site_snags/edit',
        'method': 'post',
        'data': {
            'ignore_year': "2006",
            'ignore_month': "12",
            'ignore_day': "26",
            'ignore_hour': "00",
            'ignore_minute': "00",
            'ignore': "Ignore"},
        'status_code': 303},
    {
        'path': '/hhdc_contracts/29/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/ftp/hh_data.df2'},
        'regexes': [
            r"/hhdc_contracts/29/hh_imports/11"],
        'status_code': 303},
    {
        'path': '/hhdc_contracts/29/hh_imports/11',
        'tries': {},
        'regexes': [
            r"The import has completed.*successfully"],
        'status_code': 200},
    {
        'path': '/site_snags',
        'regexes': [
            r"<tbody>\s*</tbody>"],
        'status_code': 200},
    {
        'path': '/supplies/5/hh_data?months=1&finish_year=2010&'
        'finish_month=03',
        'regexes': [
            r'<form action="/supplies/5/hh_data">',
            r"<tr>\s*<td>\s*2010-03-15 12:00\s*</td>\s*<td>0</td>\s*"
            "<td>A</td>",
            ],
        'status_code': 200},

    # Create a new batch
    {
        'name': "Batches",
        'path': '/supplier_contracts/31/add_batch',
        'method': 'post',
        'data': {
            'reference': "04-003",
            'description': "Contract 4, batch number 3"},
        'status_code': 303},

    # Check it gives a good error message for a duplicate name
    {
        'path': '/supplier_contracts/31/add_batch',
        'method': 'post',
        'data': {
            'reference': "04-003",
            'description': "dup batch"},
        'regexes': [
            r"There&#39;s already a batch attached to the contract "
            "Half-hourlies 2007 with the reference 04-003\."],
        'status_code': 400},

    # Create a new import. Supplier contract 30
    {
        'name': "Bill imports",
        'path': '/supplier_bill_imports',
        'method': 'post',
        'data': {
            'supplier_batch_id': '1'},
        'files': {'import_file': 'test/bills.mm'},
        'status_code': 303,
        'regexes': [
            r"/supplier_bill_imports/0"]},

    {
        'name': "Supplier contract 31, batch 1",
        'path': '/supplier_bill_imports/0',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"<td>2007-02-28 00:00</td>\s*<td>0</td>\s*<td>4463.08</td>",
            r"All the bills have been successfully loaded and attached to the "
            "batch\."]},

    # Valid import of supplies
    {
        'name': "Set up NHH",
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/nhh-supplies.csv'},
        'status_code': 303,
        'regexes': [
            r"/general_imports/10"]},
    {
        'path': '/general_imports/10',
        'tries': {},

        # Check it's loaded ok
        'regexes': [
            r"The file has been imported successfully"],
        'status_code': 200},

    # Check values have been imported correctly. Supply 11
    {
        'path': '/eras/11/edit',
        'regexes': [
            r"K87D74429"],
        'status_code': 200},

    # Create a new batch
    {
        'path': '/supplier_contracts/34/add_batch',
        'method': 'post',
        'data': {
            'reference': "06-002",
            'description': "Bgb batch"},
        'status_code': 303},

    {
        'name': "Supplier contract 34",
        'path': '/supplier_bill_imports',
        'method': 'post',
        'data': {
            'supplier_batch_id': '3'},
        'files': {'import_file': 'test/bills.bgb.edi'},
        'status_code': 303,
        'regexes': [
            r"/supplier_bill_imports/1"]},

    # Supplier contract 34, batch 3
    {
        'path': '/supplier_bill_imports/1',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"All the bills have been successfully loaded and attached to the "
            "batch\."]},

    # Set a previously estimated HH to actual, supply 1, era 1, channel 3
    {
        'name': "Check that resolved HH estimates have their snags cleared.",
        'path': '/hh_data/12/edit',
        'method': 'post',
        'data': {
            'update': "Update",
            'value': "0.5",
            'status': "A"},
        'status_code': 303},

    # Check that the snag has been cleared. Supply 1, era 1
    {
        'path': '/channels/3',
        'regexes': [
            r"Channel Export\s*ACTIVE",
            r"<td>2005-12-15 07:30</td>\s*<td>2005-12-15 09:30</td>\s*"
            "<td>Estimated</td>"]},

    # Change it back. supply 1, era 1.
    {
        'path': '/hh_data/12/edit',
        'method': 'post',
        'data': {
            'value': "0.5",
            'status': "E"},
        'status_code': 303},
    {
        'name': "Test of BGlobal HH data import",
        'path': '/hhdc_contracts/29/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh_data.bg.csv'},
        'status_code': 303,
        'regexes': [
            r"/hhdc_contracts/29/hh_imports/12"]
        },
    {
        'path': '/hhdc_contracts/29/hh_imports/12',
        'tries': {},
        'regexes': [
            r"The import has completed.*successfully."],
        'status_code': 200},

    # supply 1, era 1 },
    {
        'name': "Check the BGlobal data is imported to the right number of "
        "sig figs",
        'path': '/channels/1?start_year=2008&start_month=07',
        'status_code': 200,
        'regexes': [
            r"0\.262"]},
    {
        'name': "Check okay if supply era update is interupted by an error. "
        "Supply 9",
        'path': '/eras/9/edit',
        'method': 'post',
        'data': {
            'msn': "P96C93722",
            'start_year': "2005",
            'start_month': "08",
            'start_day': "06",
            'is_ended': "false",
            'pc_id': "9",
            'mtc_code': "535",
            'llfc_code': "510",
            'imp_mpan_core': "22 0195 4836 192",
            'ssc_code': "0127",
            'gsp_group_id': "11",
            'imp_sc': "30",
            'hhdc_contract_id': "HH contract",
            'hhdc_account': "",
            'imp_supplier_contract_id': "Non half-hourlies 2007",
            'imp_supplier_account': "341664",

            # Should error on this
            'exp_mpan_core': "99 0000 4444 883",
            'exp_sc': "200",
            'exp_supplier_contract_id': "Non half-hourlies 2007",
            'exp_supplier_account': "341664", },
        'status_code': 400, },
    {
        'name': "HH data general import",
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh_data.csv'},
        'status_code': 303,
        'regexes': [
            r"/general_imports/11"]},
    {
        'path': '/general_imports/11',
        'tries': {},
        'regexes': [
            r"The file has been imported successfully\."],
        'status_code': 200},

    # Create new batch },
    {
        'name': "CSV import",
        'path': '/supplier_contracts/31/add_batch',
        'method': 'post',
        'data': {
            'reference': "06-004",
            'description': "CSV batch"},
        'status_code': 303},

    {
        'name': "Insert bills. Supplier contract",
        'path': '/supplier_bill_imports',
        'method': 'post',
        'data': {
            'supplier_batch_id': '4'},
        'files': {'import_file': 'test/bills.csv'},
        'status_code': 303,
        'regexes': [
            r"/supplier_bill_imports/2"]},

    # Supplier contract 57, batch 4
    {
        'path': '/supplier_bill_imports/2',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"All the bills have been successfully loaded and attached to the "
            "batch\."]},

    # First create the era
    {
        'name': "Check one is able to delete an era ok",
        'path': '/supplies/9/edit',
        'method': 'post',
        'data': {
            'start_year': "2009",
            'start_month': "01",
            'start_day': "20",
            'start_hour': "00",
            'start_minute': "00",
            'insert_era': "Insert"},
        'regexes': [
            r"/supplies/9"],
        'status_code': 303},

    # Delete era. Supply 9
    {
        'path': '/eras/12/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'status_code': 303},
    {
        'name': "Check 'view' link is correct on a site in the edit world.",
        'path': '/sites/7/edit',
        'regexes': [
            r"/sites/7"],
        'status_code': 200},
    {
        'name': "Check that if era dates change, hh data move with them.",
        'path': '/supplies/1/edit',
        'method': 'post',
        'data': {
            'start_year': "2008",
            'start_month': "7",
            'start_day': "7",
            'start_hour': "00",
            'start_minute': "00",
            'insert_era': "Insert"},
        'regexes': [
            r"/supplies/1"],
        'status_code': 303},

    {
        'name': "supply 1, era 13",
        'path': '/channels/32?start_year=2008&start_month=07',
        'regexes': [
            r'<td>\s*'
            '\[<a href="/hh_data/66/edit">'
            'edit</a>\]\s*</td>\s*<td>2008-07-07 00:00</td>\s*'
            '<td>0.247</td>\s*<td>A</td>'],
        'status_code': 200},
    {
        'name': "Check 'view' link is correct on a supply in the edit world.",
        'path': '/supplies/10/edit',
        'regexes': [
            r"/supplies/10"],
        'status_code': 200},
    {
        'name': "Check site nav link is correct on site HH data page.",
        'path': '/sites/1/hh_data?year=2005&month=11',
        'regexes': [
            r"/sites/1",

            # Check that columns are in the right order
            r'kWh</th>\s*<th colspan="4">\s*1 net\s*</th>'],
        'status_code': 200},
    {
        'name': "Check no duplicate supplies in Supplies Duration report.",
        'path': '/reports/149?start_year=2008&start_month=07&start_day=01&'
        'start_hour=0&start_minute=0&finish_year=2008&finish_month=07&'
        'finish_day=31&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"000_FINISHED_watkinsexamplecom_supplies_duration\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '000_FINISHED_watkinsexamplecom_supplies_duration.csv',
        'regexes': [
            # Check starts with titles
            r'\)\s\sSupply',

            r'("1","1","net","","CH017",){1}',

            # Check full line
            r'"2","1","net","","CI004","Lower Treave","2008-07-01 00:00",'
            '"2008-07-31 23:30","00","845","5","","0","hh",'
            '570,22 9813 2107 763,430,Half-hourlies 2007,0,0,0.0,0,,None,1488,'
            '581,22 3475 1614 211,900,Half-hourlies 2007,0,0,,0,,None,1488'],
        'status_code': 200},

    # Delete a day of data. Supply 1, era 13 },
    {
        'name': "Check last HH is deleted when a day of HH data is deleted.",
        'path': '/channels/32/edit',
        'method': 'post',
        'data': {
            'start_year': "2008",
            'start_month': "07",
            'start_day': "07",
            'start_hour': "00",
            'start_minute': "00",
            'finish_year': "2008",
            'finish_month': "07",
            'finish_day': "07",
            'finish_hour': "23",
            'finish_minute': "30",
            'delete_data': "Delete"},
        'status_code': 303},
    {
        'name': "Check last HH is deleted when a day of HH data is deleted.",
        'path': '/channels/32',
        'regexes': [
            r"Data successfully deleted\."],
        'status_code': 200},

    # Check the last HH of the day is deleted. Supply 1, era 13
    {
        'path': '/channels/32?start_year=2008&start_month=07',
        'regexes': [
            r'<tbody>\s*<tr>\s*<td>\s*'
            r'\[<a href="/hh_data/114/edit">edit</a>\]\s*'
            r'</td>\s*<td>2008-07-08 00:00</td>\s*'
            r'<td>0.299</td>\s*'
            r'<td>A</td>'],
        'status_code': 200},

    # supply 1, era 1, channel 1 },
    {
        'name': "Check one is redirected to hh data when a datum is deleted.",
        'path': '/hh_data/23/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'status_code': 303,
        'regexes': [
            r"/channels/1"]},

    # Supply 5 },
    {
        'name': "Test that it gives an error if the hhdc_contract_id is null.",
        'path': '/eras/5/edit',
        'method': 'post',
        'data': {
            'msn': "",
            'start_year': "2003",
            'start_month': "08",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'is_ended': "false",
            'mop_contract_id': "32",
            'mop_account': "22 0883 6932 301",
            'hhdc_contract_id': "null",
            'pc_id': "9",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'imp_llfc_code': "570",
            'imp_mpan_core': "22 0883 6932 301",
            'imp_sc': "350",
            'imp_supplier_contract_id': "57",
            'imp_supplier_account': "01"},
        'status_code': 400,
        'regexes': [
            r"Problem parsing the field hhdc_contract_id as an integer: "
            "invalid literal for int\(\) with base 10: .*null"]},
    {
        'name': "Test that profile 05 is displayed for an era. Supply 9",
        'path': '/eras/9/edit',
        'regexes': [
            r'<option value="5" selected>05 - Non-domestic, MD, load factor '
            '0-20%</option>'],
        'status_code': 200},
    {
        'name': "Try adding a party viewer.",
        'path': '/users',
        'method': 'post',
        'data': {
            'email_address': "mishka@localhost",
            'password': "fyodor",
            'user_role_code': "party-viewer",
            'party_id': "97"},  # DASL HHDC

        'status_code': 303,
        'regexes': [
            r"/users/5"]},
    {
        'name': "Check that the party viewer is able to view snags.",
        'path': '/channel_snags?hhdc_contract_id=29&days_hidden=5',
        'auth': ('mishka@localhost', 'fyodor'),
        'regexes': [
            r"<td>\s*22 0470 7514 535\s*</td>\s*<td>\s*<ul>\s*<li>\s*"
            "CH017 Parbola\s*</li>",
            r"There are 46 snag\(s\) older than\s*5 days\s*"
            r"that aren't ignored\.",
            r'<a href="/hhdc_contracts/29">HH contract</a>',
            r'<li>\s*'
            '<a href="/channel_snags/1">view</a>\s*'
            '\[<a href="/channel_snags/1/edit">edit</a>\]\s*'
            '</li>',
            r'<form action="/reports/233">'],
        'status_code': 200},
    {
        'name': "Make sure everything's there on the home page.",
        'path': '/',
        'auth': ('watkin\\s@example.com', 'alan'),
        'regexes': [
            r'<a href="/participants">Market Participants</a>',
            r'<a href="/meter_payment_types">Meter Payment Types</a>',
            r'<a href="/sources">\s*Sources\s*</a>',
            r'<a href="/generator_types">\s*Generator Types\s*'
            '</a>',
            r'<a href="/csv_sites_monthly_duration">Download</a>',
            r'<a href="/ods_scenario_runner">\s*Scenario Runner\s*</a>'],
        'status_code': 200},

    # Supplier contract 47
    {
        'name': "Test deleting the only rate script attached to a supplier "
        "contract.",
        'path': '/supplier_rate_scripts/99/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'regexes': [
            r"You can&#39;t delete the last rate script\."],
        'status_code': 400},
    {
        'name': "Try adding a second rate script (set to 'ongoing'), and see "
        "if the era can be updated.",
        'path': '/supplier_contracts/34/add_rate_script',
        'method': 'post',
        'data': {
            'start_year': "2009",
            'start_month': "08",
            'start_day': "16",
            'start_hour': "00",
            'start_minute': "00",
            'script': ""},
        'status_code': 303},

    # Supply 1
    {
        'path': '/eras/13/edit',
        'method': 'post',
        'data': {
            'start_year': "2008",
            'start_month': "07",
            'start_day': "07",
            'start_hour': "00",
            'start_minute': "00",
            'is_ended': "false",
            'mop_contract_id': "32",
            'mop_account': "mc-22 0470 7514 535",
            'hhdc_contract_id': "29",
            'hhdc_account': "01",
            'msn': "",
            'pc_id': "9",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'exp_llfc_code': "581",
            'exp_mpan_core': "22 0470 7514 535",
            'exp_sc': "150",
            'exp_supplier_contract_id': "34",
            'exp_supplier_account': "010"},
        'status_code': 303},
    {
        'name': "Check updating of HHDC contract state.",
        'path': '/hhdc_contracts/29/edit',
        'method': 'post',
        'data': {
            'state': """{
'last_import_keys': {'.': '1960-11-30 00:00_example.csv'}}
""",
            'update_state': "Update State"},
        'status_code': 303},
    {
        'path': '/hhdc_contracts/29',
        'status_code': 200,
        'regexes': [
            r"\{\s*&#39;last_import_keys&#39;: \{&#39;.&#39;: "
            "&#39;1960-11-30 00:00_example.csv&#39;\}\}",

            # Check link to channel snags
            r"days_hidden",

            # Check link to add a rate script
            r'Rate Scripts\s*'
            '\[<a href="/hhdc_contracts/29/add_rate_script">'
            'add</a>\]']},

    # Insert era
    {
        'name': "Check dates are correct for four eras.",
        'path': '/supplies/1/edit',
        'method': 'post',
        'data': {
            'start_year': "2008",
            'start_month': "08",
            'start_day': "07",
            'start_hour': "00",
            'start_minute': "00",
            'insert_era': "insert_era"},
        'status_code': 303},
    {
        'path': '/supplies/1/edit',
        'method': 'post',
        'data': {
            'start_year': "2008",
            'start_month': "09",
            'start_day': "07",
            'start_hour': "00",
            'start_minute': "00",
            'insert_era': "insert_era"},
        'status_code': 303},
    {
        'path': '/supplies/1/edit',
        'regexes': [
            r"<tr>\s*<td>2003-08-03 00:00</td>\s*<td>2008-07-06 23:30"],
        'status_code': 200},
    {
        'name': "Test 'view' link from supplier rate script add.",
        'path': '/supplier_contracts/34/add_rate_script',
        'regexes': [
            r"/supplier_contracts/34"]},
    {
        'name': "Check 'HH Contract' option is there. Supply 9.",
        'path': '/eras/9/edit',
        'regexes': [
            r'<option value="29">HH contract</option>\s*</select>']},
    {
        'name': "Try bulk delete of HHDC snags.",
        'path': '/hhdc_contracts/29/edit',
        'method': 'post',
        'data': {
            'ignore_year': "2010",
            'ignore_month': "01",
            'ignore_day': "13",
            'ignore_hour': "00",
            'ignore_minute': "00",
            'ignore_snags': ""},
        'status_code': 303},
    {
        'name': "Check python compile error gives a reasonable message.",
        'path': '/supplier_contracts/31/edit',
        'method': 'post',
        'data': {
            'party_id': "22",  # BIZZ
            'name': "Half-hourlies 2007",
            'charge_script': """
def virtual_bill(supply, startDate, finishDate, pw):
    syntax error
""",
            'properties': "{}"},
        'regexes': [
            #  Different errors for CPython and Jython
            r"<li>invalid syntax \(&lt;unknown&gt;, line 3\)</li>|"
            r"\(&lt;unknown&gt;, line 3\)</li>"],
        'status_code': 400},

    # Put back to how it was before
    {
        'path': '/supplier_contracts/31/edit',
        'method': 'post',
        'data': {
            'party_id': "22",
            'name': "Half-hourlies 2007",
            'charge_script': """
from operator import itemgetter
from datetime import datetime as Datetime
import pytz
from dateutil.relativedelta import relativedelta
from chellow.utils import HH
import chellow.triad
import chellow.computer
import chellow.ccl
import chellow.bsuos
import chellow.tlms
import chellow.duos
import chellow.system_price

TRIAD_TITLES = (
    'triad-actual-1-date', 'triad-actual-1-msp-kw', 'triad-actual-1-status',
    'triad-actual-1-laf', 'triad-actual-1-gsp-kw', 'triad-actual-2-date',
    'triad-actual-2-msp-kw', 'triad-actual-2-status', 'triad-actual-2-laf',
    'triad-actual-2-gsp-kw', 'triad-actual-3-date', 'triad-actual-3-msp-kw',
    'triad-actual-3-status', 'triad-actual-3-laf', 'triad-actual-3-gsp-kw',
    'triad-actual-gsp-kw', 'triad-actual-rate', 'triad-actual-gbp',
    'triad-estimate-1-date', 'triad-estimate-1-msp-kw',
    'triad-estimate-1-status', 'triad-estimate-1-laf',
    'triad-estimate-1-gsp-kw', 'triad-estimate-2-date',
    'triad-estimate-2-msp-kw', 'triad-estimate-2-status',
    'triad-estimate-2-laf', 'triad-estimate-2-gsp-kw', 'triad-estimate-3-date',
    'triad-estimate-3-msp-kw', 'triad-estimate-3-status',
    'triad-estimate-3-laf', 'triad-estimate-3-gsp-kw', 'triad-estimate-gsp-kw',
    'triad-estimate-rate', 'triad-estimate-months', 'triad-estimate-gbp',
    'triad-all-estimates-months', 'triad-all-estimates-gbp')


def virtual_bill_titles():
    return [
        'net-gbp', 'tlm', 'ccl-kwh', 'ccl-rate', 'ccl-gbp',
        'data-collection-gbp', 'duos-availability-kva',
        'duos-availability-days', 'duos-availability-rate',
        'duos-availability-gbp', 'duos-excess-availability-kva',
        'duos-excess-availability-days', 'duos-excess-availability-rate',
        'duos-excess-availability-gbp','duos-day-kwh', 'duos-day-gbp',
        'duos-night-kwh', 'duos-night-gbp', 'duos-reactive-rate',
        'duos-reactive-gbp', 'duos-standing-gbp', 'settlement-gbp',
        'night-msp-kwh', 'night-gsp-kwh', 'night-gbp', 'other-msp-kwh',
        'other-gsp-kwh', 'other-gbp', 'summer-pk-msp-kwh', 'summer-pk-gsp-kwh',
        'summer-pk-gbp', 'winter-low-pk-msp-kwh', 'winter-low-pk-gsp-kwh',
        'winter-low-pk-gbp', 'winter-off-pk-msp-kwh', 'winter-off-pk-gsp-kwh',
        'winter-off-pk-gbp', 'winter-pk-msp-kwh', 'winter-pk-gsp-kwh',
        'winter-pk-gbp', 'bsuos-kwh', 'bsuos-rate', 'bsuos-gbp'] + \
        list(TRIAD_TITLES) + ['problem']

def displaced_virtual_bill_titles():
    return [
        'net-gbp', 'bsuos-kwh', 'bsuos-rate', 'bsuos-gbp', 'ccl-kwh',
        'ccl-rate', 'ccl-gbp', 'ssp-rate', 'tlm', 'duos-green-kwh',
        'duos-green-rate', 'duos-green-gbp', 'duos-reactive-gbp',
        'duos-reactive-working', 'duos-standing-gbp', 'night-gbp',
        'night-gsp-kwh', 'night-msp-kwh', 'other-gbp', 'other-gsp-kwh',
        'other-msp-kwh', 'summer-pk-gbp', 'summer-pk-gsp-kwh',
        'summer-pk-msp-kwh', 'triad-gbp', 'triad-working', 'winter-low-pk-gbp',
        'winter-low-pk-gsp-kwh', 'winter-low-pk-msp-kwh', 'winter-off-pk-gbp',
        'winter-off-pk-gsp-kwh', 'winter-off-pk-msp-kwh', 'winter-pk-gbp',
        'winter-pk-gsp-kwh', 'winter-pk-msp-kwh'] + list(TRIAD_TITLES) + \
        ['problem']

slot_names = [
    'winter-pk', 'winter-low-pk', 'winter-off-pk', 'summer-pk', 'night',
    'other']

slots = {}
for slot_name in slot_names:
    slots[slot_name] = {
        'msp-kwh': slot_name + '-msp-kwh', 'gsp-kwh': slot_name + '-gsp-kwh',
        'gbp': slot_name + '-gbp'}


def displaced_virtual_bill(supply_source):
    bill = supply_source.supplier_bill
    rate_sets = supply_source.supplier_rate_sets

    # just check that revolving works
    supply_source.revolve_to_3rd_party_used()
    supply_source.revolve_to_gen_used()

    for slot_name in slot_names:
        slot_keys = slots[slot_name]
        bill[slot_keys['msp-kwh']] = 0
        bill[slot_keys['gsp-kwh']] = 0


    supply_source.is_green = False
    chellow.duos.duos_vb(supply_source)
    chellow.ccl.ccl(supply_source)
    chellow.triad.hh(supply_source)
    chellow.triad.bill(supply_source)

    for hh in sorted(supply_source.hh_data, key=itemgetter('start-date')):
        is_weekday = hh['utc-day-of-week'] < 5
        if is_weekday and hh['utc-month'] in (1, 12) and \
                16 < hh['utc-decimal-hour'] <= 19:
            slot_key = 'winter-pk'
        elif is_weekday and hh['utc-month'] in (2, 11) and \
                16 < hh['utc-decimal-hour'] <= 19:
            slot_key = 'winter-low-pk'
        elif is_weekday and (hh['utc-month'] > 10 or hh['utc-month'] < 4) and \
                8 < hh['utc-decimal-hour'] <= 20:
            slot_key = 'winter-off-pk'
        elif is_weekday and (hh['utc-month'] > 3 or hh['utc-month'] < 11) and \
                8 < hh['utc-decimal-hour'] <= 20:
            slot_key = 'summer-pk'
        elif 0 < hh['utc-decimal-hour'] <= 7:
            slot_key = 'night'
        else:
            slot_key = 'other'
        slot_keys = slots[slot_key]
        bill[slot_keys['msp-kwh']] += hh['msp-kwh']
        bill[slot_keys['gsp-kwh']] += hh['gsp-kwh']
        rates = supply_source.hh_rate(
            db_id, hh['start-date'], 'gsp_gbp_per_kwh')
        bill[slot_keys['gbp']] += hh['gsp-kwh'] * rates[slot_name]
        if 'ccl-kwh' in hh:
            bill['ccl-kwh'] += hh['ccl-kwh']
            bill['ccl-gbp'] += hh['ccl-gbp']

    chellow.tlms.hh(supply_source)
    chellow.bsuos.hh(supply_source)
    chellow.system_price.hh(supply_source)

    for rate_name, rate_set in rate_sets.items():
        if len(rate_set) == 1:
            bill[rate_name] = rate_set.pop()

    for k in list(bill.keys()):
        if k.startswith('duos-reactive-'):
            del bill[k]

    bill['net-gbp'] = sum(
        v for k, v in sorted(bill.items()) if k[-4:] == '-gbp')


def virtual_bill(supply_source):
    chellow.duos.duos_vb(supply_source)
    chellow.ccl.ccl(supply_source)
    chellow.triad.hh(supply_source)
    chellow.triad.bill(supply_source)
    rate_sets = supply_source.supplier_rate_sets
    bill = supply_source.supplier_bill
    bill.update(
        {
            'net-gbp': 0, 'data-collection-gbp': 0, 'settlement-gbp': 0,
            'problem': ''})

    for slot_name in slot_names:
        slot_keys = slots[slot_name]
        bill[slot_keys['msp-kwh']] = 0
        bill[slot_keys['gsp-kwh']] = 0


    llfc_code = supply_source.llfc_code
    voltage_level = supply_source.voltage_level_code
    is_substation = supply_source.is_substation
    supply_capacity = supply_source.sc
    supply_source.is_green = False

    for hh in sorted(supply_source.hh_data, key=itemgetter('start-date')):
        is_weekday = hh['utc-day-of-week'] < 5
        if is_weekday and hh['utc-month'] in (1, 12) and \
                16 < hh['utc-decimal-hour'] <= 19:
            slot_key = 'winter-pk'
        elif is_weekday and hh['utc-month'] in (2, 11) and \
                16 < hh['utc-decimal-hour'] <= 19:
            slot_key = 'winter-low-pk'
        elif is_weekday and (hh['utc-month'] > 10 or \
                hh['utc-month'] < 4) and \
                8 < hh['utc-decimal-hour'] <= 20:
            slot_key = 'winter-off-pk'
        elif is_weekday and (hh['utc-month'] > 3 or \
                hh['utc-month'] < 11) and \
                8 < hh['utc-decimal-hour'] <= 20:
            slot_key = 'summer-pk'
        elif 0 < hh['utc-decimal-hour'] <= 7:
            slot_key = 'night'
        else:
            slot_key = 'other'
        slot_keys = slots[slot_key]
        bill[slot_keys['msp-kwh']] += hh['msp-kwh']
        bill[slot_keys['gsp-kwh']] += hh['gsp-kwh']

        if 'ccl-kwh' in hh:
            bill['ccl-kwh'] += hh['ccl-kwh']
            bill['ccl-gbp'] += hh['ccl-gbp']

    month_begin = Datetime(
        supply_source.start_date.year, supply_source.start_date.month, 1,
        tzinfo=pytz.utc)
    month_end = month_begin + relativedelta(months=1) - HH

    bill['data-collection-gbp'] += 5.89
    bill['settlement-gbp'] += 88

    chellow.tlms.hh(supply_source)
    chellow.bsuos.hh(supply_source)
    chellow.system_price.hh(supply_source)
    rates = supply_source.hh_rate(
        db_id, supply_source.finish_date, 'gsp_gbp_per_kwh')
    for slot_name in slot_names:
        slot_keys = slots[slot_name]
        bill[slot_keys['gbp']] = bill[slot_keys['gsp-kwh']] * rates[slot_name]

    for rate_name, rate_set in rate_sets.items():
        if len(rate_set) == 1:
            bill[rate_name] = rate_set.pop()

    bill['net-gbp'] = sum(
        v for k, v in sorted(bill.items()) if k.endswith('-gbp'))
""",
            'properties': "{}"},
        'status_code': 303},
    {
        'name': "Check that when there are gt 2 eras, the previous era is "
        "updated. Supply 1",
        'path': '/eras/15/edit',
        'method': 'post',
        'data': {
            'start_year': "2008",
            'start_month': "09",
            'start_day': "06",
            'start_hour': "00",
            'start_minute': "00",
            'is_ended': "false",
            'mop_contract_id': "32",
            'mop_account': "mc-22 0470 7514 535",
            'hhdc_contract_id': "29",
            'hhdc_account': "01",
            'msn': "",
            'pc_id': "9",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'exp_llfc_code': "581",
            'exp_mpan_core': "22 0470 7514 535",
            'exp_sc': "150",
            'exp_supplier_contract_id': "31",
            'exp_supplier_account': "010"},
        'status_code': 303},

    # Supply 1
    {
        'path': '/eras/14/edit',
        'regexes': [
            r'<select name="finish_day">\s*<option value="1">01</option>\s*'
            '<option value="2">02</option>\s*<option value="3">03</option>\s*'
            '<option value="4">04</option>\s*'
            '<option value="5" selected>05</option>']},
    {
        'name': "Supplies snapshot selector",
        'path': '/csv_supplies_snapshot',
        'status_code': 200},
    {
        'name': "Check supplies snapshot",
        'path': '/reports/33?date_year=2005&date_month=12&date_day=31&'
        'date_hour=23&date_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"001_FINISHED_watkinsexamplecom_supplies_snapshot\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '001_FINISHED_watkinsexamplecom_supplies_snapshot.csv',
        'tries': {'max': 10, 'period': 1},
        'status_code': 200,
        'regexes': [
            r'2005-12-31 23:30,CI005,Wheal Rodney,,,11,net,,_L,'
            '22,LV,nhh,no,05,803,5,0154,2,MOP Contract,'
            'mc-22 9974 3438 105,Dynamat data,dc-22 9974 3438 105,'
            'K87D74429,2005-10-06 00:00,,,,,false,false,'
            'false,false,false,false,22 9974 3438 105,20,540,'
            'PC 5-8 & HH S/S,Non half-hourlies 2007,341665,,,,,'
            ',,,,,']},

    {
        'name': "Check supplies snapshot mandatory kw",
        'path': '/reports/33?supply_id=1&date_year=2008&date_month=9&'
        'date_day=30&date_hour=23&date_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"002_FINISHED_watkinsexamplecom_supplies_snapshot\.csv"],
        'status_code': 200, },
    {
        'path': '/downloads/'
        '002_FINISHED_watkinsexamplecom_supplies_snapshot.csv',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r'Date,Physical Site Id,Physical Site Name,Other Site Ids,'
            r'Other Site Names,Supply Id,Source,Generator Type,GSP Group,'
            r'DNO Name,'
            r'Voltage Level,Metering Type,Mandatory HH,PC,MTC,CoP,SSC,'
            r'Number Of Registers,MOP Contract,Mop Account,HHDC Contract,'
            r'HHDC Account,Meter Serial Number,Meter Installation Date,'
            r'Latest Normal Meter Read Date,Latest Normal Meter Read Type,'
            r'Latest DC Bill Date,Latest MOP Bill Date,Import ACTIVE\?,'
            r'Import REACTIVE_IMPORT\?,Import REACTIVE_EXPORT\?,'
            r'Export ACTIVE\?,'
            r'Export REACTIVE_IMPORT\?,Export REACTIVE_EXPORT\?,'
            r'Import MPAN core,Import Agreed Supply Capacity \(kVA\),'
            r'Import LLFC Code,Import LLFC Description,'
            r'Import Supplier Contract,Import Supplier Account,'
            r'Import Mandatory kW,Latest Import Supplier Bill Date,'
            r'Export MPAN core,Export Agreed Supply Capacity \(kVA\),'
            r'Export LLFC Code,Export LLFC Description,'
            r'Export Supplier Contract,Export Supplier Account,'
            r'Export Mandatory kW,Latest Export Supplier Bill Date',

            r'2008-09-30 23:30,CH017,Parbola,,,1,net,,_L,22,'
            r'LV,hh,no,00,845,5,,,MOP Contract,'
            r'mc-22 0470 7514 535,HH contract,01,,2003-08-03 00:00,'
            r'hh,,,,true,true,false,true,false,true,,,'
            r',,,,1.866,,22 0470 7514 535,150,581,'
            r'Export \(LV\),Half-hourlies 2007,010,,'
            r'2007-02-28 23:30']},

    {
        'name': "Generate an orphaned hh data message. Supply 5",
        'path': '/eras/5/edit',
        'method': 'post',
        'data': {
            'start_year': "2010",
            'start_month': "08",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'is_ended': "false",
            'msn': "",
            'pc_id': "9",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'mop_contract_id': "32",
            'mop_account': "mc-22 0883 6932 301",
            'hhdc_contract_id': "29",
            'hhdc_account': "22 0883 6932 301",
            'imp_llfc_code': "570",
            'imp_mpan_core': "22 0883 6932 301",
            'imp_sc': "350",
            'imp_supplier_contract_id': "31",
            'imp_supplier_account': "01"},
        'status_code': 400,
        'regexes': [
            r"There are orphaned HH data between 2003-08-03 00:00 and "
            "2010-08-02 23:30\."]},

    # Generate similar one for ongoing orphaned data
    {
        'path': '/eras/5/edit',
        'method': 'post',
        'data': {
            'start_year': "2003",
            'start_month': "08",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'is_ended': "true",
            'finish_year': "2003",
            'finish_month': "08",
            'finish_day': "03",
            'finish_hour': "00",
            'finish_minute': "00",
            'msn': "",
            'pc_id': "9",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'mop_contract_id': "32",
            'mop_account': "mc-22 0883 6932 301",
            'hhdc_contract_id': "29",
            'hhdc_account': "22 0883 6932 301",
            'imp_llfc_code': "570",
            'imp_mpan_core': "22 0883 6932 301",
            'imp_sc': "350",
            'imp_supplier_contract_id': "31",
            'imp_supplier_account': "01"},
        'status_code': 400,
        'regexes': [
            r"There are orphaned HH data between 2003-08-03 00:30 and "
            "ongoing\."]},

    # Test deleting of supplier contracts
    {
        'name': "Create a new supplier contract",
        'path': '/supplier_contracts/add',
        'method': 'post',
        'data': {
            'participant_id': "485",  # RWED
            'name': "GDF",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'charge_script': "",
            'properties': "{}", },
        'regexes': [
            r"/supplier_contracts/35"],
        'status_code': 303},

    {
        'name': "Now delete the contract",
        'path': '/supplier_contracts/35/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'status_code': 303},

    {
        'name': "Check that it's really gone",
        'path': '/supplier_contracts/49',
        'status_code': 404},

    # Create an HHDC contract
    {
        'name': "Test deleting of HHDC contracts",
        'path': '/hhdc_contracts/add',
        'method': 'post',
        'data': {
            'participant_id': "527",  # UKDC
            'name': "Siemens Contract",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00"},
        'status_code': 303,
        'regexes': [
            r"/hhdc_contracts/36"]},

    {
        'name': "Now delete the contract",
        'path': '/hhdc_contracts/36/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'status_code': 303},

    # Check that it's really gone
    {
        'path': '/hhdc_contracts/36',
        'status_code': 404},

    # Load in march's HH data
    {
        'name': "Check TRIAD calculation for March",
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh_data_long.csv'},
        'status_code': 303,
        'regexes': [
            r"/general_imports/12"]},
    {
        'path': '/general_imports/12',
        'tries': {'max': 20, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"The file has been imported successfully\."]},

    {
        'path': '/reports/291?supply_id=7&start_year=2009&start_month=03&'
        'start_day=01&start_hour=00&start_minute=0&finish_year=2009&'
        'finish_month=03&finish_day=31&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"003_FINISHED_watkinsexamplecom_supply_virtual_bills_7\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '003_FINISHED_watkinsexamplecom_supply_virtual_bills_7.csv',
        'regexes': [
            r'Imp MPAN Core,Exp MPAN Core,Site Code,Site Name,'
            'Account,From,To,,mop-net-gbp,mop-problem,,'
            'dc-net-gbp,dc-problem,,imp-supplier-net-gbp,'
            'imp-supplier-tlm,imp-supplier-ccl-kwh,'
            'imp-supplier-ccl-rate,imp-supplier-ccl-gbp,'
            'imp-supplier-data-collection-gbp,'
            'imp-supplier-duos-availability-kva,'
            'imp-supplier-duos-availability-days,'
            'imp-supplier-duos-availability-rate,'
            'imp-supplier-duos-availability-gbp,'
            'imp-supplier-duos-excess-availability-kva,'
            'imp-supplier-duos-excess-availability-days,'
            'imp-supplier-duos-excess-availability-rate,'
            'imp-supplier-duos-excess-availability-gbp,'
            'imp-supplier-duos-day-kwh,imp-supplier-duos-day-gbp,'
            'imp-supplier-duos-night-kwh,imp-supplier-duos-night-gbp,'
            'imp-supplier-duos-reactive-rate,'
            'imp-supplier-duos-reactive-gbp,'
            'imp-supplier-duos-standing-gbp,imp-supplier-settlement-gbp,'
            'imp-supplier-night-msp-kwh,imp-supplier-night-gsp-kwh,'
            'imp-supplier-night-gbp,imp-supplier-other-msp-kwh,'
            'imp-supplier-other-gsp-kwh,imp-supplier-other-gbp,'
            'imp-supplier-summer-pk-msp-kwh,'
            'imp-supplier-summer-pk-gsp-kwh,imp-supplier-summer-pk-gbp,'
            'imp-supplier-winter-low-pk-msp-kwh,'
            'imp-supplier-winter-low-pk-gsp-kwh,'
            'imp-supplier-winter-low-pk-gbp,'
            'imp-supplier-winter-off-pk-msp-kwh,'
            'imp-supplier-winter-off-pk-gsp-kwh,'
            'imp-supplier-winter-off-pk-gbp,'
            'imp-supplier-winter-pk-msp-kwh,'
            'imp-supplier-winter-pk-gsp-kwh,imp-supplier-winter-pk-gbp,'
            'imp-supplier-bsuos-kwh,imp-supplier-bsuos-rate,'
            'imp-supplier-bsuos-gbp,imp-supplier-triad-actual-1-date,'
            'imp-supplier-triad-actual-1-msp-kw,'
            'imp-supplier-triad-actual-1-status,'
            'imp-supplier-triad-actual-1-laf,'
            'imp-supplier-triad-actual-1-gsp-kw,'
            'imp-supplier-triad-actual-2-date,'
            'imp-supplier-triad-actual-2-msp-kw,'
            'imp-supplier-triad-actual-2-status,'
            'imp-supplier-triad-actual-2-laf,'
            'imp-supplier-triad-actual-2-gsp-kw,'
            'imp-supplier-triad-actual-3-date,'
            'imp-supplier-triad-actual-3-msp-kw,'
            'imp-supplier-triad-actual-3-status,'
            'imp-supplier-triad-actual-3-laf,'
            'imp-supplier-triad-actual-3-gsp-kw,'
            'imp-supplier-triad-actual-gsp-kw,'
            'imp-supplier-triad-actual-rate,'
            'imp-supplier-triad-actual-gbp,'
            'imp-supplier-triad-estimate-1-date,'
            'imp-supplier-triad-estimate-1-msp-kw,'
            'imp-supplier-triad-estimate-1-status,'
            'imp-supplier-triad-estimate-1-laf,'
            'imp-supplier-triad-estimate-1-gsp-kw,'
            'imp-supplier-triad-estimate-2-date,'
            'imp-supplier-triad-estimate-2-msp-kw,'
            'imp-supplier-triad-estimate-2-status,'
            'imp-supplier-triad-estimate-2-laf,'
            'imp-supplier-triad-estimate-2-gsp-kw,'
            'imp-supplier-triad-estimate-3-date,'
            'imp-supplier-triad-estimate-3-msp-kw,'
            'imp-supplier-triad-estimate-3-status,'
            'imp-supplier-triad-estimate-3-laf,'
            'imp-supplier-triad-estimate-3-gsp-kw,'
            'imp-supplier-triad-estimate-gsp-kw,'
            'imp-supplier-triad-estimate-rate,'
            'imp-supplier-triad-estimate-months,'
            'imp-supplier-triad-estimate-gbp,'
            'imp-supplier-triad-all-estimates-months,'
            'imp-supplier-triad-all-estimates-gbp'
            ',imp-supplier-problem',
            r'22 4862 4512 332,,CH023,Treglisson,11640077,'
            r'2009-03-01 00:00,2009-03-31 23:30,,10,,,10,,,'
            r'10614.409553652016,,148925.71000000002,0.00456,'
            r'679.1012375999993,5.89,230,31,0.0368,262.384,'
            r'169.72000000000003,31,0.0368,193.616576,'
            r'105487.43999999983,770.0583120000015,43438.26999999999,'
            r'112.93950200000005,0.0033,0.0,,88,43401.25000000001,'
            r'46092.12750000003,288.79483406400016,54364.72999999998,'
            r'57735.34326,361.746566729856,0,0,0.0,0,0,0.0,'
            r'51159.730000000054,54331.63325999999,340.4202813538559,'
            r'0,0,0.0,159627.38110258686,,146.91999204976776,'
            r'2009-01-06 17:00,288.82,A,1.07,309.0374,'
            r'2008-12-01 17:00,384.44,A,1.07,411.35080000000005,'
            r'2008-12-15 17:00,185.36,A,1.07,198.33520000000001,'
            r'306.2411333333334,25.212997,7721.256776009935,'
            r'2007-12-17 17:00,0,X,1.07,0.0,2008-01-03 17:00,'
            r'43.6,A,1.062,46.303200000000004,2007-11-26 17:00,0,'
            r'X,1.07,0.0,15.434400000000002,25.212997,1,'
            r'32.42895674140001,12,-389.14748089680006,',
            r"text/csv",
            r"supply_virtual_bills_7.csv"],
        'status_code': 200},

    # Try looking at it using the TRIAD report
    {
        'path': '/reports/41?supply_id=4&year=2010',
        'status_code': 200,
        'regexes': [
            r'CI005,"Wheal Rodney","1",net,"","22 6158 2968 220",'
            r'"2010-01-07 17:00","0","X","1.058","0.0","2010-01-25 17:00","0",'
            r'"X","1.058","0.0","2009-12-15 17:00","0","X","1.058","0.0",'
            r'"0.0","25.631634000000002","0.0","22 3479 7618 470",'
            r'"2010-01-07 17:00","0","X","1.058","0.0","2010-01-25 17:00","0",'
            r'"X","1.058","0.0","2009-12-15 17:00","0","X","1.058","0.0",'
            r'"0.0","25.631634000000002","0.0"']},
    {
        'name': "Check we can delete a rate script (when it's not the only "
        "one). Supplier contract 33.",
        'path': '/supplier_rate_scripts/100/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'status_code': 303},
    {
        'name': "Try 'Supply MPAN Months' report.",
        'path': '/supplies/2/months?is_import=true&year=2014&years=1',
        'regexes': [
            r"&raquo;\s*Import\s*data by month"],
        'status_code': 200},
    {
        'name': "Try 'Supply Raw HH Data' report.",
        'path': '/supplies/1/hh_data?months=1&finish_year=2008&'
        'finish_month=07',
        'regexes': [
            r'<option value="07" selected>07</option>'],
        'status_code': 200},
    {
        'name': "Try site graph report.",
        'path': '/sites/7/used_graph?finish_year=2008&finish_month=7&months=1',
        'status_code': 200},
    {
        'name': "Try generation graph report.",
        'path': '/sites/7/gen_graph?finish_year=2008&finish_month=7&months=1',
        'status_code': 200},
    {
        'name': "Try 'Site HH bulk figures' report.",
        'path': '/reports/29?site_id=5&type=used&months=1&finish_year=2008&'
        'finish_month=01',
        'regexes': [
            r"CH023,used,2008-01-01,3.77"],
        'status_code': 200},
    {
        'name': "Try HHDC virtual bills.",
        'path': '/reports/81?hhdc_contract_id=29&months=1&end_year=2008&'
        'end_month=7',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"004_FINISHED_watkinsexamplecom_hhdc_virtual_bills\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '004_FINISHED_watkinsexamplecom_hhdc_virtual_bills.csv',
        'regexes': [
            r'Import MPAN Core,Export MPAN Core,Start Date,Finish Date,'
            r'net-gbp',
            r'22 9205 6799 106,22 0470 7514 535,2008-07-01 00:00,'
            r'2008-07-06 23:30,,$'],
        'status_code': 200},

    # Can we make a supply have source sub and view site level hh data okay?
    {
        'name': "CSV Sites HH Data",
        'path': '/supplies/1/edit',
        'method': 'post',

        # Can we update a supply name?

        # Can we update a supply source?
        'data': {
            'name': "Hello",
            'source_id': "2",
            'generator_type_id': "1",
            'gsp_group_id': "11"},
        'regexes': [
            r"/supplies/1"],
        'status_code': 303},
    {
        'path': '/reports/183?start_year=2008&start_month=07&start_day=1&'
        'start_hour=0&start_minute=0&finish_year=2008&finish_month=07&'
        'finish_day=31&finish_hour=23&finish_minute=30',
        'status_code': 200},
    {
        'name': "CSV Supplies Duration",
        'path': '/reports/149?start_year=2009&start_month=03&start_day=1&'
        'start_hour=0&start_minute=0&finish_year=2009&finish_month=03&'
        'finish_day=31&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"005_FINISHED_watkinsexamplecom_supplies_duration\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '005_FINISHED_watkinsexamplecom_supplies_duration.csv',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r'"7","1","net","","CH023","Treglisson","2009-03-01 00:00",'
            r'"2009-03-31 23:30","00","845","5","","0","hh",540,'
            r'22 4862 4512 332,230,Half-hourlies 2007,148925.71000000002,0,'
            r'158159.10402,399.72,2009-03-13 08:00,None,0,,,,,0,0,,0,,None,'
            r'1488']},

    # Insert rate script
    {
        'name': "Manipulate dno contracts",
        'path': '/dno_contracts/13/add_rate_script',
        'method': 'post',
        'data': {
            # DNO 10
            'start_year': "2010",
            'start_month': "05",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00"},
        'regexes': [
            r"/dno_rate_scripts/104"],
        'status_code': 303},

    {
        'path': '/dno_rate_scripts/104',
        'status_code': 200},

    # Test bad syntax gives an error
    {
        'path': '/dno_rate_scripts/104/edit',
        'method': 'post',
        'data': {
            'start_year': "2010",
            'start_month': "05",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00",
            'script': "/0erk",
            'update': "Update"},
        'status_code': 400},

    # Delete rate script
    {
        'path': '/dno_rate_scripts/104/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'status_code': 303},
    {
        'name': "CSV Sites Monthly Duration",
        'path': '/reports/161?site_id=5&months=1&finish_year=2009&'
        'finish_month=03',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 40, 'period': 1},
        'regexes': [
            r"006_FINISHED_watkinsexamplecom_site_monthly_duration_for_"
            r"CH023_1_to_2009_3\.csv"],
        'status_code': 200},
    {
        'name': "Unified Supplies Monthly Duration",
        'path': '/reports/247?site_id=5&months=1&finish_year=2009&'
        'finish_month=03',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 40, 'period': 1},
        'regexes': [
            r'007_FINISHED_watkinsexamplecom_unified_supplies_monthly_'
            r'duration_20090301_0000_for_1_months_site_CH023\.ods'],
        'status_code': 200},
    {
        'name': "CSV Sites TRIAD",
        'path': '/reports/181?site_id=3&year=2010',
        'regexes': [
            "Site Code,",
            '"CI005","Wheal Rodney",2010-01-07 17:00,'],
        'status_code': 200},

    # See if it handles the case where there isn't an import virtual bill
    # function.
    {
        'name': "CSV Sites Monthly Duration",
        'path': '/reports/161?site_id=4&months=1&finish_year=2009&'
        'finish_month=04',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'regexes': [
            r"008_FINISHED_watkinsexamplecom_site_monthly_duration_for_"
            r"CI017_1_to_2009_4\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '008_FINISHED_watkinsexamplecom_site_monthly_duration_for_'
        'CI017_1_to_2009_4.csv',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"Site Id,Site Name,Associated Site Ids,Sources,Generator Types,"
            "Month,Metered Imported kWh,Metered Displaced kWh,"
            "Metered Exported kWh,Metered Used kWh,Metered Parasitic kWh,"
            "Metered Generated kWh,Metered 3rd Party Import kWh,"
            "Metered 3rd Party Export kWh,Metered Imported GBP,"
            "Metered Displaced GBP,Metered Exported GBP,Metered Used GBP,"
            "Metered 3rd Party Import GBP,Billed Imported kWh,"
            "Billed Imported GBP,Metering Type,Problem",
            r'"CI017","Roselands","","net","","2009-04-30 23:30","0.0","0",'
            r'"0","0.0","0","0","0","0","2821.89","0","0","2821.89","0","0",'
            r'"0","hh","'
            "Can't find the virtual_bill function in the supplier "
            'contract. "']},

    # See if unified report handles the case where there isn't an import
    # virtual bill function.
    {
        'name': "Unified Supplies Monthly Duration - no virtual bill function",
        'path': '/reports/247?site_id=4&months=1&finish_year=2009&'
        'finish_month=04',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'regexes': [
            r'009_FINISHED_watkinsexamplecom_unified_supplies_monthly_'
            r'duration_20090401_0000_for_1_months_site_CI017\.ods'],
        'status_code': 200},
    {
        'path': '/downloads/'
        '009_FINISHED_watkinsexamplecom_unified_supplies_monthly_'
        'duration_20090401_0000_for_1_months_site_CI017.ods',
        'status_code': 200,
        'regexes': [
            r'<table:table table:name="Supply Level">\s*'
            r'<table:table-column/>\s*'
            r'<table:table-row>\s*'
            r'<table:table-cell office:string-value="imp-mpan-core" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="exp-mpan-core" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="metering-type" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="source" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="generator-type" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="supply-name" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="msn" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="pc" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="site-id" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="site-name" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="associated-site-ids" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="month" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="import-net-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="export-net-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="import-gen-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="export-gen-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="import-3rd-party-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="export-3rd-party-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="displaced-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="used-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="used-3rd-party-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="import-net-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="export-net-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="import-gen-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="export-gen-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="import-3rd-party-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="export-3rd-party-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="displaced-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="used-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="used-3rd-party-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="billed-import-net-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="billed-import-net-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="mop-net-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="mop-problem" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="dc-net-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="dc-problem" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-net-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-tlm" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-ccl-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-ccl-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-ccl-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-data-collection-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-availability-kva" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-availability-days" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-availability-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-availability-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-excess-availability-kva" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-excess-availability-days"'
            r' office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-excess-availability-rate"'
            r' office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-excess-availability-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-day-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-day-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-night-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-night-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-reactive-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-reactive-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-standing-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-settlement-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-night-msp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-night-gsp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-night-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-other-msp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-other-gsp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-other-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-summer-pk-msp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-summer-pk-gsp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-summer-pk-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-winter-low-pk-msp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-winter-low-pk-gsp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-winter-low-pk-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-winter-off-pk-msp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-winter-off-pk-gsp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-winter-off-pk-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-winter-pk-msp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-winter-pk-gsp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-winter-pk-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-bsuos-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-bsuos-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-bsuos-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-actual-1-date" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-actual-1-msp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-actual-1-status" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-actual-1-laf" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-actual-1-gsp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-actual-2-date" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-actual-2-msp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-actual-2-status" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-actual-2-laf" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-actual-2-gsp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-actual-3-date" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-actual-3-msp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-actual-3-status" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-actual-3-laf" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-actual-3-gsp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-actual-gsp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-actual-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-actual-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-estimate-1-date" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-estimate-1-msp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-estimate-1-status" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-estimate-1-laf" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-estimate-1-gsp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-estimate-2-date" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-estimate-2-msp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-estimate-2-status" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-estimate-2-laf" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-estimate-2-gsp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-estimate-3-date" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-estimate-3-msp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-estimate-3-status" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-estimate-3-laf" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-estimate-3-gsp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-estimate-gsp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-estimate-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-estimate-months" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-estimate-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-all-estimates-months" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-triad-all-estimates-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-problem" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="exp-supplier-net-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="exp-supplier-tlm" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="exp-supplier-ccl-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="exp-supplier-ccl-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="exp-supplier-ccl-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-data-collection-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-duos-availability-kva" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-duos-availability-days" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-duos-availability-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-duos-availability-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-duos-excess-availability-kva" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-duos-excess-availability-days"'
            r' office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-duos-excess-availability-rate"'
            r' office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-duos-excess-availability-gbp"'
            r' office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-duos-day-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-duos-day-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-duos-night-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-duos-night-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-duos-reactive-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-duos-reactive-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-duos-standing-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-settlement-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-night-msp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-night-gsp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="exp-supplier-night-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-other-msp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-other-gsp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="exp-supplier-other-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-summer-pk-msp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-summer-pk-gsp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-summer-pk-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-winter-low-pk-msp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-winter-low-pk-gsp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-winter-low-pk-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-winter-off-pk-msp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-winter-off-pk-gsp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-winter-off-pk-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-winter-pk-msp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-winter-pk-gsp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-winter-pk-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="exp-supplier-bsuos-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="exp-supplier-bsuos-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="exp-supplier-bsuos-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-actual-1-date" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-actual-1-msp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-actual-1-status" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-actual-1-laf" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-actual-1-gsp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-actual-2-date" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-actual-2-msp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-actual-2-status" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-actual-2-laf" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-actual-2-gsp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-actual-3-date" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-actual-3-msp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-actual-3-status" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-actual-3-laf" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-actual-3-gsp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-actual-gsp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-actual-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-actual-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-estimate-1-date" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-estimate-1-msp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-estimate-1-status" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-estimate-1-laf" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-estimate-1-gsp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-estimate-2-date" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-estimate-2-msp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-estimate-2-status" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-estimate-2-laf" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-estimate-2-gsp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-estimate-3-date" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-estimate-3-msp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-estimate-3-status" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-estimate-3-laf" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-estimate-3-gsp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-estimate-gsp-kw" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-estimate-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-estimate-months" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-estimate-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-all-estimates-months" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-triad-all-estimates-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="exp-supplier-problem" '
            r'office:value-type="string"/>\s*'
            r'</table:table-row>\s*'
            r'<table:table-row>\s*',

            r'<table:table-row>\s*'
            r'<table:table-cell office:string-value="22 6354 2983 570" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="hh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="net" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="1" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="00" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="CI017" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Roselands" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2009-04-30T23:30:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="9"/>\s*'
            r'<table:table-cell office:value="2804.89" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="6"/>\s*'
            r'<table:table-cell office:value="2804.89" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="10" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="10" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="2784.89" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0047" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="5.89" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="2300" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="30" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.039" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="2691.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0042" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="88" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="18"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2009-01-06T17:00:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.079" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2008-12-01T17:00:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.079" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2008-12-15T17:00:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.079" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="25.631634" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="1" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'</table:table-row>\s*'
            r'</table:table>\s*'
            r'</office:spreadsheet>',

            r"The supplier contract Non half-hourlies 2007 "
            r"doesn't have the virtual_bill\(\) function."]},

    {
        'name': "Update the supplier contract",
        'path': '/supplier_contracts/33/edit',
        'method': 'post',
        'data': {
            'party_id': "22",  # BIZZ
            'name': "Half-hourlies 2013",
            'charge_script': """
from operator import itemgetter
import datetime
from dateutil.relativedelta import relativedelta
import pytz
from sqlalchemy import or_
import chellow.duos
import chellow.ccl
import chellow.triad
import chellow.tlms
import chellow.rcrc
import chellow.bsuos
import chellow.aahedc
import chellow.ro


def virtual_bill_titles():
    return [
        'net-gbp', 'tlm', 'ccl-kwh', 'ccl-rate', 'ccl-gbp',
        'data-collection-gbp', 'duos-availability-kva',
        'duos-availability-days', 'duos-availability-rate',
        'duos-availability-gbp', 'duos-excess-availability-kva',
        'duos-excess-availability-days', 'duos-excess-availability-rate',
        'duos-excess-availability-gbp','duos-green-kwh', 'duos-green-rate',
        'duos-green-gbp', 'duos-green-kwh', 'duos-green-rate',
        'duos-amber-gbp', 'duos-amber-kwh', 'duos-red-rate', 'duos-red-gbp',
        'duos-reactive-kvarh', 'duos-reactive-rate', 'duos-reactive-gbp',
        'duos-fixed-days', 'duos-fixed-rate', 'duos-fixed-gbp',
        'settlement-gbp', 'aahedc-msp-kwh', 'aahedc-gsp-kwh', 'aahedc-rate',
        'aahedc-gbp', 'rcrc-kwh', 'rcrc-rate', 'rcrc-gbp', 'night-msp-kwh',
        'night-gsp-kwh', 'night-gbp', 'other-msp-kwh', 'other-gsp-kwh',
        'other-gbp', 'summer-pk-msp-kwh', 'summer-pk-gsp-kwh', 'summer-pk-gbp',
        'winter-low-pk-msp-kwh', 'winter-low-pk-gsp-kwh', 'winter-low-pk-gbp',
        'winter-off-pk-msp-kwh', 'winter-off-pk-gsp-kwh', 'winter-off-pk-gbp',
        'winter-pk-msp-kwh', 'winter-pk-gsp-kwh', 'winter-pk-gbp', 'bsuos-kwh',
        'bsuos-rate', 'bsuos-gbp', 'triad-actual-1-date',
        'triad-actual-1-msp-kw', 'triad-actual-1-status', 'triad-actual-1-laf',
        'triad-actual-1-gsp-kw', 'triad-actual-2-date',
        'triad-actual-2-msp-kw', 'triad-actual-2-status', 'triad-actual-2-laf',
        'triad-actual-2-gsp-kw', 'triad-actual-3-date',
        'triad-actual-3-msp-kw', 'triad-actual-3-status', 'triad-actual-3-laf',
        'triad-actual-3-gsp-kw', 'triad-actual-gsp-kw', 'triad-actual-rate',
        'triad-actual-gbp', 'triad-estimate-1-date', 'triad-estimate-1-msp-kw',
        'triad-estimate-1-status', 'triad-estimate-1-laf',
        'triad-estimate-1-gsp-kw', 'triad-estimate-2-date',
        'triad-estimate-2-msp-kw', 'triad-estimate-2-status',
        'triad-estimate-2-laf', 'triad-estimate-2-gsp-kw',
        'triad-estimate-3-date', 'triad-estimate-3-msp-kw',
        'triad-estimate-3-status', 'triad-estimate-3-laf',
        'triad-estimate-3-gsp-kw', 'triad-estimate-gsp-kw',
        'triad-estimate-rate', 'triad-estimate-months', 'triad-estimate-gbp',
        'triad-all-estimates-months', 'triad-all-estimates-gbp', 'problem']

def displaced_virtual_bill_titles():
    return [
        'bsuos-kwh', 'bsuos-rate', 'bsuos-gbp', 'ccl-kwh', 'ccl-rate',
        'ccl-gbp', 'duos-day-gbp', 'duos-day-kwh', 'duos-night-gbp',
        'duos-night-kwh', 'duos-reactive-gbp', 'duos-reactive-working',
        'net-gbp', 'duos-standing-gbp', 'night-gbp', 'night-gsp-kwh',
        'night-msp-kwh', 'other-gbp', 'other-gsp-kwh', 'other-msp-kwh',
        'summer-pk-gbp', 'summer-pk-gsp-kwh', 'summer-pk-msp-kwh', 'triad-gbp',
        'triad-working', 'winter-low-pk-gbp', 'winter-low-pk-gsp-kwh',
        'winter-low-pk-msp-kwh', 'winter-off-pk-gbp', 'winter-off-pk-gsp-kwh',
        'winter-off-pk-msp-kwh', 'winter-pk-gbp', 'winter-pk-gsp-kwh',
        'winter-pk-msp-kwh']

slot_names = [
    'winter-pk', 'winter-low-pk', 'winter-off-pk', 'summer-pk', 'night',
    'other']

slots = {}
for slot_name in slot_names:
    slots[slot_name] = {
        'msp-kwh': slot_name + '-msp-kwh', 'gsp-kwh': slot_name + '-gsp-kwh',
        'gbp': slot_name + '-gbp'}


def displaced_virtual_bill(supply_source):
    bill = supply_source.supplier_bill

    supply_source.is_green = False
    chellow.duos.duos_vb(supply_source)
    chellow.ccl.ccl(supply_source)
    chellow.triad.hh(supply_source)
    chellow.triad.bill(supply_source)

    for datum in sorted(supply_source.hh_data, key=itemgetter('start-date')):
        is_weekday = datum['start-date'].weekday() < 5
        if is_weekday and datum['utc-month'] in (1, 12) and \
                16 < datum['utc-decimal-hour'] <= 19:
            slot_key = 'winter-pk'
        elif is_weekday and datum['utc-month'] in (2, 11) and \
                16 < datum['utc-decimal-hour'] <= 19:
            slot_key = 'winter-low-pk'
        elif is_weekday and \
                (datum['utc-month'] > 10 or datum['utc-month'] < 4) and \
                8 < datum['utc-decimal-hour'] <= 20:
            slot_key = 'winter-off-pk'
        elif is_weekday and \
                (datum['utc-month'] > 3 or datum['utc-month'] < 11) and \
                8 < datum['utc-decimal-hour'] <= 20:
            slot_key = 'summer-pk'
        elif 0 < datum['utc-decimal-hour'] <= 7:
            slot_key = 'night'
        else:
            slot_key = 'other'
        slot_keys = slots[slot_key]
        bill[slot_keys['msp-kwh']] += datum['msp-kwh']
        bill[slot_keys['gsp-kwh']] += datum['gsp-kwh']
        if 'ccl-kwh' in datum:
            bill['ccl-kwh'] += datum['ccl-kwh']
            bill['ccl-gbp'] += datum['ccl-gbp']

    chellow.tlms.hh(supply_source)
    chellow.bsuos.hh(supply_source)
    chellow.aahedc.hh(supply_source)

    rates = supply_source.hh_rate(
        db_id, supply_source.finish_date, 'gsp_gbp_per_kwh')
    for slot_name in slot_names:
        slot_keys = slots[slot_name]
        bill[slot_keys['gbp']] = bill[slot_keys['gsp-kwh']] * rates[slot_name]

    for rate_name, rate_set in supply_source.supplier_rate_sets.items():
        if len(rate_set) == 1:
            bill[rate_name] = rate_set.pop()

    bill['net-gbp'] = sum(
        v for k, v in sorted(bill.items()) if k[-4:] == '-gbp')


def virtual_bill(supply_source):
    chellow.duos.duos_vb(supply_source)
    chellow.ccl.ccl(supply_source)
    chellow.triad.hh(supply_source)
    chellow.triad.bill(supply_source)
    chellow.tlms.hh(supply_source)
    chellow.rcrc.hh(supply_source)
    chellow.bsuos.hh(supply_source)
    chellow.aahedc.hh(supply_source)

    bill = supply_source.supplier_bill
    supply_source.is_green = False

    for hh in sorted(supply_source.hh_data, key=itemgetter('start-date')):
        is_weekday = hh['utc-day-of-week'] < 5 and \
            not hh['utc-is-bank-holiday']
        if is_weekday and hh['utc-month'] in (1, 12) and \
                16 < hh['utc-decimal-hour'] <= 19:
            slot_key = 'winter-pk'
        elif is_weekday and hh['utc-month'] in (2, 11) and \
                16 < hh['utc-decimal-hour'] <= 19:
            slot_key = 'winter-low-pk'
        elif is_weekday and \
                (hh['utc-month'] > 10 or hh['utc-month'] < 4) and \
                8 < hh['utc-decimal-hour'] <= 20:
            slot_key = 'winter-off-pk'
        elif is_weekday and \
                (hh['utc-month'] > 3 or hh['utc-month'] < 11) and \
                8 < hh['utc-decimal-hour'] <= 20:
            slot_key = 'summer-pk'
        elif 0 < hh['utc-decimal-hour'] <= 7:
            slot_key = 'night'
        else:
            slot_key = 'other'
        slot_keys = slots[slot_key]
        bill[slot_keys['msp-kwh']] += hh['msp-kwh']
        bill[slot_keys['gsp-kwh']] += hh['gsp-kwh']
        rates = supply_source.hh_rate(
            db_id, hh['start-date'], 'gsp_gbp_per_kwh')
        bill[slot_keys['gbp']] += hh['gsp-kwh'] * rates[slot_name]

        if 'ccl-kwh' in hh:
            bill['ccl-kwh'] += hh['ccl-kwh']
            bill['ccl-gbp'] += hh['ccl-gbp']

    bill['data-collection-gbp'] += 5.89
    bill['settlement-gbp'] += 88

    for rate_name, rate_set in supply_source.supplier_rate_sets.items():
        if len(rate_set) == 1:
            bill[rate_name] = rate_set.pop()

    bill['net-gbp'] = sum(
        v for k, v in sorted(bill.items()) if k[-4:] == '-gbp')

""",
            'properties': "{}"},
        'status_code': 303,
        'regexes': [
            r'/supplier_contracts/33']},
    {
        'path': '/supplier_contracts/34/edit',
        'method': 'post',
        'data': {
            'name': "Non half-hourlies 2007",
            'party_id': "664",  # HYDE
            'charge_script': """
def virtual_bill_titles():
    return ['net-gbp', 'vat-gbp', 'gross-gbp', 'sum-msp-kwh', 'problem']

def virtual_bill(supply_source):
    bill = supply_source.supplier_bill
    sum_msp_kwh = sum(h['msp-kwh'] for h in supply_source.hh_data)
    for rate_name, rate_set in supply_source.supplier_rate_sets.items():
        if len(rate_set) == 1:
            bill[rate_name] = rate_set.pop()
    bill.update(
        {
            'net-gbp': 0.0, 'vat-gbp':0.0, 'gross-gbp': 0.0,
            'sum-msp-kwh': sum_msp_kwh})
""",
            'properties': "{}"},
        'status_code': 303},
    {
        'name': "Site In View World",
        'path': '/sites/3',
        'status_code': 200,
        'regexes': [
            r'<a href="/supplies/2">view</a>',
            r'<a href="https://maps.google.com/maps\?q=CI005">Google Maps</a>',
            r'<option value="imp_net">Imported</option>',
            r'<form action="/reports/csv_site_hh_data">\s*'
            r'<fieldset>\s*'
            r'<legend>HH Data: HH Per Row Format</legend>']},

    # Show a dead supply. Supply 11
    {
        'name': "Show a dead supply. Supply 11. Mark as dead.",
        'path': '/eras/11/edit',
        'method': 'post',
        'data': {
            'start_year': "2005",
            'start_month': "10",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'is_ended': "true",
            'finish_year': "2010",
            'finish_month': "04",
            'finish_day': "13",
            'finish_hour': "23",
            'finish_minute': "30",
            'mop_contract_id': "32",
            'mop_account': "mc-22 9974 3438 105",
            'hhdc_contract_id': "29",
            'hhdc_account': "dc-22 9974 3438 105",
            'msn': "K87D74429",
            'pc_id': "5",
            'mtc_code': "803",
            'cop_id': "5",
            'ssc_code': "0154",
            'imp_llfc_code': "540",
            'imp_mpan_core': "22 9974 3438 105",
            'imp_sc': "20",
            'imp_supplier_contract_id': "34",
            'imp_supplier_account': "SA341665"},
        'status_code': 303},
    {
        'path': '/sites/3',
        'status_code': 200,
        'regexes': [
            r'<td>\s*'
            '<a href="/supplies/11">view</a>\s*'
            '</td>\s*<td>3</td>\s*<td>2005-10-03 00:00</td>\s*<td>\s*'
            '2010-04-13 23:30\s*</td>']},

    # Insert a 20 supply
    {
        'name': "Try a pre 2010-04-01 DNO 20 bill.",
        'path': '/sites/1/edit',
        'method': 'post',
        'data': {
            'source_id': "1",
            'name': "Reserve Supply",
            'start_year': "2003",
            'start_month': "08",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'msn': "",
            'gsp_group_id': "8",
            'pc_id': "9",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'mop_contract_id': "32",
            'mop_account': "mc-22 6354 2983 570",
            'hhdc_contract_id': "30",
            'hhdc_account': "01",
            'imp_llfc_code': "453",
            'imp_mpan_core': "20 6354 2983 571",
            'imp_sc': "2300",
            'imp_supplier_contract_id': "31",
            'imp_supplier_account': "141 5532",
            'insert': "insert"},
        'regexes': [
            r"/supplies/12"],
        'status_code': 303},

    # Add import related ACTIVE channel. Supply 12
    {
        'path': '/eras/16/add_channel',
        'method': 'post',
        'data': {
            'imp_related': "true",
            'channel_type': "ACTIVE"},
        'regexes': [
            r"/channels/42"],
        'status_code': 303},

    # Try out simple.csv hh import format.
    {
        'path': '/hhdc_contracts/30/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh.simple.csv'},
        'status_code': 303,
        'regexes': [
            r"/hhdc_contracts/30/hh_imports/0"]},
    {
        'path': '/hhdc_contracts/30/hh_imports/0',
        'tries': {},
        'regexes': [
            r"The import has completed.*successfully."],
        'status_code': 200},

    # Check that the first datum has been correctly loaded in
    {
        'path': '/supplies/7/hh_data?months=1&finish_year=2010&'
        'finish_month=02',
        'regexes': [
            r"<td>\s*2010-02-04 20:00\s*</td>\s*<td>30.4339</td>"],
        'status_code': 200},
    {
        'path': '/reports/291?supply_id=12&start_year=2009&start_month=3&'
        'start_day=01&start_hour=00&start_minute=0&finish_year=2009&'
        'finish_month=03&finish_day=31&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"010_FINISHED_watkinsexamplecom_supply_virtual_bills_12\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '010_FINISHED_watkinsexamplecom_supply_virtual_bills_12.csv',
        'regexes': [
            r'Imp MPAN Core,Exp MPAN Core,Site Code,Site Name,'
            'Account,From,To,,mop-net-gbp,mop-problem,,'
            'dc-net-gbp,dc-problem,,imp-supplier-net-gbp,'
            'imp-supplier-tlm,imp-supplier-ccl-kwh,'
            'imp-supplier-ccl-rate,imp-supplier-ccl-gbp,'
            'imp-supplier-data-collection-gbp,'
            'imp-supplier-duos-availability-kva,'
            'imp-supplier-duos-availability-days,'
            'imp-supplier-duos-availability-rate,'
            'imp-supplier-duos-availability-gbp,'
            'imp-supplier-duos-excess-availability-kva,'
            'imp-supplier-duos-excess-availability-days,'
            'imp-supplier-duos-excess-availability-rate,'
            'imp-supplier-duos-excess-availability-gbp,'
            'imp-supplier-duos-day-kwh,imp-supplier-duos-day-gbp,'
            'imp-supplier-duos-night-kwh,imp-supplier-duos-night-gbp,'
            'imp-supplier-duos-reactive-rate,'
            'imp-supplier-duos-reactive-gbp,'
            'imp-supplier-duos-standing-gbp,imp-supplier-settlement-gbp,'
            'imp-supplier-night-msp-kwh,imp-supplier-night-gsp-kwh,'
            'imp-supplier-night-gbp,imp-supplier-other-msp-kwh,'
            'imp-supplier-other-gsp-kwh,imp-supplier-other-gbp,'
            'imp-supplier-summer-pk-msp-kwh,'
            'imp-supplier-summer-pk-gsp-kwh,imp-supplier-summer-pk-gbp,'
            'imp-supplier-winter-low-pk-msp-kwh,'
            'imp-supplier-winter-low-pk-gsp-kwh,'
            'imp-supplier-winter-low-pk-gbp,'
            'imp-supplier-winter-off-pk-msp-kwh,'
            'imp-supplier-winter-off-pk-gsp-kwh,'
            'imp-supplier-winter-off-pk-gbp,'
            'imp-supplier-winter-pk-msp-kwh,'
            'imp-supplier-winter-pk-gsp-kwh,imp-supplier-winter-pk-gbp,'
            'imp-supplier-bsuos-kwh,imp-supplier-bsuos-rate,'
            'imp-supplier-bsuos-gbp,imp-supplier-triad-actual-1-date,'
            'imp-supplier-triad-actual-1-msp-kw,'
            'imp-supplier-triad-actual-1-status,'
            'imp-supplier-triad-actual-1-laf,'
            'imp-supplier-triad-actual-1-gsp-kw,'
            'imp-supplier-triad-actual-2-date,'
            'imp-supplier-triad-actual-2-msp-kw,'
            'imp-supplier-triad-actual-2-status,'
            'imp-supplier-triad-actual-2-laf,'
            'imp-supplier-triad-actual-2-gsp-kw,'
            'imp-supplier-triad-actual-3-date,'
            'imp-supplier-triad-actual-3-msp-kw,'
            'imp-supplier-triad-actual-3-status,'
            'imp-supplier-triad-actual-3-laf,'
            'imp-supplier-triad-actual-3-gsp-kw,'
            'imp-supplier-triad-actual-gsp-kw,'
            'imp-supplier-triad-actual-rate,'
            'imp-supplier-triad-actual-gbp,'
            'imp-supplier-triad-estimate-1-date,'
            'imp-supplier-triad-estimate-1-msp-kw,'
            'imp-supplier-triad-estimate-1-status,'
            'imp-supplier-triad-estimate-1-laf,'
            'imp-supplier-triad-estimate-1-gsp-kw,'
            'imp-supplier-triad-estimate-2-date,'
            'imp-supplier-triad-estimate-2-msp-kw,'
            'imp-supplier-triad-estimate-2-status,'
            'imp-supplier-triad-estimate-2-laf,'
            'imp-supplier-triad-estimate-2-gsp-kw,'
            'imp-supplier-triad-estimate-3-date,'
            'imp-supplier-triad-estimate-3-msp-kw,'
            'imp-supplier-triad-estimate-3-status,'
            'imp-supplier-triad-estimate-3-laf,'
            'imp-supplier-triad-estimate-3-gsp-kw,'
            'imp-supplier-triad-estimate-gsp-kw,'
            'imp-supplier-triad-estimate-rate,'
            'imp-supplier-triad-estimate-months,'
            'imp-supplier-triad-estimate-gbp,'
            'imp-supplier-triad-all-estimates-months,'
            'imp-supplier-triad-all-estimates-gbp,'
            'imp-supplier-problem',
            r'20 6354 2983 571,,CI004,Lower Treave,141 5532,'
            r'2009-03-01 00:00,2009-03-31 23:30,,10,,,7,,,'
            r'2274.518581480245,,,0.00456,,5.89,2300,,,'
            r'2165.0,0,,,,0,0.0,86.9732,0.10262837600000001,'
            r',,14.91,88,86.9732,93.49619,0.585809728064,0,'
            r'0.0,0.0,0,0,0.0,0,0,0.0,0,0.0,0.0,0,0,'
            r'0.0,94.295292586311,,0.030143376181066044,'
            r'2009-01-06 17:00,0,X,1.095,0.0,2008-12-01 17:00,0,'
            r'X,1.095,0.0,2008-12-15 17:00,0,X,1.095,0.0,'
            r'0.0,22.19481,0.0,2007-12-17 17:00,0,X,1.095,0.0,'
            r'2008-01-03 17:00,0,X,1.079,0.0,2007-11-26 17:00,0,'
            r'X,1.095,0.0,0.0,22.19481,1,0.0,12,-0.0,'],
        'status_code': 200},

    # Check it works when the DNO rate script contains a double LLFC 453,470
    {
        'path': '/reports/291?supply_id=12&start_year=2009&start_month=6&'
        'start_day=01&start_hour=00&start_minute=0&finish_year=2009&'
        'finish_month=06&finish_day=30&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"011_FINISHED_watkinsexamplecom_supply_virtual_bills_12\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '011_FINISHED_watkinsexamplecom_supply_virtual_bills_12.csv',
        'regexes': [
            r'20 6354 2983 571,,CI004,Lower Treave,141 5532,'
            '2009-06-01 00:00,2009-06-30 23:30,'],
        'status_code': 200},

    # supply 12, era 16, channel 42
    {
        'path': '/hh_data/6773/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'status_code': 303},
    {
        'name': "Delete a supply.",
        'path': '/supplies/12/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'status_code': 303},

    # Create new supplier contract
    {
        'name': "Test importing of sse.edi bills",
        'path': '/supplier_contracts/add',
        'method': 'post',
        'data': {
            'participant_id': "54",  # COOP
            'name': "Non half-hourlies 2010",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00",
            'charge_script': """
def virtual_bill_titles():
    return ['net-gbp', 'sum-msp-kwh', 'problem']

def virtual_bill(supply_source):
    bill = supply_source.supplier_bill
    bill['consumption_info'] = supply_source.consumption_info
    bill['net-gbp'] =  0
    bill['sum-msp-kwh'] = 0

    for rate_name, rate_set in supply_source.supplier_rate_sets.items():
        if len(rate_set) == 1:
            bill[rate_name] = rate_set.pop()
    for h in supply_source.hh_data:
        msp_kwh = h['msp-kwh']
        bill['sum-msp-kwh'] += msp_kwh
        bill['net-gbp'] += msp_kwh * 0.1
        if h['utc-is-month-end']:
            pass
""",
            'properties': "{}"},
        'regexes': [
            r"/supplier_contracts/37"],
        'status_code': 303},

    # Add new era
    {
        'path': '/supplies/10/edit',
        'method': 'post',
        'data': {
            'start_year': "2010",
            'start_month': "01",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00",
            'insert_era': "Insert"},
        'regexes': [
            r"/supplies/10"],
        'status_code': 303},

    # Change to new supplier contract. Supply 10
    {
        'path': '/eras/17/edit',
        'method': 'post',
        'data': {
            'start_year': "2010",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'is_ended': "false",
            'mop_contract_id': "32",
            'mop_account': "mc-22 1065 3921 534",
            'hhdc_contract_id': "29",
            'hhdc_account': "dc-22 1065 3921 534",
            'msn': "I02D89150",
            'pc_id': "3",
            'mtc_code': "801",
            'cop_id': "6",
            'ssc_code': "0393",
            'imp_llfc_code': "110",
            'imp_mpan_core': "22 1065 3921 534",
            'imp_sc': "30",
            'imp_supplier_contract_id': "37",
            'imp_supplier_account': "SA342376000"},
        'status_code': 303},

    # Create a new batch
    {
        'path': '/supplier_contracts/37/add_batch',
        'method': 'post',
        'data': {
            'reference': "07-008",
            'description': "SSE batch"},
        'status_code': 303},

    # Supplier contract 50.
    {
        'path': '/supplier_bill_imports',
        'method': 'post',
        'data': {
            'supplier_batch_id': "5"},
        'files': {'import_file': 'test/bills.sse.edi'},
        'status_code': 303,
        'regexes': [
            r"/supplier_bill_imports/3"]},

    # Supplier contract 37.
    {
        'path': '/supplier_bill_imports/3',
        'tries': {},
        'regexes': [
            r"<th>Reference</th>\s*<th>Account</th>\s*<th>Bill Type</th>\s*"
            "<th>MPANs</th>\s*<th>Issue Date</th>\s*<th>Start Date</th>\s*"
            "<th>Finish Date</th>\s*<th>kWh</th>\s*<th>Net</th>\s*"
            "<th>VAT</th>\s*<th>Gross</th>\s*<th>R1 MPAN</th>\s*"
            "<th>R1 Meter Serial Number</th>\s*<th>R1 Coefficient</th>\s*"
            "<th>R1 Units</th>\s*<th>R1 TPR</th>\s*"
            "<th>R1 Previous Read Date</th>\s*"
            "<th>R1 Previous Read Value</th>\s*"
            "<th>R1 Previous Read Type</th>\s*<th>R1 Present Read Date</th>\s*"
            "<th>R1 Present Read Value</th>\s*<th>R1 Present Read Type</th>\s*"
            "<th>Breakdown</th>",
            r"<td>3423760005</td>\s*<td>SA342376000</td>\s*<td>N</td>\s*"
            "<td>\[u?&#39;03 801 110 22 10653921534&#39;\]</td>\s*"
            "<td>2010-05-12 00:00</td>\s*<td>2010-01-19 00:00</td>\s*"
            "<td>2010-04-20 23:30</td>\s*<td>253</td>\s*<td>36.16</td>\s*"
            "<td>1.8</td>\s*<td>0</td>\s*"
            "<td>03 801 110 22 1065 3921 534</td>\s*<td>K87D74429</td>\s*"
            "<td>1</td>\s*<td>kWh</td>\s*<td>00001</td>\s*"
            "<td>2010-01-18 23:30</td>\s*<td>16963</td>\s*<td>E</td>\s*"
            "<td>2010-04-20 23:30</td>\s*<td>17216</td>\s*<td>E</td>",
            r"All the bills have been successfully loaded and attached to the "
            "batch\."],

        'status_code': 200},

    {

        'name': "Test the supplier batch checking",
        'path': '/reports/111?batch_id=5',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"012_FINISHED_watkinsexamplecom_bill_check\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/012_FINISHED_watkinsexamplecom_bill_check.csv',
        'regexes': [
            r'batch,bill-reference,bill-type,bill-kwh,bill-net-gbp,'
            r'bill-vat-gbp,bill-start-date,bill-finish-date,bill-mpan-core,'
            r'site-code,site-name,covered-from,covered-to,covered-bills,'
            r'metered-kwh,covered-net-gbp,virtual-net-gbp,difference-net-gbp,'
            r'covered-sum-msp-kwh,virtual-sum-msp-kwh,covered-problem,'
            r'virtual-problem',
            r'07-008,3423760005,N,253,36.16,1.8,'
            r'2010-01-19 00:00,2010-04-20 23:30,22 1065 3921 534,'
            r'CI017,Roselands,2010-01-19 00:00,2010-04-20 23:30,10,'
            r'0.0,36.16,25.29999999999758,10.860000000002415,253.0,'
            r'252.99999999998357,,'],
        'status_code': 200},

    # Create a new site
    {
        'name': "Test reports for a supply-less site",
        'path': '/sites/add',
        'method': 'post',
        'data': {
            'code': "B00LG",
            'name': "Bieling"},
        'status_code': 303},
    {
        'path': '/sites/8/months?finish_year=2008&finish_month=07',
        'status_code': 200},
    {
        'name': "Check can import channel snag ignores okay.",
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/channel-snag-ignores.csv'},
        'status_code': 303,
        'regexes': [
            r"/general_imports/13"]},
    {
        'path': '/general_imports/13',
        'tries': {},

        # Check it's loaded ok
        'regexes': [
            r"The file has been imported successfully"],
        'status_code': 200},
    {
        'name': "Check can import site snag ignores okay.",
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/site-snag-ignores.csv'},
        'status_code': 303,
        'regexes': [
            r"/general_imports/14"]},
    {
        'path': '/general_imports/14',
        'tries': {},

        # Check it's loaded ok
        'regexes': [
            r"The file has been imported successfully"],
        'status_code': 200},


    # Test that generator is set to None if source is 'net'. },
    {
        'name': "Create a supply, and then delete it.",
        'path': '/sites/7/edit',
        'method': 'post',
        'data': {
            'source_id': "1",
            'generator_type_id': "1",
            'name': "Supply H8",
            'start_year': "2010",
            'start_month': "05",
            'start_day': "26",
            'start_hour': "05",
            'start_minute': "26",
            'msn': "",
            'gsp_group_id': "3",
            'mop_contract_id': "32",
            'mop_account': "mc-22 9879 0084 358",
            'hhdc_contract_id': "29",
            'hhdc_account': "dc-22 9879 0084 358",
            'pc_id': "9",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'imp_mpan_core': "22 9879 0084 358",
            'imp_llfc_code': "540",
            'imp_sc': "700",
            'imp_supplier_contract_id': "31",
            'imp_supplier_account': "d",
            'insert': "Insert"},
        'regexes': [
            r"/supplies/13"],
        'status_code': 303},

    # Check that the generator type 'chp' has been ignored.
    {
        'path': '/sites/7',
        'regexes': [
            r"<td>net</td>\s*<td>\s*</td>"],
        'status_code': 200},
    {
        'path': '/supplies/13/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'status_code': 303},

    # Create a new batch.
    {
        'name': "GDF CSV Bills",
        'path': '/supplier_contracts/31/add_batch',
        'method': 'post',
        'data': {
            'reference': "008",
            'description': "GDF CSV batch"},
        'status_code': 303},

    {
        'name': "Supplier contract 31",
        'path': '/supplier_bill_imports',
        'method': 'post',
        'data': {
            'supplier_batch_id': "6"},

        # File has a character outside 8 bits to check unicode handling
        'files': {'import_file': 'test/bills.gdf.csv'},
        'status_code': 303,
        'regexes': [
            r"/supplier_bill_imports/4"]},

    {
        'name': "Supplier contract 31, batch 6",
        'path': '/supplier_bill_imports/4',
        'tries': {},
        'regexes': [
            r"<th>Reference</th>\s*<th>Account</th>\s*<th>Bill Type</th>\s*"
            "<th>MPANs</th>\s*<th>Issue Date</th>\s*<th>Start Date</th>\s*"
            "<th>Finish Date</th>\s*<th>kWh</th>\s*<th>Net</th>\s*"
            "<th>VAT</th>\s*<th>Gross</th>\s*<th>Breakdown</th>",
            r"<td>KUH773</td>\s*<td>02</td>\s*<td>N</td>\s*<td>\[\]</td>\s*"
            "<td>2010-06-09 00:00</td>\s*<td>2010-05-01 00:00</td>\s*"
            "<td>2010-05-31 23:30</td>\s*<td>32124.5</td>\s*"
            r'<td>2219.41</td>\s*<td>388.4</td>\s*<td>2607.81</td>\s*'
            r'<td>\[\(&#39;aahedc-gbp&#39;, 5.29\),',
            r"All the bills have been successfully loaded and attached to "
            "the batch\."],
        'status_code': 200},

    # Check the bill appears correctly in batch view
    {
        'path': '/supplier_batches/6',
        'regexes': [
            r'\[<a href="/supplier_batches/6/edit">edit</a>\]',
            r"<td>2010-06-09 00:00</td>\s*<td>2010-05-01 00:00</td>\s*"
            "<td>2010-05-31 23:30</td>\s*<td>32124.5</td>\s*"
            "<td>2219.41</td>\s*<td>388.4</td>\s*<td>2607.81</td>",
            r'<a\s*href="/reports/111\?batch_id=6"\s*>Check Bills</a>'],
        'status_code': 200},
    {
        'name': "Test displaced virtual bill.",
        'path': '/reports/389?site_id=1&months=1&finish_year=2010&'
        'finish_month=06',
        'regexes': [
            r"Site Code,Site Name,Associated Site Ids,From,To,Gen Types,"
            "CHP kWh,LM kWh,Turbine kWh,PV kWh,net-gbp,bsuos-kwh,bsuos-rate,"
            "bsuos-gbp,ccl-kwh,ccl-rate,ccl-gbp,ssp-rate,tlm,duos-green-kwh,"
            "duos-green-rate,duos-green-gbp,duos-reactive-gbp,"
            "duos-reactive-working,duos-standing-gbp,night-gbp,night-gsp-kwh,"
            "night-msp-kwh,other-gbp,other-gsp-kwh,other-msp-kwh,"
            "summer-pk-gbp,summer-pk-gsp-kwh,summer-pk-msp-kwh,triad-gbp,"
            "triad-working,winter-low-pk-gbp,winter-low-pk-gsp-kwh,"
            "winter-low-pk-msp-kwh,winter-off-pk-gbp,winter-off-pk-gsp-kwh,"
            "winter-off-pk-msp-kwh,winter-pk-gbp,winter-pk-gsp-kwh,"
            "winter-pk-msp-kwh,triad-actual-1-date,triad-actual-1-msp-kw,"
            "triad-actual-1-status,triad-actual-1-laf,triad-actual-1-gsp-kw,"
            "triad-actual-2-date,triad-actual-2-msp-kw,triad-actual-2-status,"
            "triad-actual-2-laf,triad-actual-2-gsp-kw,triad-actual-3-date,"
            "triad-actual-3-msp-kw,triad-actual-3-status,triad-actual-3-laf,"
            "triad-actual-3-gsp-kw,triad-actual-gsp-kw,triad-actual-rate,"
            "triad-actual-gbp,triad-estimate-1-date,triad-estimate-1-msp-kw,"
            "triad-estimate-1-status,triad-estimate-1-laf,"
            "triad-estimate-1-gsp-kw,triad-estimate-2-date,"
            "triad-estimate-2-msp-kw,triad-estimate-2-status,"
            "triad-estimate-2-laf,triad-estimate-2-gsp-kw,"
            "triad-estimate-3-date,triad-estimate-3-msp-kw,"
            "triad-estimate-3-status,triad-estimate-3-laf,"
            "triad-estimate-3-gsp-kw,triad-estimate-gsp-kw,"
            "triad-estimate-rate,triad-estimate-months,triad-estimate-gbp,"
            "triad-all-estimates-months,triad-all-estimates-gbp,problem",
            r'"CI004","Lower Treave","","2010-06-01 00:00","2010-06-30 23:30",'
            '"chp","","","","","0.0","0.0","","0.0","","0.0047","","","","0",'
            '"0.0013","0.0","","","","0.0","0.0","0","0.0","0.0","0","0.0",'
            '"0.0","0","","","","0","0","","0","0","","0","0","","","","","",'
            '"","","","","","","","","","","","","","2010-01-07 17:00","0",'
            '"E","1.078","0.0","2010-01-25 17:00","0","E","1.078","0.0",'
            '"2009-12-15 17:00","0","E","1.078","0.0","0.0","26.057832","1",'
            '"0.0","","",""'],
        'status_code': 200},

    # Try a 12 month run
    {
        'path': '/reports/389?site_id=1&months=12&finish_year=2011&'
        'finish_month=06',
        'status_code': 200},
    {
        'name': "Test bulk ignore.",
        'path': '/hhdc_contracts/29/edit',
        'method': 'post',
        'data': {
            'ignore_year': "2008",
            'ignore_month': "09",
            'ignore_day': "01",
            'ignore_hour': "00",
            'ignore_minute': "00",
            'ignore_snags': "Ignore Snags"},
        'status_code': 303},
    {
        'name': "Check that a era can be deleted. Supply 1",
        'path': '/eras/14/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'status_code': 303},
    {
        'name': "Check a contract virtual bill that crosses a era boundary "
        "comes out correctly.",
        'path': '/reports/291?supply_id=11&start_year=2010&start_month=04&'
        'start_day=01&start_hour=00&start_minute=00&finish_year=2010&'
        'finish_month=04&finish_day=30&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"013_FINISHED_watkinsexamplecom_supply_virtual_bills_11\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '013_FINISHED_watkinsexamplecom_supply_virtual_bills_11.csv',
        'regexes': [
            r'Imp MPAN Core,Exp MPAN Core,Site Code,Site Name,'
            r'Account,From,To,,mop-net-gbp,mop-problem,,'
            r'dc-net-gbp,dc-problem,,imp-supplier-net-gbp,'
            r'imp-supplier-vat-gbp,imp-supplier-gross-gbp,'
            r'imp-supplier-sum-msp-kwh,imp-supplier-problem',
            r'22 9974 3438 105,,CI005,Wheal Rodney,SA341665,'
            r'2010-04-01 00:00,2010-04-13 23:30,,0,,,,,,'
            r'0.0,0.0,0.0,0.0,'],
        'status_code': 200},
    {
        'name': "NHH CSV import",
        'path': '/supplier_contracts/37/add_batch',
        'method': 'post',
        'data': {
            'reference': "07-002",
            'description': "nhh csv batch"},
        'status_code': 303},

    {
        'name': "Supplier contract 37",
        'path': '/supplier_bill_imports',
        'method': 'post',
        'data': {
            'supplier_batch_id': "7"},
        'files': {'import_file': 'test/bills-nhh.csv'},
        'status_code': 303,
        'regexes': [
            r"/supplier_bill_imports/5"]},

    {
        'name': "Supplier contract 37, batch 7",
        'path': '/supplier_bill_imports/5',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"All the bills have been successfully loaded and attached to "
            "the batch\."]},

    # Supplier contract 37, batch 7, bill 10
    {
        'path': '/reads/7/edit',
        'regexes': [
            r'31</option>\s*</select>\s*<select name="present_hour">\s*'
            '<option value="0">00</option>\s*<option value="1">01</option>\s*'
            '<option value="2">02</option>\s*<option value="3">03</option>\s*'
            '<option value="4">04</option>\s*<option value="5">05</option>\s*'
            '<option value="6">06</option>\s*<option value="7">07</option>\s*'
            '<option value="8">08</option>\s*<option value="9">09</option>\s*'
            '<option value="10">10</option>\s*'
            '<option value="11">11</option>\s*'
            '<option value="12">12</option>\s*'
            '<option value="13">13</option>\s*'
            '<option value="14">14</option>\s*'
            '<option value="15">15</option>\s*'
            '<option value="16">16</option>\s*'
            '<option value="17">17</option>\s*'
            '<option value="18">18</option>\s*'
            '<option value="19">19</option>\s*'
            '<option value="20">20</option>\s*'
            '<option value="21">21</option>\s*'
            '<option value="22">22</option>\s*'
            '<option value="23" selected>23</option>\s*'
            '</select>:<select name="present_minute">\s*'
            '<option value="0">00</option>\s*'
            '<option value="30" selected>30</option>\s*</select>',
            r'<input type="hidden" name="supplier_read_id" value="7">']},
    {
        'name': "Test viewers' search",
        'path': '/supplies?search_pattern=',
        'regexes': [
            r'<td>\s*'
            '<a href="/supplies/9">supply</a>\s*'
            '</td>\s*<td>P96C93722</td>',
            r"<td>\s*</td>\s*<td>\s*</td>\s*<td>\s*</td>\s*<td>\s*"
            "00 845 581\s*22 0470 7514 535\s*</td>"],
        'status_code': 200},

    {
        'name': "Check that searching for an account with a space works",
        'path': '/supplies?search_pattern=141%205532',
        'regexes': [
            r"/supplies/6"],
        'status_code': 307},

    {
        'name': "Check that searching on an MSN works",
        'path': '/supplies?search_pattern=P96C93722',
        'regexes': [
            r"/supplies/9"],
        'status_code': 307},
    {
        'name': "Check can view a supply.",
        'path': '/supplies/2',

        # Check there's a link to raw HH data
        'regexes': [
            r"/supplies/2/hh_data?",

            # Check we can see the site
            r'<a href="/sites/1" title="Lower Treave">CI004</a>',

            # Check a link to supplier bill is correct
            r'<a href="/supplier_bills/11">View</a>',

            # Check link to supply duration is correct
            r'<form action="/reports/149">\s*<fieldset>\s*'
            '<input type="hidden" name="supply_id"',
            r'<td rowspan="4">\s*'
            '<a href="/pcs/9" title="Half-'
            'hourly">00</a>\s*</td>\s*<td rowspan="4"></td>\s*'
            '<td rowspan="4">\s*'
            '<a href="/mtcs/52" title="HH '
            'COP5 And Above With Comms">845</a>\s*</td>'],
        'status_code': 200},

    # Supply 10
    {
        'name': "Check that if the end date of an era is altered, it can tell "
        "if there's a succeeding era.",
        'path': '/eras/10/edit',
        'method': 'post',
        'data': {
            'start_year': "2005",
            'start_month': "09",
            'start_day': "06",
            'start_hour': "00",
            'start_minute': "00",
            'is_ended': "true",
            'finish_year': "2010",
            'finish_month': "01",
            'finish_day': "03",
            'finish_hour': "23",
            'finish_minute': "30",
            'mop_contract_id': "32",
            'mop_account': "mc-22 1065 3921 534",
            'hhdc_contract_id': "30",
            'hhdc_account': "dc-22 1065 3921 534",
            'msn': "I02D89150",
            'pc_id': "3",
            'mtc_code': "801",
            'cop_id': "5",
            'ssc_code': "0393",
            'imp_llfc_code': "110",
            'imp_mpan_core': "22 1065 3921 534",
            'imp_sc': "30",
            'imp_supplier_contract_id': "34",
            'imp_supplier_account': "SA342376"},
        'status_code': 303},
    {
        'name': "Check that it works if a supply era is inserted by CSV "
        "before the beginning of a supply ",
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/era-insert.csv'},
        'status_code': 303,
        'regexes': [
            r"/general_imports/15"]},
    {
        'path': '/general_imports/15',
        'tries': {},

        # Check it's loaded ok
        'regexes': [
            r"The file has been imported successfully"],
        'status_code': 200},

    # Supply 9
    {
        'path': '/eras/20/edit',

        # Check the import supplier account is there
        'regexes': [
            r"341664"],
        'status_code': 200},
    {
        'name': "Check that the general import of register reads works.",
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/bills-general.csv'},
        'status_code': 303,
        'regexes': [
            r"/general_imports/16"]},
    {
        'path': '/general_imports/16',
        'tries': {},

        # Check it's loaded ok
        'regexes': [
            r"The file has been imported successfully"],
        'status_code': 200},
    {
        'path': '/supplier_bills/14',
        'tries': {},

        # Check it's loaded ok
        'regexes': [
            r'<td>\s*<a href="/reports/111\?bill_id=14">Check</a>\s*</td>',
            r'<td>38992</td>\s*<td>\s*<a title="Estimated"\s*'
            'href="/read_types/4">E</a>\s*</td>\s*'
            '<td>2007-01-17 00:00</td>\s*<td>39000\s*</td>\s*<td>\s*'
            '<a title="Estimated"\s*'
            'href="/read_types/4">E</a>\s*</td>'],
        'status_code': 200},
    {
        'name': "Check the 'update bill' page.",
        'path': '/supplier_bills/10/edit',
        'status_code': 200,
        'regexes': [
            r"type_id",
            r'<option value="2" selected>N Normal</option>',
            r'name="account" value="SA342376000"']},
    {
        'name': "Check the batch page.",
        'path': '/supplier_batches/5',
        'status_code': 200,
        'regexes': [
            r"<td>2010-01-19 00:00</td>\s*<td>2010-04-20 23:30</td>"]},
    {
        'name': "Test supply era update for a supply with 2 mpans.",
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/era-update-2-mpans.csv'},
        'status_code': 303,
        'regexes': [
            r"/general_imports/17"]},
    {
        'path': '/general_imports/17',
        'tries': {},

        # Check it's loaded ok
        'regexes': [
            r"The file has been imported successfully"],
        'status_code': 200},

    # Insert a new batch
    {
        'name': "Add batch to HHDC contract",
        'path': '/hhdc_contracts/29/add_batch',
        'method': 'post',
        'data': {
            'reference': "001-7t",
            'description': "hhdc batch"},
        'status_code': 303,
        'regexes': [
            r"/hhdc_batches/8"]},

    {
        'name': "Check that it's there to edit. HHDC contract 28",
        'path': '/hhdc_batches/8/edit',
        'status_code': 200},
    {
        'name': "View HHDC bill imports. Contract 28",
        'path': '/hhdc_bill_imports?hhdc_batch_id=8',
        'status_code': 200,
        'regexes': [
            r'<a href="/hhdc_batches/8">001-7t</a>']},
    {
        'name': "Try adding bills to the HHDC batch. Contract 28",
        'path': '/hhdc_bill_imports',
        'method': 'post',
        'data': {
            'hhdc_batch_id': "8"},
        'files': {'import_file': 'test/hhdc-bill.csv'},
        'status_code': 303,
        'regexes': [
            r"/hhdc_bill_imports/6"]},

    {
        'name': "Contract 29 batch 8",
        'path': '/hhdc_bill_imports/6',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"All the bills have been successfully loaded and attached to "
            "the batch\."]},

    {
        'name': "Add batch to MOP contract",
        'path': '/mop_contracts/32/add_batch',
        'method': 'post',
        'data': {
            'reference': "99/992",
            'description': "mop batch"},
        'status_code': 303,
        'regexes': [
            r"/mop_batches/9"]},

    {
        'name': "Check that it's there in edit mode. Contract 31",
        'path': '/mop_batches/9/edit',
        'status_code': 200,
        'regexes': [
            r'<input type="hidden" name="mop_batch_id" value="9">']},

    {
        'name': "Check confirm-delete page. Contract 32",
        'path': '/mop_batches/9/edit?confirm_delete=Delete',
        'status_code': 200,
        'regexes': [
            r'<input type="hidden" name="mop_batch_id" value="9">']},
    {
        'name': "Supplier Batch: confirm-delete page.",
        'path': '/supplier_batches/6/edit?confirm_delete=Delete',
        'status_code': 200,
        'regexes': [
            r'<a class="btn" href="/supplier_batches/6/edit">Cancel</a>']},

    {
        'name': "Check we can see it in 'view' mode. Contract 32",
        'path': '/mop_batches/9',
        'status_code': 200},

    # Mop contract 58
    {
        'name': "Try adding bills to the MOP batch",
        'path': '/mop_bill_imports',
        'method': 'post',
        'data': {
            'mop_batch_id': "9"},
        'files': {'import_file': 'test/mop-bill.csv'},
        'status_code': 303,
        'regexes': [
            r"/mop_bill_imports/7"]},

    # Mop contract 57, batch 9
    {
        'path': '/mop_bill_imports/7',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"All the bills have been successfully loaded and attached to "
            "the batch\."]},
    {
        'name': "If a new supply has a blank LLFC field, check it gives a "
        "good error message. Also make sure that site name doesn't change "
        "if supply name changes.",
        'path': '/sites/7/edit',
        'method': 'post',
        'data': {
            'source_id': "1",
            'name': "John Nash",
            'start_year': "2010",
            'start_month': "05",
            'start_day': "26",
            'start_hour': "00",
            'start_minute': "00",
            'msn': "",
            'gsp_group_id': "3",
            'mop_contract_id': "32",
            'mop_account': "mc-22 9879 0084 358",
            'hhdc_contract_id': "29",
            'hhdc_account': "dc-22 9879 0084 358",
            'pc_id': "9",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'imp_mpan_core': "22 9879 0084 358",
            'imp_llfc_code': "",
            'imp_sc': "700",
            'imp_supplier_contract_id': "31",
            'imp_supplier_account': "d",
            'insert': "Insert"},
        'regexes': [
            r"There is no LLFC with the code &#39;&#39; associated with the "
            "DNO 22\.",
            r'<input name="site_name" value="Parbola"'],
        'status_code': 400},
    {
        'name': "If a new supply has a blank import sc field, check it gives "
        "a good error message.",
        'path': '/sites/7/edit',
        'method': 'post',
        'data': {
            'source_id': "1",
            'name': "Supply 54",
            'start_year': "2010",
            'start_month': "05",
            'start_day': "26",
            'start_hour': "00",
            'start_minute': "00",
            'msn': "",
            'gsp_group_id': "3",
            'mop_contract_id': "32",
            'mop_account': "mc-22 9879 0084 358",
            'hhdc_contract_id': "29",
            'hhdc_account': "dc-22 9879 0084 358",
            'pc_id': "9",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'imp_mpan_core': "22 9879 0084 358",
            'imp_llfc_code': "570",
            'imp_sc': "",
            'imp_supplier_contract_id': "31",
            'imp_supplier_account': "d",
            'insert': "Insert"},
        'regexes': [
            r"Problem parsing the field imp_sc as an integer: invalid literal "
            "for int\(\) with base 10: "],
        'status_code': 400},
    {
        'name': "If a new supply has a blank MTC code field, check it gives "
        "a good error message.",
        'path': '/sites/7/edit',
        'method': 'post',
        'data': {
            'source_id': "1",
            'name': "Supply 54",
            'start_year': "2010",
            'start_month': "05",
            'start_day': "26",
            'start_hour': "00",
            'start_minute': "00",
            'msn': "",
            'gsp_group_id': "3",
            'mop_contract_id': "32",
            'mop_account': "mc-22 9879 0084 358",
            'hhdc_contract_id': "29",
            'hhdc_account': "dc-22 9879 0084 358",
            'pc_id': "9",
            'mtc_code': "",
            'cop_id': "5",
            'ssc_code': "",
            'imp_mpan_core': "22 9879 0084 358",
            'imp_llfc_code': "570",
            'imp_sc': "700",
            'imp_supplier_contract_id': "31",
            'imp_supplier_account': "d",
            'insert': "Insert"},
        'regexes': [
            r"The MTC code must be a whole number\.", ],
        'status_code': 400},
    {
        'name': "Try view page of meter payment types.",
        'path': '/meter_payment_types',
        'status_code': 200},
    {
        'name': "View a meter payment type",
        'path': '/meter_payment_types/1',
        'status_code': 200},
    {
        'name': "Try a monthly sites duration for a site with a 3rd party "
        "supply.",
        'path': '/sites/4/edit',
        'method': 'post',
        'data': {
            'source_id': "5",
            'name': "3",
            'start_year': "2010",
            'start_month': "05",
            'start_day': "26",
            'start_hour': "00",
            'start_minute': "00",
            'msn': "",
            'gsp_group_id': "3",
            'mop_contract_id': "32",
            'mop_account': "mc-22 9789 0534 938",
            'hhdc_contract_id': "29",
            'hhdc_account': "dc-22 9789 0534 938",
            'pc_id': "3",
            'mtc_code': "801",
            'cop_id': "5",
            'ssc_code': "393",
            'imp_mpan_core': "22 9789 0534 938",
            'imp_llfc_code': "110",
            'imp_sc': "0",
            'imp_supplier_contract_id': "37",
            'imp_supplier_account': "taa2",
            'insert': "Insert"},
        'regexes': [
            r"/supplies/16"],
        'status_code': 303},
    {
        'path': '/reports/161?site_id=4&months=1&finish_year=2010&'
        'finish_month=07',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'regexes': [
            r"014_FINISHED_watkinsexamplecom_site_monthly_duration_for_"
            r"CI017_1_to_2010_7.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '014_FINISHED_watkinsexamplecom_site_monthly_duration_for_'
        'CI017_1_to_2010_7.csv',
        'regexes': [
            r'"CI017","Roselands","","3rd-party,net","","2010-07-31 23:30",'
            r'"0.0","0","0","0.0","0","0","0.0","0","1633.3413999999993","0",'
            r'"0","1653.3413999999993","20.0","0","0","hh",""'],
        'status_code': 200},

    {
        'path': '/reports/247?site_id=4&months=1&finish_year=2010&'
        'finish_month=07',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'regexes': [
            r'015_FINISHED_watkinsexamplecom_unified_supplies_monthly_'
            r'duration_20100701_0000_for_1_months_site_CI017\.ods'],
        'status_code': 200},
    {
        'path': '/downloads/'
        '015_FINISHED_watkinsexamplecom_unified_supplies_monthly_'
        'duration_20100701_0000_for_1_months_site_CI017.ods',
        'regexes': [
            r'<table:table-row>\s*'
            r'<table:table-cell office:string-value="22 6354 2983 570" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="hh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="net" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="1" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="00" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="CI017" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Roselands" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2010-07-31T23:30:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="9"/>\s*'
            r'<table:table-cell office:value="1613.3413999999993" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="6"/>\s*'
            r'<table:table-cell office:value="1613.3413999999993" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="10" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="10" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="1593.3413999999993" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0047" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="5.89" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="2300" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="31" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.021" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="1497.2999999999993" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="31" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.021" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="4"/>\s*'
            r'<table:table-cell office:value="0.00326" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="88" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="18"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2010-01-07T17:00:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.078" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2010-01-25T17:00:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.078" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2009-12-15T17:00:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.078" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="26.057832" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="1" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0013" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.16146" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="31" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0694" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="2.151399999999999" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="10"/>\s*'
            r'</table:table-row>\s*'
            r'<table:table-row>\s*'
            r'<table:table-cell office:string-value="22 1065 3921 534" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="nhh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="net" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="2" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="I02D89150" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="03" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="CI017" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Roselands" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2010-07-31T23:30:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="6"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="20.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="6"/>\s*'
            r'<table:table-cell office:value="20.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="10" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="10" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="81"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="20"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'</table:table-row>\s*'
            r'<table:table-row>\s*'
            r'<table:table-cell office:string-value="22 9789 0534 938" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="nhh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="3rd-party" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="3" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="03" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="CI017" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Roselands" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2010-07-31T23:30:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" '
            r'table:number-columns-repeated="4"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>'
            r'<table:table-cell office:value="0.0" office:value-type="float"/>'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="5"/>'
            r'<table:table-cell office:value="20.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="20.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="10" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="10" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="81"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="20"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'</table:table-row>\s*'
            r'</table:table>'],
        'status_code': 200},
    {
        'name': "Try creating and deleting a rate script for a non-core "
        "contract (templater).",
        'path': '/non_core_contracts/1/add_rate_script',
        'method': 'post',
        'data': {
            'start_year': "2010",
            'start_month': "05",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00",
            'insert': "Insert"},
        'regexes': [
            r"/non_core_rate_scripts/106"],
        'status_code': 303},
    {
        'path': '/non_core_rate_scripts/106/edit?delete=Delete',
        'regexes': [
            r"Are you sure you want to delete this rate script\?"],
        'status_code': 200},
    {
        'path': '/non_core_rate_scripts/106/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'status_code': 303},
    {
        'path': '/non_core_rate_scripts/106',
        'status_code': 404},
    {
        'name': "Try adding a rate script before other rate scripts.",
        'path': '/non_core_contracts/1/add_rate_script',
        'method': 'post',
        'data': {
            'start_year': "1999",
            'start_month': "04",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00",
            'insert': "Insert"},
        'regexes': [
            r"/non_core_rate_scripts/107"],
        'status_code': 303},
    {
        'path': '/non_core_rate_scripts/107/edit',
        'regexes': [
            r'<input name="finish_year" maxlength="4" size="4" value="2000">',

            # Check that the start hour of a non-core rate script is correct."
            r'<select name="start_hour">\s*'
            '<option value="0" selected>00</option>'],
        'status_code': 200},
    {
        'path': '/non_core_rate_scripts/107/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'status_code': 303},

    {
        'name': "Adding a bill manually. Supplier contract 44",
        'path': '/supplier_batches/6/add_bill',
        'method': 'post',
        'data': {
            'mpan_core': "22 9813 2107 763",
            'reference': "KUH774",
            'issue_year': "2010",
            'issue_month': "12",
            'issue_day': "06",
            'issue_hour': "00",
            'issue_minute': "00",
            'start_year': "2010",
            'start_month': "12",
            'start_day': "06",
            'start_hour': "00",
            'start_minute': "00",
            'finish_year': "2010",
            'finish_month': "12",
            'finish_day': "06",
            'finish_hour': "00",
            'finish_minute': "00",
            'kwh': "0",
            'net': "0",
            'vat': "0",
            'gross': "0",
            'account': "02",
            'bill_type_id': "1",
            'breakdown': "{}"},
        'regexes': [
            r"/supplier_bills/18"],
        'status_code': 303},

    {
        'name': "Supplier contract 30, batch 6",
        'path': '/supplier_bills/18/edit',
        'regexes': [
            r'<select name="start_day">\s*<option value="1">01</option>\s*'
            '<option value="2">02</option>\s*<option value="3">03</option>\s*'
            '<option value="4">04</option>\s*<option value="5">05</option>\s*'
            '<option value="6" selected>06</option>\s*'
            '<option value="7">07</option>\s*<option value="8">08</option>\s*'
            '<option value="9">09</option>\s*<option value="10">10</option>\s*'
            '<option value="11">11</option>\s*'
            '<option value="12">12</option>\s*'
            '<option value="13">13</option>\s*'
            '<option value="14">14</option>\s*'
            '<option value="15">15</option>\s*'
            '<option value="16">16</option>\s*'
            '<option value="17">17</option>\s*'
            '<option value="18">18</option>\s*'
            '<option value="19">19</option>\s*'
            '<option value="20">20</option>\s*'
            '<option value="21">21</option>\s*'
            '<option value="22">22</option>\s*'
            '<option value="23">23</option>\s*'
            '<option value="24">24</option>\s*'
            '<option value="25">25</option>\s*'
            '<option value="26">26</option>\s*'
            '<option value="27">27</option>\s*'
            '<option value="28">28</option>\s*'
            '<option value="29">29</option>\s*'
            '<option value="30">30</option>\s*'
            '<option value="31">31</option>\s*'
            '</select>\s*<select name="start_hour">\s*'
            '<option value="0" selected>00</option>\s*'
            '<option value="1">01</option>\s*<option value="2">02</option>\s*'
            '<option value="3">03</option>\s*<option value="4">04</option>\s*'
            '<option value="5">05</option>\s*<option value="6">06</option>\s*'
            '<option value="7">07</option>\s*<option value="8">08</option>\s*'
            '<option value="9">09</option>\s*<option value="10">10</option>\s*'
            '<option value="11">11</option>\s*'
            '<option value="12">12</option>\s*'
            '<option value="13">13</option>\s*'
            '<option value="14">14</option>\s*'
            '<option value="15">15</option>\s*'
            '<option value="16">16</option>\s*'
            '<option value="17">17</option>\s*'
            '<option value="18">18</option>\s*'
            '<option value="19">19</option>\s*'
            '<option value="20">20</option>\s*'
            '<option value="21">21</option>\s*'
            '<option value="22">22</option>\s*'
            '<option value="23">23</option>\s*'
            '</select>:<select name="start_minute">\s*'
            '<option value="0" selected>00</option>\s*'
            '<option value="30">30</option>\s*</select>',
            r'<select name="finish_day">\s*<option value="1">01</option>\s*'
            '<option value="2">02</option>\s*<option value="3">03</option>\s*'
            '<option value="4">04</option>\s*<option value="5">05</option>\s*'
            '<option value="6" selected>06</option>\s*'
            '<option value="7">07</option>\s*<option value="8">08</option>\s*'
            '<option value="9">09</option>\s*<option value="10">10</option>\s*'
            '<option value="11">11</option>\s*'
            '<option value="12">12</option>\s*'
            '<option value="13">13</option>\s*'
            '<option value="14">14</option>\s*'
            '<option value="15">15</option>\s*'
            '<option value="16">16</option>\s*'
            '<option value="17">17</option>\s*'
            '<option value="18">18</option>\s*'
            '<option value="19">19</option>\s*'
            '<option value="20">20</option>\s*'
            '<option value="21">21</option>\s*'
            '<option value="22">22</option>\s*'
            '<option value="23">23</option>\s*'
            '<option value="24">24</option>\s*'
            '<option value="25">25</option>\s*'
            '<option value="26">26</option>\s*'
            '<option value="27">27</option>\s*'
            '<option value="28">28</option>\s*'
            '<option value="29">29</option>\s*'
            '<option value="30">30</option>\s*'
            '<option value="31">31</option>\s*'
            '</select>\s*<select name="finish_hour">\s*'
            '<option value="0" selected>00</option>\s*'
            '<option value="1">01</option>\s*<option value="2">02</option>\s*'
            '<option value="3">03</option>\s*<option value="4">04</option>\s*'
            '<option value="5">05</option>\s*<option value="6">06</option>\s*'
            '<option value="7">07</option>\s*<option value="8">08</option>\s*'
            '<option value="9">09</option>\s*<option value="10">10</option>\s*'
            '<option value="11">11</option>\s*'
            '<option value="12">12</option>\s*'
            '<option value="13">13</option>\s*'
            '<option value="14">14</option>\s*'
            '<option value="15">15</option>\s*'
            '<option value="16">16</option>\s*'
            '<option value="17">17</option>\s*'
            '<option value="18">18</option>\s*'
            '<option value="19">19</option>\s*'
            '<option value="20">20</option>\s*'
            '<option value="21">21</option>\s*'
            '<option value="22">22</option>\s*'
            '<option value="23">23</option>\s*'
            '</select>:<select name="finish_minute">\s*'
            '<option value="0" selected>00</option>\s*'
            '<option value="30">30</option>\s*</select>'],
        'status_code': 200},
    {
        'name': "Check that bill with two sets of register reads gets "
        "displayed correctly.",
        'path': '/supplies/10',
        'regexes': [
            r'<td rowspan="2">\s*'
            '<a href="/bill_types/2" title="Normal">N</a>\s*</td>\s*'
            '<td style="border-right: none;">\s*'
            '<a title="2011-02-04 23:30 I02D89150">34285</a>\s*</td>',
            r'25927</a>\s*</td>\s*'
            '<td style="border-left: none; text-align: right;">\s*E\s*</td>\s*'
            '<td>\s*</td>\s*<td style="border-right: none;">\s*</td>\s*'
            '<td style="border-left: none; text-align: right;">\s*</td>\s*'
            '<td style="border-right: none;">\s*</td>\s*'
            '<td style="border-left: none; text-align: right;">\s*</td>\s*'
            '</tr>',

            # Check form action for virtual bills is correct
            r'<form action="/reports/291">',

            # Check link to TPR from outer read
            r'<td>\s*'
            '<a href="/tprs/2">00003</a>\s*'
            '</td>'],
        'status_code': 200},

    # Supplier contract 62
    {
        'name': "Deleting a batch with bills with register reads.",
        'path': '/supplier_batches/5/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'status_code': 303,
        'regexes': [
            r'/supplier_batches\?supplier_contract_id=37']},
    {
        'name': "Check 'insert supplier batch' page.",
        'path': '/supplier_contracts/37/add_batch',
        'regexes': [
            r'="description"']},
    {
        'name': "Viewing the insert batch page of a DC contract.",
        'path': '/hhdc_contracts/30/add_batch',
        'regexes': [
            r'="description"']},
    {
        'name': "Viewing a batch in view mode, when it has a custom report.",
        'path': '/non_core_contracts/5/edit',
        'method': 'post',
        'data': {
            'name': "configuration",
            'properties': """
{
    'ips': {'127.0.0.1': 'implicit-user@localhost'},
    'site_links': [
        {'name': 'Google Maps', 'href': 'https://maps.google.com/maps?q='}],
    'batch_reports': [1],
    'elexonportal_scripting_key': 'xxx'}
""", },
        'status_code': 303},

    # Check that we can see a MOP batch okay. Contract 47
    {
        'path': '/mop_batches/9',
        'regexes': [
            r"/local_reports/1/output"],
        'status_code': 200},

    # Check that we can see a supplier batch okay. Contract 56
    {
        'path': '/supplier_batches/4',
        'regexes': [
            r'/local_reports/1/output\?batch_id=4'],
        'status_code': 200},
    {
        'name': "Check 'no channel' error when importing hh data.",
        'path': '/hhdc_contracts/29/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh-no-channel.simple.csv'},
        'status_code': 303,
        'regexes': [
            r"/hhdc_contracts/29/hh_imports/13"]},
    {
        'path': '/hhdc_contracts/29/hh_imports/13',
        'tries': {},
        'regexes': [
            r"There is no channel for the datum: \{&#39;channel_type&#39;: "
            "&#39;REACTIVE_EXP&#39;, &#39;mpan_core&#39;: &#39;22 4862 4512 "
            "332&#39;, &#39;start_date&#39;: "
            "datetime.datetime\(2010, 2, 4, 20, 0, tzinfo=&lt;UTC&gt;\), "
            "&#39;status&#39;: &#39;A&#39;, &#39;value&#39;: "
            "Decimal\(&#3\d;30.4339&#3\d;\)\}\."],
        'status_code': 200},
    {
        'name': "Check the bill import page.",
        'path': '/hhdc_contracts/29/hh_imports',
        'status_code': 200,
        'regexes': [
            r"/hhdc_contracts/29"]},

    # Can we add a new era ok? },
    {
        'name': "Check good error message if new era has same start date as "
        "existing era.",
        'path': '/supplies/10/edit',
        'method': 'post',
        'data': {
            'start_year': "2005",
            'start_month': "09",
            'start_day': "06",
            'start_hour': "00",
            'start_minute': "00",
            'insert_era': "Insert"},
        'regexes': [
            r"There&#39;s already an era with that start date\."],
        'status_code': 400},
    {
        'name': "Check MOP and DC bills are displaying correctly",
        'path': '/supplies/5',
        'regexes': [
            r'<td>\s*'
            '<a href="/hhdc_batches/8">001-7t'
            '</a>\s*</td>\s*<td>00031</td>\s*<td>22 0883 6932 301</td>\s*'
            '<td>2007-09-01 00:00</td>',
            r'<td>\s*'
            '<a href="/mop_batches/9">99/992'
            '</a>\s*</td>\s*<td>06</td>\s*<td>22 0883 6932 301</td>',

            # Check that MOP bill before supply start is displayed
            r'<td>\s*'
            '<a href="/mop_batches/9">99/992'
            '</a>\s*</td>\s*<td>08</td>\s*<td>22 0883 6932 301</td>',

            # Check that channel type is displayed
            r'<tr>\s*<td>\s*'
            '<a href="/channels/16">ACTIVE</a>\s*'
            '<a href="/channels/17">REACTIVE_IMP</a>\s*</td>'],
        'status_code': 200},
    {
        'name': "View the notes page.",
        'path': '/supplies/2/notes',
        'status_code': 200,
        'regexes': [
            r'Notes\s*\[<a href="/supplies/2/notes/add">add</a>\]']},
    {
        'name': "Try adding a note.",
        'path': '/supplies/2/notes/add',
        'method': 'post',
        'data': {
            'is_important': "True",
            'category': "general",
            'body': ""},
        'status_code': 303},
    {
        'name': "View the note editing page.",
        'path': '/supplies/2/notes/0/edit',
        'status_code': 200},

    # Try importing HH data from FTP server.
    {
        'name': "Update Contract",
        'path': '/hhdc_contracts/29/edit',
        'method': 'post',
        'data': {
            'party_id': "97",  # DASL
            'name': "HH contract",
            'charge_script': """
def virtual_bill_titles():
    return ['net-gbp', 'problem']

def virtual_bill(supply_source):
    supply_source.dc_bill['net-gbp'] = 0
""",
            'properties': """
{
    'file_type': '.df2',
    'hostname': 'localhost',
    'port': 2121,
    'username': 'chellow',
    'password': 'HixaNfUBOf*u',
    'directories': ['.']}
"""},
        'status_code': 303},

    # Do an 'import now'
    {
        'name': "Do an 'import now'",
        'path': '/hhdc_contracts/29/auto_importer',
        'method': 'post',
        'regexes': [
            '/hhdc_contracts/29/auto_importer'],
        'status_code': 303},
    {
        'name': "Check that file from FTP server has imported properly",
        'path': '/hhdc_contracts/29/auto_importer',
        'tries': {},
        'regexes': [
            r"Finished loading",
            r'<a href="/hhdc_contracts/29/auto_importer">Refresh page</a>']},
    {
        'path': '/hhdc_contracts/29',
        'regexes': [
            r"hh_data\.df2"]},

    {
        'name': "System price",
        'path': '/non_core_contracts/8/edit',
        'method': 'post',
        'data': {
            'name': 'system_price',
            'properties': """
{
    'enabled': True,
    'url': 'http://127.0.0.1:8080/elexonportal/',
    'limit': True}
"""},
        'status_code': 303},

    {
        'name': "Do an 'import now'",
        'path': '/non_core_contracts/8/auto_importer',
        'method': 'post',
        'regexes': [
            '/non_core_contracts/8/auto_importer'],
        'status_code': 303},

    {
        'name': 'System Price',
        'path': '/non_core_contracts/8/auto_importer',
        'tries': {'max': 40, 'period': 1},
        'regexes': [
            r"Updating rate script starting at 2005-01-01 00:00\."],
        'status_code': 200},

    {
        'name': 'System Price Feb',
        'path': '/non_core_contracts/8/auto_importer',
        'method': 'post',
        'data': {
            'name': 'now'},
        'status_code': 303},
    {
        'name': 'System Price',
        'path': '/non_core_contracts/8/auto_importer',
        'tries': {'max': 40, 'period': 1},
        'regexes': [
            r"Updating rate script starting at 2005-02-01 00:00\."],
        'status_code': 200},
    {
        'name': 'System Price March',
        'path': '/non_core_contracts/8/auto_importer',
        'method': 'post',
        'data': {
            'name': 'now'},
        'status_code': 303},
    {
        'name': 'System Price',
        'path': '/non_core_contracts/8/auto_importer',
        'tries': {'max': 40, 'period': 1},
        'regexes': [
            r"Updating rate script starting at 2005-03-01 00:00\."],
        'status_code': 200},
    {
        'name': 'System Price April',
        'path': '/non_core_contracts/8/auto_importer',
        'method': 'post',
        'data': {
            'name': 'now'},
        'status_code': 303},
    {
        'name': 'System Price',
        'path': '/non_core_contracts/8/auto_importer',
        'tries': {'max': 40, 'period': 1},
        'regexes': [
            r"Updating rate script starting at 2005-04-01 00:00\."],
        'status_code': 200},

    {
        'name': "Check that later bills are at the top.",
        'path': '/supplies/1',
        'regexes': [
            r"supplier_bills/7.*supplier_bills/1",
            r"2007-02-28 23:30"],
        'status_code': 200},

    # Change generation to NHH. Supply 7 },
    {
        'name': "Check that CRC report works for an AMR with no data.",
        'path': '/eras/7/edit',
        'method': 'post',
        'data': {
            'msn': "",
            'start_year': "2003",
            'start_month': "08",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'is_ended': "false",
            'pc_id': "4",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "393",
            'mop_contract_id': "32",
            'mop_account': "mc-22 6354 2983 570",
            'hhdc_contract_id': "29",
            'hhdc_account': "01",
            'imp_llfc_code': "210",
            'imp_mpan_core': "22 4862 4512 332",
            'imp_sc': "230",
            'imp_supplier_contract_id': "34",
            'imp_supplier_account': "141 5532"},
        'status_code': 303},

    {
        'name': "Run CRC report for month without data",
        'path': '/reports/207?supply_id=7&year=2012',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"016_FINISHED_watkinsexamplecom_crc_2012_2013_supply_7\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '016_FINISHED_watkinsexamplecom_crc_2012_2013_supply_7.csv',
        'status_code': 200,
        'regexes': [
            r'^"7","22 4862 4512 332"']},

    # Supply 9
    {
        'name': "Test monthly supplies duration for an unmetered supply.",
        'path': '/eras/20/edit',
        'method': 'post',
        'data': {
            'start_year': "2010",
            'start_month': "10",
            'start_day': "11",
            'start_hour': "00",
            'start_minute': "00",
            'is_ended': "false",
            'mop_contract_id': "32",
            'mop_account': "mc-22 0195 4836 192",
            'hhdc_contract_id': "30",
            'hhdc_account': "dc-22 0195 4836 192",
            'msn': "P96C93722",
            'pc_id': "8",
            'mtc_code': "857",
            'cop_id': "8",
            'ssc_code': "0428",
            'imp_llfc_code': "980",
            'imp_mpan_core': "22 0195 4836 192",
            'imp_sc': "304",
            'imp_supplier_contract_id': "34",
            'imp_supplier_account': "SA342376"},
        'status_code': 303},
    {
        'path': '/reports/291?supply_id=9&start_year=2011&start_month=05&'
        'start_day=01&start_hour=00&start_minute=0&finish_year=2011&'
        'finish_month=05&finish_day=31&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"017_FINISHED_watkinsexamplecom_supply_virtual_bills_9\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '017_FINISHED_watkinsexamplecom_supply_virtual_bills_9.csv',
        'regexes': [
            r'Imp MPAN Core,Exp MPAN Core,Site Code,Site Name,'
            r'Account,From,To,,mop-net-gbp,mop-problem,,'
            r'dc-net-gbp,dc-problem,,imp-supplier-net-gbp,'
            r'imp-supplier-vat-gbp,imp-supplier-gross-gbp,'
            r'imp-supplier-sum-msp-kwh,imp-supplier-problem',
            r'22 0195 4836 192,,CI004,Lower Treave,SA342376,'
            r'2011-05-01 00:00,2011-05-31 23:30,,10,,,7,,,'
            r'0.0,0.0,0.0,25.819178082191478,'],
        'status_code': 200},

    # Parties
    {
        'name': "Parties",
        'path': '/parties',
        'regexes': [
            r'<a href="/participants/513">SWEB</a>'],
        'status_code': 200},

    {
        'name': "Check rounding in bills is correct.",
        'path': '/supplies/5',

        # Check bill net and vat are shown correctly
        'regexes': [
            r"<td>195.60</td>\s*<td>36.03</td>"],
        'status_code': 200},
    {
        'name': "Test the right number of rows returned for a search on '22'.",
        'path': '/supplies?search_pattern=22&max_results=12',
        'regexes': [
            r"<tbody>\s*(<tr>.*?){11}\s*</tbody>"],
        'status_code': 200},
    {
        'name': "Try monthly supply duration with a non-half-hourly with "
        "bills.",
        'path': '/reports/177?supply_id=10&months=1&end_year=2011&'
        'end_month=01',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"018_FINISHED_watkinsexamplecom_supplies_monthly_duration_for_"
            r"10_1_to_2011_1\.csv"]
        },
    {
        'path': '/downloads/'
        '018_FINISHED_watkinsexamplecom_supplies_monthly_duration_for_'
        '10_1_to_2011_1.csv',
        'status_code': 200,
        'regexes': [
            r"supply-id,supply-name,source-code,generator-type,month,pc-code,"
            "msn,site-code,site-name,metering-type,import-mpan-core,"
            "metered-import-kwh,metered-import-net-gbp,"
            "metered-import-estimated-kwh,billed-import-kwh,"
            "billed-import-net-gbp,export-mpan-core,metered-export-kwh,"
            "metered-export-estimated-kwh,billed-export-kwh,"
            "billed-export-net-gbp,problem,timestamp",
            r'10,"2","net","","2011-01-31 23:30","03","I02D89150","CI017",'
            '"Roselands","nhh","22 1065 3921 534","0.0","10.0","0","150.0",'
            '"98.17","None","0","0","0","0",""']},
    {
        'name': "Try monthly supply duration with a half-hourly.",
        'path': '/reports/177?supply_id=4&months=1&end_year=2010&end_month=05',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"019_FINISHED_watkinsexamplecom_supplies_monthly_duration_for_"
            r"4_1_to_2010_5\.csv"]},
    {
        'path': '/downloads/'
        '019_FINISHED_watkinsexamplecom_supplies_monthly_duration_for_'
        '4_1_to_2010_5.csv',
        'status_code': 200,
        'regexes': [
            r"supply-id,supply-name,source-code,generator-type,month,pc-code,"
            "msn,site-code,site-name,metering-type,import-mpan-core,"
            "metered-import-kwh,metered-import-net-gbp,"
            "metered-import-estimated-kwh,billed-import-kwh,"
            "billed-import-net-gbp,export-mpan-core,metered-export-kwh,"
            "metered-export-estimated-kwh,billed-export-kwh,"
            "billed-export-net-gbp,problem,timestamp",
            r'4,"1","net","","2010-05-31 23:30","00","","CI005",'
            r'"Wheal Rodney","hh","22 6158 2968 220","0","189.22680000000003",'
            r'"0","0","0","22 3479 7618 470","0","0","0","0",""']},
    {
        'name': "Check supplies monthly duration page.",
        'path': '/csv_supplies_monthly_duration',
        'regexes': [
            r"end_month",
            r'/reports/177'],
        'status_code': 200},

    {
        'name': "CSV Sites Duration Selector",
        'path': '/csv_sites_duration',

        # Should have link to CSS
        'regexes': [
            r"/style"],
        'status_code': 200},
    {
        'path': '/reports/59?start_year=2013&start_month=04&start_day=01&'
        'start_hour=00&start_minute=00&finish_year=2013&finish_month=04&'
        'finish_day=1&finish_hour=23&finish_minute=30',
        'regexes': [
            r'"CH017","Parbola","","sub","","2013-04-01 00:00",'
            '"2013-04-01 23:30","0","0","0","0","0","0","hh"'],
        'status_code': 200},
    {
        'name': "Check CSV Sites HH Data Selector.",
        'path': '/csv_sites_hh_data',

        # Should have link to CSS
        'regexes': [
            r"/style"],
        'status_code': 200},
    {
        'name': "Check CSV Supplies HH Data. With supply_id",
        'path': '/reports/169?supply_id=1&imp_related=true&'
        'channel_type=ACTIVE&start_year=2008&start_month=7&start_day=1&'
        'start_hour=0&start_minute=0&finish_year=2008&finish_month=07&'
        'finish_day=31&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"020_FINISHED_watkinsexamplecom_supplies_hh_data_200807312330_"
            r"supply_22_9205_6799_106\.csv"]},
    {
        'path': '/downloads/'
        '020_FINISHED_watkinsexamplecom_supplies_hh_data_200807312330_'
        'supply_22_9205_6799_106.csv',
        'status_code': 200,

        # Check the HH data is there
        'regexes': [
            r"NA,2008-07-06,0\.262"]},

    # Add a new era with this contract
    {
        'name': "Test duos-fixed",
        'path': '/supplies/5/edit',
        'method': 'post',
        'data': {
            'start_year': "2013",
            'start_month': "01",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00",
            'insert_era': "Insert"},
        'regexes': [
            r"/supplies/5"],
        'status_code': 303},

    # Supply 5
    {
        'path': '/eras/23/edit',
        'method': 'post',
        'data': {
            'start_year': "2013",
            'start_month': "01",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00",
            'is_ended': "false",
            'gsp_group_id': "11",
            'mop_contract_id': "32",
            'mop_account': "22 0883 6932 301",
            'hhdc_contract_id': "29",
            'hhdc_account': "22 0883 6932 301",
            'msn': "",
            'pc_id': "9",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'imp_llfc_code': "570",
            'imp_mpan_core': "22 0883 6932 301",
            'imp_sc': "350",
            'imp_supplier_contract_id': "33",
            'imp_supplier_account': "4341"},
        'status_code': 303},
    {
        'path': '/reports/291?supply_id=5&start_year=2013&start_month=04&'
        'start_day=01&start_hour=00&start_minute=00&finish_year=2013&'
        'finish_month=04&finish_day=30&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"021_FINISHED_watkinsexamplecom_supply_virtual_bills_5\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '021_FINISHED_watkinsexamplecom_supply_virtual_bills_5.csv',
        'regexes': [
            r'Imp MPAN Core,Exp MPAN Core,Site Code,Site Name,'
            'Account,From,To,,mop-net-gbp,mop-problem,,'
            'dc-net-gbp,dc-problem,,imp-supplier-net-gbp,'
            'imp-supplier-tlm,imp-supplier-ccl-kwh,'
            'imp-supplier-ccl-rate,imp-supplier-ccl-gbp,'
            'imp-supplier-data-collection-gbp,'
            'imp-supplier-duos-availability-kva,'
            'imp-supplier-duos-availability-days,'
            'imp-supplier-duos-availability-rate,'
            'imp-supplier-duos-availability-gbp,'
            'imp-supplier-duos-excess-availability-kva,'
            'imp-supplier-duos-excess-availability-days,'
            'imp-supplier-duos-excess-availability-rate,'
            'imp-supplier-duos-excess-availability-gbp,'
            'imp-supplier-duos-green-kwh,imp-supplier-duos-green-rate,'
            'imp-supplier-duos-green-gbp,imp-supplier-duos-green-kwh,'
            'imp-supplier-duos-green-rate,imp-supplier-duos-amber-gbp,'
            'imp-supplier-duos-amber-kwh,imp-supplier-duos-red-rate,'
            'imp-supplier-duos-red-gbp,imp-supplier-duos-reactive-kvarh,'
            'imp-supplier-duos-reactive-rate,'
            'imp-supplier-duos-reactive-gbp,imp-supplier-duos-fixed-days,'
            'imp-supplier-duos-fixed-rate,imp-supplier-duos-fixed-gbp,'
            'imp-supplier-settlement-gbp,imp-supplier-aahedc-msp-kwh,'
            'imp-supplier-aahedc-gsp-kwh,imp-supplier-aahedc-rate,'
            'imp-supplier-aahedc-gbp,imp-supplier-rcrc-kwh,'
            'imp-supplier-rcrc-rate,imp-supplier-rcrc-gbp,'
            'imp-supplier-night-msp-kwh,imp-supplier-night-gsp-kwh,'
            'imp-supplier-night-gbp,imp-supplier-other-msp-kwh,'
            'imp-supplier-other-gsp-kwh,imp-supplier-other-gbp,'
            'imp-supplier-summer-pk-msp-kwh,'
            'imp-supplier-summer-pk-gsp-kwh,imp-supplier-summer-pk-gbp,'
            'imp-supplier-winter-low-pk-msp-kwh,'
            'imp-supplier-winter-low-pk-gsp-kwh,'
            'imp-supplier-winter-low-pk-gbp,'
            'imp-supplier-winter-off-pk-msp-kwh,'
            'imp-supplier-winter-off-pk-gsp-kwh,'
            'imp-supplier-winter-off-pk-gbp,'
            'imp-supplier-winter-pk-msp-kwh,'
            'imp-supplier-winter-pk-gsp-kwh,'
            'imp-supplier-winter-pk-gbp,'
            'imp-supplier-bsuos-kwh,imp-supplier-bsuos-rate,'
            'imp-supplier-bsuos-gbp,imp-supplier-triad-actual-1-date,'
            'imp-supplier-triad-actual-1-msp-kw,'
            'imp-supplier-triad-actual-1-status,'
            'imp-supplier-triad-actual-1-laf,'
            'imp-supplier-triad-actual-1-gsp-kw,'
            'imp-supplier-triad-actual-2-date,'
            'imp-supplier-triad-actual-2-msp-kw,'
            'imp-supplier-triad-actual-2-status,'
            'imp-supplier-triad-actual-2-laf,'
            'imp-supplier-triad-actual-2-gsp-kw,'
            'imp-supplier-triad-actual-3-date,'
            'imp-supplier-triad-actual-3-msp-kw,'
            'imp-supplier-triad-actual-3-status,'
            'imp-supplier-triad-actual-3-laf,'
            'imp-supplier-triad-actual-3-gsp-kw,'
            'imp-supplier-triad-actual-gsp-kw,'
            'imp-supplier-triad-actual-rate,'
            'imp-supplier-triad-actual-gbp,'
            'imp-supplier-triad-estimate-1-date,'
            'imp-supplier-triad-estimate-1-msp-kw,'
            'imp-supplier-triad-estimate-1-status,'
            'imp-supplier-triad-estimate-1-laf,'
            'imp-supplier-triad-estimate-1-gsp-kw,'
            'imp-supplier-triad-estimate-2-date,'
            'imp-supplier-triad-estimate-2-msp-kw,'
            'imp-supplier-triad-estimate-2-status,'
            'imp-supplier-triad-estimate-2-laf,'
            'imp-supplier-triad-estimate-2-gsp-kw,'
            'imp-supplier-triad-estimate-3-date,'
            'imp-supplier-triad-estimate-3-msp-kw,'
            'imp-supplier-triad-estimate-3-status,'
            'imp-supplier-triad-estimate-3-laf,'
            'imp-supplier-triad-estimate-3-gsp-kw,'
            'imp-supplier-triad-estimate-gsp-kw,'
            'imp-supplier-triad-estimate-rate,'
            'imp-supplier-triad-estimate-months,'
            'imp-supplier-triad-estimate-gbp,'
            'imp-supplier-triad-all-estimates-months,'
            'imp-supplier-triad-all-estimates-gbp,'
            'imp-supplier-problem',
            r'22 0883 6932 301,,CI005,Wheal Rodney,4341,'
            r'2013-04-01 00:00,2013-04-30 23:30,,10,,,0,,,'
            r'369.6049999999999,,,0.00525288,,5.89,350,30,'
            r'0.026,272.99999999999994,0,31,0.026,0.0,0,'
            r'0.00161,0.0,,,0.0,0,0.2441,0.0,0.0,0.00382,'
            r'0.0,30,0.0905,2.7150000000000003,88,0,'
            r'0.0,0.0001897,0.0,0.0,,0.0,0,'
            '0.0,0.0,0,0.0,0.0,0,0.0,0.0,,,,,,,,'
            ',,0.0,'
            ',0.0,,,,,,,,,,,,,,,,'
            ',,,2012-11-29 17:00,0,X,1.087,0.0,'
            '2012-12-12 17:00,0,X,1.087,0.0,2013-01-16 17:00,0,'
            'X,1.087,0.0,0.0,33.551731,1,0.0,,,'],
        'status_code': 200},
    {
        'path': '/csv_sites_monthly_duration',
        'regexes': [
            r"finish_year"],
        'status_code': 200},
    {
        'name': "Try site search",
        'path': '/sites?pattern=',
        'regexes': [
            r'<a href="/sites/8">'
            'B00LG Bieling</a>'],
        'status_code': 200},
    {
        'name': "Site search with trailing whitespace",
        'path': '/sites?pattern= B00LG',
        'status_code': 302},
    {
        'name': "Try TRIAD report when supply starts after first triad",
        'path': '/reports/41?supply_id=6&year=2007',
        'status_code': 200,
        'regexes': [
            r'CI017,"Roselands","1",net,"","22 6354 2983 570",'
            '"2007-01-23 17:00","0","X","1.074","0.0","2006-12-20 17:00","0",'
            '"before start of supply","before start of supply","0",'
            '"2007-02-08 17:30","0","X","1.074","0.0","0.0","5.94264","0.0",'
            '"","","","","","","","","","","","","","","","","","",""$']},

    # Insert a 14 supply
    {
        'name': "Try a pre 2010-04-01 DNO 14 bill.",
        'path': '/sites/5/edit',
        'method': 'post',
        'data': {
            'source_id': "1",
            'name': "Bernard",
            'start_year': "2003",
            'start_month': "08",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'msn': "88jiuf ff",
            'gsp_group_id': "5",
            'pc_id': "9",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'mop_contract_id': "32",
            'mop_account': "mc-14 7206 6139 971",
            'hhdc_contract_id': "29",
            'hhdc_account': "dc-14 7206 6139 971",
            'imp_llfc_code': "365",
            'imp_mpan_core': "14 7206 6139 971",
            'imp_sc': "2300",
            'imp_supplier_contract_id': "31",
            'imp_supplier_account': "sup-14 7206 6139 971",
            'insert': "insert"},
        'regexes': [
            r"/supplies/17"],
        'status_code': 303},

    # Try a pre 2010-04-01 DNO 14 bill.
    {
        'path': '/reports/291?supply_id=17&start_year=2009&start_month=06&'
        'start_day=01&start_hour=00&start_minute=00&finish_year=2009&'
        'finish_month=06&finish_day=30&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"022_FINISHED_watkinsexamplecom_supply_virtual_bills_17\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '022_FINISHED_watkinsexamplecom_supply_virtual_bills_17.csv',
        'regexes': [
            r'Imp MPAN Core,Exp MPAN Core,Site Code,Site Name,'
            r'Account,From,To,,mop-net-gbp,mop-problem,,'
            r'dc-net-gbp,dc-problem,,imp-supplier-net-gbp,'
            r'imp-supplier-tlm,imp-supplier-ccl-kwh,'
            r'imp-supplier-ccl-rate,imp-supplier-ccl-gbp,'
            r'imp-supplier-data-collection-gbp,'
            r'imp-supplier-duos-availability-kva,'
            'imp-supplier-duos-availability-days,'
            'imp-supplier-duos-availability-rate,'
            'imp-supplier-duos-availability-gbp,'
            'imp-supplier-duos-excess-availability-kva,'
            'imp-supplier-duos-excess-availability-days,'
            'imp-supplier-duos-excess-availability-rate,'
            'imp-supplier-duos-excess-availability-gbp,'
            'imp-supplier-duos-day-kwh,imp-supplier-duos-day-gbp,'
            'imp-supplier-duos-night-kwh,imp-supplier-duos-night-gbp,'
            'imp-supplier-duos-reactive-rate,'
            'imp-supplier-duos-reactive-gbp,'
            'imp-supplier-duos-standing-gbp,'
            'imp-supplier-settlement-gbp,imp-supplier-night-msp-kwh,'
            'imp-supplier-night-gsp-kwh,imp-supplier-night-gbp,'
            'imp-supplier-other-msp-kwh,imp-supplier-other-gsp-kwh,'
            'imp-supplier-other-gbp,imp-supplier-summer-pk-msp-kwh,'
            'imp-supplier-summer-pk-gsp-kwh,imp-supplier-summer-pk-gbp,'
            'imp-supplier-winter-low-pk-msp-kwh,'
            'imp-supplier-winter-low-pk-gsp-kwh,'
            'imp-supplier-winter-low-pk-gbp,'
            'imp-supplier-winter-off-pk-msp-kwh,'
            'imp-supplier-winter-off-pk-gsp-kwh,'
            'imp-supplier-winter-off-pk-gbp,'
            'imp-supplier-winter-pk-msp-kwh,'
            'imp-supplier-winter-pk-gsp-kwh,'
            'imp-supplier-winter-pk-gbp,'
            'imp-supplier-bsuos-kwh,imp-supplier-bsuos-rate,'
            'imp-supplier-bsuos-gbp,imp-supplier-triad-actual-1-date,'
            'imp-supplier-triad-actual-1-msp-kw,'
            'imp-supplier-triad-actual-1-status,'
            'imp-supplier-triad-actual-1-laf,'
            'imp-supplier-triad-actual-1-gsp-kw,'
            'imp-supplier-triad-actual-2-date,'
            'imp-supplier-triad-actual-2-msp-kw,'
            'imp-supplier-triad-actual-2-status,'
            'imp-supplier-triad-actual-2-laf,'
            'imp-supplier-triad-actual-2-gsp-kw,'
            'imp-supplier-triad-actual-3-date,'
            'imp-supplier-triad-actual-3-msp-kw,'
            'imp-supplier-triad-actual-3-status,'
            'imp-supplier-triad-actual-3-laf,'
            'imp-supplier-triad-actual-3-gsp-kw,'
            'imp-supplier-triad-actual-gsp-kw,'
            'imp-supplier-triad-actual-rate,imp-supplier-triad-actual-gbp,'
            'imp-supplier-triad-estimate-1-date,'
            'imp-supplier-triad-estimate-1-msp-kw,'
            'imp-supplier-triad-estimate-1-status,'
            'imp-supplier-triad-estimate-1-laf,'
            'imp-supplier-triad-estimate-1-gsp-kw,'
            'imp-supplier-triad-estimate-2-date,'
            'imp-supplier-triad-estimate-2-msp-kw,'
            'imp-supplier-triad-estimate-2-status,'
            'imp-supplier-triad-estimate-2-laf,'
            'imp-supplier-triad-estimate-2-gsp-kw,'
            'imp-supplier-triad-estimate-3-date,'
            'imp-supplier-triad-estimate-3-msp-kw,'
            'imp-supplier-triad-estimate-3-status,'
            'imp-supplier-triad-estimate-3-laf,'
            'imp-supplier-triad-estimate-3-gsp-kw,'
            'imp-supplier-triad-estimate-gsp-kw,'
            'imp-supplier-triad-estimate-rate,'
            'imp-supplier-triad-estimate-months,'
            'imp-supplier-triad-estimate-gbp,'
            'imp-supplier-triad-all-estimates-months,'
            'imp-supplier-triad-all-estimates-gbp,imp-supplier-problem',
            r'14 7206 6139 971,,CH023,Treglisson,'
            'sup-14 7206 6139 971,2009-06-01 00:00,2009-06-30 23:30,,'
            '10,,,0,,,334.30000000000007,,,0.0047,,'
            r'5.89,,,0.0457,105.11,,,,,0,0.0,0,0.0,'
            r'0.0012,0.0,135.30000000000004,88,0,0.0,0.0,0,'
            r'0.0,0.0,0,0.0,0.0,0,0,0.0,0,0,0.0,0,0,'
            r'0.0,0.0,,0.0,,,,,,,,,,,,,,,'
            r',,,,'
            '2009-01-06 17:00,0,X,1.037,0.0,2008-12-01 17:00,0,'
            'X,1.037,0.0,2008-12-15 17:00,0,X,1.037,0.0,0.0,'
            '20.526611,1,0.0,,,,duos-availability-agreed-kva,'
            '2300,duos-availability-billed-kva,2300'],
        'status_code': 200},
    {
        'name': "Report of HHDC snags",
        'path': '/reports/233?hhdc_contract_id=29&days_hidden=1',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"023_FINISHED_watkinsexamplecom_channel_snags\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '023_FINISHED_watkinsexamplecom_channel_snags.csv',
        'regexes': [
            r'83,22 0883 6932 301,,CI005,Wheal Rodney,Missing,'
            'True,ACTIVE,2002-01-01 00:00,2003-08-02 23:30,'],
        'status_code': 200},
    {
        'name': "Site use graph",
        'path': '/sites/5/used_graph?months=1&finish_year=2013&finish_month=6',
        'status_code': 200,
        'regexes': [
            r'<option value="06" selected>06</option>']},
    {
        'name': "Site generation graph",
        'path': '/sites/7/gen_graph?months=1&finish_year=2013&finish_month=7',
        'status_code': 200},

    # Can we make a supply have source sub and view site level hh data okay?
    {
        'name': "CSV Sites HH Data",
        'path': '/supplies/1/edit',
        'method': 'post',

        # Can we update a supply name?

        # Can we update a supply source?
        'data': {
            'name': "Hello",
            'source_id': "2",
            'generator_type_id': "1",
            'gsp_group_id': "11"},
        'regexes': [
            r"/supplies/1"],
        'status_code': 303},
    {
        'path': '/reports/29?site_id=7&type=used&months=1&finish_year=2008&'
        'finish_month=07',
        'status_code': 200,
        'regexes': [
            r"CH017,used,2008-07-01,", ]},
    {
        'path': '/reports/29?site_id=7&type=displaced&months=1&'
        'finish_year=2008&finish_month=07',
        'status_code': 200,
        'regexes': [
            r"CH017,displaced,2008-07-01,"]},
    {
        'name': "Look at list of supplier contracts.",
        'path': '/supplier_contracts',

        # Are the contracts in alphabetical order?
        'regexes': [
            r'<tbody>\s*<tr>\s*<td>\s*'
            '<a href="/supplier_contracts/31">Half-hourlies 2007</a>'],
        'status_code': 200},
    {
        'name': "Daily supplier virtual bills page.",
        'path': '/reports/241?supply_id=6&is_import=true&start_year=2013&'
        'start_month=10&start_day=1&finish_year=2013&finish_month=10&'
        'finish_day=31',
        'status_code': 200,
        'regexes': [
            r'"22 6354 2983 570","CI017","Roselands","141 5532",'
            r'"2013-10-31 00:00","2013-10-31 23:30","153.78050000000002",'
            r'"","","0.00525288","","5.89","2300","1","0.026","59.8",'
            r'"0","31","0.026","0.0","","","","","0.00382","0.0","","88","0",'
            r'"0.0","0.0","0","0.0","0.0","0","0.0","0.0","0","0","0.0","0",'
            r'"0","0.0","0","0","0.0","0.0","","0.0","","","","","","","","",'
            r'"","","","","","","","","","","2012-11-29 17:00","0","X",'
            r'"1.087","0.0","2012-12-12 17:00","0","X","1.087","0.0",'
            r'"2013-01-16 17:00","0","X","1.087","0.0","0.0","33.551731","1",'
            r'"0.0","","","","duos-amber-gbp","0.0","duos-amber-kwh","0",'
            r'"duos-amber-rate","0.00287","duos-fixed-days","1",'
            r'"duos-fixed-gbp","0.0905","duos-fixed-rate","0.0905",'
            r'"duos-green-gbp","0.0","duos-green-kwh","0","duos-green-rate",'
            r'"0.00161","duos-reactive-kvarh","0.0","duos-red-gbp","0.0",'
            r'"duos-red-kwh","0","duos-red-rate","0.2441","sbp-rate",'
            r'"0.02436","ssp-rate","0.01844324"\s*\Z']},

    # See if selector is working
    {
        'name': "Test register read report.",
        'path': '/csv_register_reads',
        'status_code': 200,
        'regexes': [
            r"end_year"]},
    {
        'name': "Test register read report for a supply.",
        'path': '/reports/219?supply_id=10&months=1&end_year=2011&end_month=1',
        'status_code': 200,
        'regexes': [
            r'\.csv".\)',
            r"Duration Start,Duration Finish,Supply Id,Import MPAN Core,"
            "Export MPAN Core,Batch Reference,Bill Id,Bill Reference,"
            "Bill Issue Date,Bill Type,Register Read Id,TPR,Coefficient,"
            "Previous Read Date,Previous Read Value,Previous Read Type,"
            "Present Read Date,Present Read Value,Present Read Type",
            r'"2011-01-01 00:00","2011-01-31 23:30","10","22 1065 3921 534",'
            '"","07-002","13","3423760005","2011-02-02 00:00","N","8","00001",'
            '"1","2011-01-04 23:30","24286","E","2011-01-06 23:30","25927",'
            '"E"']},

    # Try for a period where there's a read with no TPR (an MD read)
    {
        'path': '/reports/219?supply_id=10&months=1&end_year=2007&end_month=1',
        'status_code': 200,
        'regexes': [
            r'"2007-01-01 00:00","2007-01-31 23:30","10","22 1065 3921 534",'
            '"","06-002","14","SA342376","2007-01-01 00:00","N","12","md","1",'
            '"2007-01-04 00:00","45","E","2007-01-17 00:00","76","E"']},
    {
        'name': "View a MOP rate script. Contract 31.",
        'path': '/mop_rate_scripts/98',
        'status_code': 200},

    {
        'name': "View supplies duration selector.",
        'path': '/csv_supplies_duration',
        'status_code': 200,
        'regexes': [
            r"start_year"]},

    {
        'name': "View supplies hh data selector.",
        'path': '/csv_supplies_hh_data',
        'status_code': 200},

    {
        'name': "Look at a TPR.",
        'path': '/tprs/1',
        'status_code': 200,
        'regexes': [
            r"<tbody>\s*<tr>\s*<td>1</td>\s*<td>1</td>"]},
    {
        'name': "CSV Bills.",
        'path': '/csv_bills',
        'status_code': 200,
        'regexes': [
            r"end_year"]},
    {
        'name': "CSV Supplies Duration with register reads",
        'path': '/reports/149?start_year=2010&start_month=01&start_day=1&'
        'start_hour=0&start_minute=0&finish_year=2010&finish_month=01&'
        'finish_day=31&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"024_FINISHED_watkinsexamplecom_supplies_duration\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '024_FINISHED_watkinsexamplecom_supplies_duration.csv',
        'regexes': [
            r'"10","2",'],
        'status_code': 200},
    {
        'name': "Try the site level monthly data HTML report.",
        'path': '/sites/3/months?finish_year=2005&finish_month=11',
        'regexes': [
            r"For 12 months finishing at the end of",
            r"<th>2005-09-15 00:00</th>"],
        'status_code': 200},
    {
        'name': "Change the name of a site.",
        'path': '/sites/8/edit',
        'method': 'post',
        'data': {
            'site_name': "Ishmael",
            'code': "MOBY",
            'update': "Update"},
        'status_code': 303},

    # Insert era
    {
        'name': "Try inserting an era where the existing era is attached to "
        "more than one site.",
        'path': '/supplies/2/edit',
        'method': 'post',
        'data': {
            'start_year': "2005",
            'start_month': "05",
            'start_day': "04",
            'start_hour': "00",
            'start_minute': "00",
            'insert_era': "insert_era"},
        'status_code': 303},
    {
        'name': "Check user roles page.",
        'path': '/user_roles',
        'status_code': 200,
        'regexes': [
            r"party-viewer"]},

    {
        'name': "Scenario runner",
        'path': '/ods_scenario_runner',
        'status_code': 200},

    {
        'name': "Unified report",
        'path': '/ods_unified_report',
        'status_code': 200},

    {
        'name': "Bill type",
        'path': '/bill_types/1',
        'status_code': 200},

    # Supplier contract 62. },
    {
        'name': "Test sse edi bill with MD line",
        'path': '/supplier_bill_imports',
        'method': 'post',
        'data': {
            'supplier_batch_id': "3", },
        'files': {'import_file': 'test/bills2.sse.edi'},
        'status_code': 303,
        'regexes': [
            r"/supplier_bill_imports/8"]},

    # Supplier contract 62.
    {
        'path': '/supplier_bill_imports/8',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"All the bills have been successfully loaded and attached to "
            "the batch\."]},
    {
        'name': "Look at an HHDC batch",
        'path': '/hhdc_batches/8',
        'status_code': 200,
        'regexes': [
            r'<a href="/local_reports/1/output\?batch_id=8">',
            r"<tbody>\s*<tr>"]},

    # Supplier contract 61, batch 7, bill 10
    {
        'name': "Edit register read with a TPR that's not 00001",
        'path': '/reads/1/edit',
        'regexes': [
            r'<option value="37" selected>00040</option>']},

    # Insert a new batch
    {
        'name': "Add and delete an HHDC contract",
        'path': '/hhdc_contracts/29/add_batch',
        'method': 'post',
        'data': {
            'reference': "to_delete",
            'description': ""},
        'status_code': 303,
        'regexes': [
            r"/hhdc_batches/10"]},

    {
        'name': "HHDC batch confirm delete page. HHDC contract 29",
        'path': '/hhdc_batches/10/edit?confirm_delete=Delete',
        'status_code': 200,
        'regexes': [
            r'<form method="post" action="">\s*'
            r'<fieldset>\s*'
            r'<input type="submit" name="delete" value="Delete">\s']},
    {
        'name': "Delete it. HHDC contract 29",
        'path': '/hhdc_batches/10/edit',
        'method': 'post',
        'data': {
            'delete': 'Delete'},
        'status_code': 303,
        'regexes': [
            '/hhdc_batches\?hhdc_contract_id=29']},
    {
        'name': "Check it's really gone. HHDC contract 29",
        'path': '/hhdc_batches/10',
        'status_code': 404},


    # CRC Special Events
    {
        'name': "CRC Special Events",
        'path': '/reports/215?year=2012',
        'status_code': 200,
        'regexes': [
            r'"22 0883 6932 301","CI005",']},

    {
        'name': "A supply level virtual bill that crosses an era boundary",
        'path': '/reports/291?supply_id=10&start_year=2010&start_month=01&'
        'start_day=01&start_hour=00&start_minute=0&finish_year=2010&'
        'finish_month=01&finish_day=31&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"025_FINISHED_watkinsexamplecom_supply_virtual_bills_10\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '025_FINISHED_watkinsexamplecom_supply_virtual_bills_10.csv',
        'regexes': [
            r'Imp MPAN Core,Exp MPAN Core,Site Code,Site Name,'
            'Account,From,To,,mop-net-gbp,mop-problem,,'
            'dc-net-gbp,dc-problem,,imp-supplier-net-gbp,'
            'imp-supplier-vat-gbp,imp-supplier-gross-gbp,'
            'imp-supplier-sum-msp-kwh,imp-supplier-problem',
            r'22 1065 3921 534,,CI017,Roselands,SA342376,'
            '2010-01-01 00:00,2010-01-03 23:30,,0,,,,,,'
            '0.0,0.0,0.0,0.0,'],
        'status_code': 200},
    {
        'name': "A bill check with multiple covered bills",
        'path': '/reports/111?bill_id=8',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"026_FINISHED_watkinsexamplecom_bill_check\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '026_FINISHED_watkinsexamplecom_bill_check.csv',
        'regexes': [
            r'06-004,00101,N,244,3810.08,355.03,'
            r'2011-05-01 00:00,2011-06-30 00:00,22 6354 2983 570,CI017,'
            r'Roselands,2011-05-01 00:00,2011-06-30 00:00,9;8,0,'
            r'4701.16,3010.2260000000024,1690.9339999999975,,,,,'
            r'11.4,0.00485,,,,,5.89,,,2300,,60,,'
            r'0.0211,,2911.8000000000025,,,0,,31,,0.0211,'
            r',0.0,,,,,,,,,,,,,0.00353,,0.0,'
            r',,,,,88,,,0,,0.0,,0.0,,,0,,'
            r'0.0,,0.0,,,0,,0.0,,0.0,,,0,,0,,'
            r'0.0,,,0,,0,,0.0,,,0,,0,,0.0,,,'
            r'0.0,,,,0.0,,,,,,,,,,,,,,,'
            r',,,,,,,,,,,,,,,,,,,,,'
            r',,,,2010-12-07 17:00,,0,,X,,1.087,,'
            r'0.0,,2010-12-20 17:00,,0,,X,,1.087,,0.0,'
            r',2011-01-06 17:00,,0,,X,,1.087,,0.0,,'
            r'0.0,,28.408897,,1,,0.0,,,,,,,,,'
            'virtual-duos-amber-gbp,0.0,,,virtual-duos-amber-kwh,'
            '0,,,virtual-duos-amber-rate,0.00205,,,'
            'virtual-duos-fixed-days,60,,,virtual-duos-fixed-gbp,'
            r'4.536000000000001,,,virtual-duos-fixed-rate,0.0756,,'
            r',virtual-duos-green-gbp,0.0,,,'
            r'virtual-duos-green-kwh,0,,,virtual-duos-green-rate,'
            r'0.00138,,'],
        'status_code': 200},
    {
        'name': "Contract virtual bills",
        'path': '/reports/87?supplier_contract_id=31&start_year=2013&'
        'start_month=12&start_day=01&start_hour=00&start_minute=00&'
        'finish_year=2013&finish_month=12&finish_day=01&finish_hour=23&'
        'finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"027_FINISHED_watkinsexamplecom_virtual_bills\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '027_FINISHED_watkinsexamplecom_virtual_bills.csv',
        'regexes': [
            r'22 0470 7514 535,CH017,Parbola,010,2013-12-01 00:00,'
            '2013-12-01 23:30,93.89,,,,,5.89,150,1,'
            '0,0,,,,,,,,,0.00147,0.0,,88,0,'
            '0.0,'
            '0.0,0,0.0,0.0,0,0,0.0,0,0,0.0,0,0,0.0,'
            '0,0,0.0,0.0,,0.0,,,,,,,,,'
            ',,,,,,,,,,,,,,,,,,,,,'
            ',,,,,,,,,,,duos-amber-gbp,0.0,'
            'duos-amber-kwh,0,duos-amber-rate,-0.00649,'
            'duos-fixed-days,1,'
            'duos-fixed-gbp,0,duos-fixed-rate,0,duos-green-gbp,'
            '0.0,duos-green-kwh,0,duos-green-rate,-0.00649'],
        'status_code': 200},

    {
        'name': "Contract displaced virtual bills",
        'path': '/reports/109?supplier_contract_id=31&months=1&'
        'finish_year=2013&finish_month=01',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"028_FINISHED_watkinsexamplecom_displaced\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '028_FINISHED_watkinsexamplecom_displaced.csv',
        'regexes': [
            r'CI004,Lower Treave,,2013-01-01 00:00,'
            r'2013-01-31 23:30,chp,,,,,0.0,0.0,,0.0,,0.00509,'
            r',,,0,0.00161,0.0,,,,0.0,0.0,0,0.0,'
            r'0.0,0,,0,0,,,,0,0,0.0,0.0,0,0.0,'
            r'0.0,0,,,,,,,,,,,,,,,,,,,'
            r'2011-12-05 17:00,0,E,1.087,0.0,2012-01-16 17:00,0,'
            r'E,1.087,0.0,2012-02-02 17:30,0,E,1.075,0.0,'
            r'0.0,31.062748,1,0.0,,,,duos-amber-gbp,0.0,'
            r'duos-amber-kwh,0,duos-amber-rate,0.00251,duos-red-gbp,'
            r'0.0,duos-red-kwh,0,duos-red-rate,0.20727'],
        'status_code': 200},

    # Move finish date of era
    {
        'name': "Check that covering hh data by a different era doesn't "
        "result in missing data being reported.",
        'path': '/eras/1/edit',
        'method': 'post',
        'data': {
            'start_year': "2003",
            'start_month': "08",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'is_ended': "true",
            'finish_year': "2004",
            'finish_month': "07",
            'finish_day': "06",
            'finish_hour': "23",
            'finish_minute': "30",
            'mop_contract_id': "32",
            'mop_account': "mc-22 9205 6799 106",
            'hhdc_contract_id': "29",
            'hhdc_account': "01",
            'msn': "",
            'pc_id': "9",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'imp_llfc_code': "540",
            'imp_mpan_core': "22 9205 6799 106",
            'imp_sc': "450",
            'imp_supplier_contract_id': "31",
            'imp_supplier_account': "11640077",
            'exp_llfc_code': "581",
            'exp_mpan_core': "22 0470 7514 535",
            'exp_sc': "150",
            'exp_supplier_contract_id': "31",
            'exp_supplier_account': ""},
        'status_code': 303},
    {
        'path': '/channel_snags?hhdc_contract_id=29&days_hidden=5',
        'status_code': 200,
        'regexes': [
            r'<tr>\s*<td>\s*<ul>\s*<li>\s*'
            r'<a href="/channel_snags/100">view</a>\s*'
            r'\[<a href="/channel_snags/100/edit">edit</a>\]\s*'
            r'</li>\s*</ul>\s*</td>\s*<td>\s*</td>\s*<td>\s*'
            '22 0470 7514 535\s*</td>\s*<td>\s*<ul>\s*'
            '<li>CH017 Parbola</li>\s*</ul>\s*</td>\s*<td>Missing</td>\s*'
            '<td>\s*<ul>\s*<li>\s*Export\s*ACTIVE\s*</li>\s*</ul>\s*</td>\s*'
            '<td>\s*2004-07-07 00:00 to\s*2005-09-14 23:30\s*</td>\s*</tr>']},

    # Insert era
    {
        'name': "Inserting an era that covers an ongoing era that has data "
        "from start.",
        'path': '/supplies/7/edit',
        'method': 'post',
        'data': {
            'start_year': "2008",
            'start_month': "11",
            'start_day': "02",
            'start_hour': "00",
            'start_minute': "00",
            'insert_era': "insert_era"},
        'status_code': 303},
    {
        'path': '/reports/233?hhdc_contract_id=29&days_hidden=0',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"029_FINISHED_watkinsexamplecom_channel_snags\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '029_FINISHED_watkinsexamplecom_channel_snags.csv',
        'status_code': 200,
        'regexes': [
            r'0,107,22 4862 4512 332,,CH023,Treglisson,'
            'Missing,True,ACTIVE,2010-02-04 20:30,',
            r'0,3,22 9205 6799 106,22 0470 7514 535,CH017,Parbola,'
            'Missing,False,ACTIVE,2003-08-03 00:00,2004-07-06 23:30,'
            '[^,]*,[^,]*,True\s*0,100,,22 0470 7514 535,'
            'CH017,Parbola,Missing,False,ACTIVE,2004-07-07 00:00,'
            '2005-09-14 23:30,[^,]*,[^,]*,False\s*0,102,,'
            '22 0470 7514 535,CH017,Parbola,Missing,False,ACTIVE,'
            '2005-09-15 00:30,2005-12-15 06:30,[^,]*,[^,]*,False\s*'
            '0,101,,22 0470 7514 535,CH017,Parbola,Missing,'
            'False,ACTIVE,2005-12-15 10:00,2008-07-06 23:30,[^,]*,'
            '[^,]*,False\s*0,56,,22 0470 7514 535,CH017,'
            'Parbola,Missing,False,ACTIVE,2008-07-07 00:00,'
            '2008-08-06 23:30,[^,]*,[^,]*,True\s*'
            '0,79,,22 0470 7514 535,CH017,Parbola,Missing,'
            'False,ACTIVE,2008-08-07 00:00,2008-09-05 23:30,'
            '[^,]*,[^,]*,False\s*0,68,,22 0470 7514 535,'
            'CH017,Parbola,Missing,False,ACTIVE,2008-09-06 00:00,'
            ',[^,]*,[^,]*,False\s*']},
    {
        'name': "Check that an era with imp_sc of 0 is displayed properly in "
        "edit mode. Supply 17",
        'path': '/eras/22/edit',
        'regexes': [
            r'<input name="imp_sc" value="0" size="9" maxlength="9">'],
        'status_code': 200},

    {
        'name': "Try out the supplies snapshot report including a last normal "
        "read type.",
        'path': '/reports/33?supply_id=9&date_year=2007&date_month=09&'
        'date_day=30&date_hour=23&date_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"030_FINISHED_watkinsexamplecom_supplies_snapshot\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '030_FINISHED_watkinsexamplecom_supplies_snapshot.csv',
        'status_code': 200,
        'regexes': [
            r'2007-09-30 23:30,CI004,Lower Treave,,,9,net,,_L,'
            r'22,HV,nhh,no,05,535,5,0127,3,MOP Contract,'
            r'mc-22 0195 4836 192,Dynamat data,dc-22 0195 4836 192,'
            r'P96C93722,2005-08-06 00:00,2007-08-01 00:00,N,,,'
            r'false,false,false,false,false,false,'
            r'22 0195 4836 192,30,510,PC 5-8 & HH HV,'
            r'Non half-hourlies 2007,341664,,2007-08-01 00:00,,,,'
            r',,,,']},

    # Try a supplies snapshot where previous era isn't AMR
    {
        'path': '/reports/33?supply_id=9&date_year=2011&date_month=05&'
        'date_day=31&date_hour=23&date_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"031_FINISHED_watkinsexamplecom_supplies_snapshot\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '031_FINISHED_watkinsexamplecom_supplies_snapshot.csv',
        'status_code': 200,
        'regexes': [
            r'2011-05-31 23:30,CI004,Lower Treave,,,9,net,,_L,'
            r'22,LV,unmetered,no,08,857,6c,0428,2,'
            r'MOP Contract,mc-22 0195 4836 192,Dynamat data,'
            r'dc-22 0195 4836 192,P96C93722,2005-08-06 00:00,unmetered,'
            r',,,false,false,false,false,false,false,'
            r'22 0195 4836 192,304,980,NHH UMS Cat B : Dusk to Dawn,'
            r'Non half-hourlies 2007,SA342376,,2007-08-01 00:00,,,'
            r',,,,,$']},

    # Try a supplies snapshot to check that latest import supplier bill is
    # correct
    {
        'path': '/reports/33?supply_id=6&date_year=2012&date_month=05&'
        'date_day=31&date_hour=23&date_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"032_FINISHED_watkinsexamplecom_supplies_snapshot\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '032_FINISHED_watkinsexamplecom_supplies_snapshot.csv',
        'status_code': 200,
        'regexes': [
            r'Other Site Ids,Other Site Names',
            r'2012-05-31 23:30,CI017,Roselands,,,6,net,,_L,22,'
            r'LV,hh,no,00,845,5,,,MOP Contract,'
            'mc-22 6354 2983 570,HH contract,01,,2007-01-01 00:00,'
            'hh,,,,true,true,false,false,false,true,'
            '22 6354 2983 570,2300,570,PC 5-8 & HH LV,'
            'Half-hourlies 2007,141 5532,,2011-06-30 00:00,,,,'
            ',,,,$']},

    {
        'name': "Run supply virtual bill over 2 months",
        'path': '/reports/291?supply_id=7&start_year=2013&start_month=09&'
        'start_day=29&start_hour=00&start_minute=00&finish_year=2013&'
        'finish_month=11&finish_day=28&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"033_FINISHED_watkinsexamplecom_supply_virtual_bills_7\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '033_FINISHED_watkinsexamplecom_supply_virtual_bills_7.csv',
        'regexes': [
            r'22 4862 4512 332,,CH023,Treglisson,141 5532,'
            r'2013-10-01 00:00,2013-10-31 23:30,,10,,,0,,,'
            r'0.0,0.0,0.0,0,'],
        'status_code': 200},
    {
        'name': "Un-ignore a site snag",
        'path': '/site_snags/36/edit',
        'method': 'post',
        'data': {
            'ignore': "false"},
        'status_code': 303},
    {
        'name': "Insert a batch with general import",
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/gi_batch.csv'},
        'status_code': 303,
        'regexes': [
            r"/general_imports/18"]},
    {
        'path': '/general_imports/18',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"The file has been imported successfully\."]},

    # Import some hh Stark DF2 data
    {
        'name': "Check df2 clock change",
        'path': '/hhdc_contracts/29/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh_clock_change.df2'},
        'status_code': 303,
        'regexes': [
            r"/hhdc_contracts/29/hh_imports/14"]},
    {
        'path': '/hhdc_contracts/29/hh_imports/14',
        'tries': {},
        'regexes': [
            r"The import has completed.*successfully."],
        'status_code': 200},
    {
        'path': '/supplies/5/hh_data?months=1&finish_year=2014&'
        'finish_month=03',
        'regexes': [
            r"<tr>\s*<td>\s*2014-03-30 00:30\s*</td>\s*<td>0</td>\s*"
            "<td>A</td>"],
        'status_code': 200},

    # Create a new batch
    {
        'name': "NHH bill outside supply period.",
        'path': '/supplier_contracts/34/add_batch',
        'method': 'post',
        'data': {
            'reference': "06-078",
            'description': "Way out batch"},
        'status_code': 303,
        'regexes': [
            r"/supplier_batches/12"]},
    {
        'path': '/supplier_bill_imports',
        'method': 'post',
        'data': {
            'supplier_batch_id': "12"},
        'files': {'import_file': 'test/nhh_bills2007.csv'},
        'status_code': 303,
        'regexes': [
            r"/supplier_bill_imports/9"]},

    {
        'name': 'Supplier contract 34, batch 12',
        'path': '/supplier_bill_imports/9',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"All the bills have been successfully loaded and attached to "
            "the batch\."]},
    {
        'path': '/reports/219?supply_id=7&months=1&end_year=2002&end_month=1',
        'status_code': 200,
        'regexes': [
            r'"2002-01-01 00:00","2002-01-31 23:30","7","22 4862 4512 332","",'
            '"06-078","20","jg87593jfj","2002-02-02 00:00","N","15","00001",'
            '"1","2002-01-04 23:30","2286","E","2002-01-06 23:30","2927",'
            '"E"']},

    # Attach another site to an era. Supply 2
    {
        'name': "Check the 'also supplies' field of a site.",
        'path': '/eras/8/edit',
        'method': 'post',
        'data': {
            'site_code': "CI005",
            'attach': "Attach"},
        'status_code': 303},
    {
        'path': '/sites/1',
        'regexes': [
            r'3475 1614 211\s*</td>\s*<td>\s*this site\s*</td>\s*<td>\s*'
            '<a href="/sites/3" title="Wheal Rodney">CI005</a>\s*</td>'],
        'status_code': 200},
    {
        'name': "In supplies snapshot, test the last billed date of MOP and "
        "DC bills",
        'path': '/reports/33?supply_id=5&date_year=2014&date_month=05&'
        'date_day=31&date_hour=23&date_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"034_FINISHED_watkinsexamplecom_supplies_snapshot\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '034_FINISHED_watkinsexamplecom_supplies_snapshot.csv',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r'2014-05-31 23:30,CI005,Wheal Rodney,,,5,gen,'
            'chp,_L,22,LV,hh,no,00,845,5,,,MOP Contract,'
            '22 0883 6932 301,HH contract,22 0883 6932 301,,'
            '2002-01-01 00:00,hh,,2007-10-31 23:30,2007-10-31 23:30,'
            'true,true,false,false,false,true,22 0883 6932 301,'
            '350,570,PC 5-8 & HH LV,Half-hourlies 2013,4341,0,,'
            ',,,,,,,']},
    {
        'name': "Site summary page that has data quality errors.",
        'path': '/sites/1/months?finish_year=2005&finish_month=11',
        'regexes': [
            r'See <a href="/sites/1/gen_graph\?months=1&amp;'
            'finish_year=2005&amp;finish_month=10">generation graph</a>']},
    {
        'name': "HTML virtual bill",
        'path': '/supplies/10/virtual_bill?start_year=2014&start_month=05&'
        'start_day=1&start_hour=0&start_minute=0&finish_year=2014&'
        'finish_month=05&finish_day=31&finish_hour=23&finish_minute=30',
        'status_code': 200},

    {
        'name': "HTML virtual bill that spans 3 eras",
        'path': '/supplies/2/virtual_bill?start_year=2005&start_month=05&'
        'start_day=1&start_hour=0&start_minute=0&finish_year=2006&'
        'finish_month=07&finish_day=31&finish_hour=23&finish_minute=30',
        'status_code': 200},

    {
        'name': "Make sure rate scripts remain contiguous.",
        'path': '/non_core_rate_scripts/26/edit',
        'method': 'post',
        'data': {
            # First rate script of non-core contract triad
            'start_year': "2005",
            'start_month': "04",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00",
            'has_finished': "true",
            'finish_year': "2006",
            'finish_month': "03",
            'finish_day': "30",
            'finish_hour': "23",
            'finish_minute': "30",
            'script': ""},
        'status_code': 303},
    {
        'path': '/non_core_rate_scripts/27',
        'regexes': [
            r"2006-03-31 00:00"],
        'status_code': 200},
    {
        'name': "Put it back to how it was",
        'path': '/non_core_rate_scripts/26/edit',
        'method': 'post',
        'data': {
            'start_year': "2005",
            'start_month': "04",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00",
            'has_finished': "true",
            'finish_year': "2006",
            'finish_month': "03",
            'finish_day': "31",
            'finish_hour': "23",
            'finish_minute': "30",
            'script': ""},
        'status_code': 303},
    {
        'name': "Try sites monthly duration with displaced bill",
        'path': '/reports/161?site_id=1&months=1&finish_year=2010&'
        'finish_month=07',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"035_FINISHED_watkinsexamplecom_site_monthly_duration_for_"
            r"CI004_1_to_2010_7\.csv"]},
    {
        'path': '/downloads/'
        '035_FINISHED_watkinsexamplecom_site_monthly_duration_for_'
        'CI004_1_to_2010_7.csv',
        'status_code': 200,
        'regexes': [
            r'"CI004",']},
    {
        'name': "Try sites monthly duration covering bills",
        'path': '/reports/161?site_id=4&months=1&finish_year=2011&'
        'finish_month=05',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"036_FINISHED_watkinsexamplecom_site_monthly_duration_for_"
            r"CI017_1_to_2011_5\.csv"]},
    {
        'path': '/downloads/'
        '036_FINISHED_watkinsexamplecom_site_monthly_duration_for_'
        'CI017_1_to_2011_5.csv',
        'status_code': 200,
        'regexes': [
            r'"CI017",']},
    {
        'name': "Try sites monthly duration with a clocked bill",
        'path': '/supplier_bill_imports',
        'method': 'post',
        'data': {
            'supplier_batch_id': "7"},
        'files': {'import_file': 'test/bills-nhh-clocked.csv'},
        'status_code': 303},
    {
        'path': '/reports/161?site_id=4&months=1&finish_year=2012&'
        'finish_month=02',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"037_FINISHED_watkinsexamplecom_site_monthly_duration_for_"
            r"CI017_1_to_2012_2\.csv"]},
    {
        'path': '/downloads/'
        '037_FINISHED_watkinsexamplecom_site_monthly_duration_for_'
        'CI017_1_to_2012_2.csv',
        'status_code': 200,
        'regexes': [
            r'"CI017",']},

    # Bill check on a clocked bill
    {
        'path': '/reports/111?bill_id=21',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"038_FINISHED_watkinsexamplecom_bill_check\.csv"]},
    {
        'path': '/downloads/038_FINISHED_watkinsexamplecom_bill_check.csv',
        'status_code': 200,
        'regexes': [
            r'07-002,3423760010,N,10,9.07,0.21,2012-01-05 00:00,'
            '2012-01-10 23:30,22 1065 3921 534,CI017,Roselands,'
            r'2012-01-05 00:00,2012-01-10 23:30,21,30.00\d*,9.07,'
            r'0.9999999999999986,8.070000000000002,10.0,'
            r'9.999999999999998,,']},
    {
        'name': "Monthly supplies duration with export hh data",
        'path': '/reports/177?supply_id=1&months=1&end_year=2008&end_month=07',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"039_FINISHED_watkinsexamplecom_supplies_monthly_duration_for_"
            r"1_1_to_2008_7\.csv"]},
    {
        'path': '/downloads/'
        '039_FINISHED_watkinsexamplecom_supplies_monthly_duration_for_'
        '1_1_to_2008_7.csv',
        'status_code': 200,
        'regexes': [
            r"supply-id,supply-name,source-code,generator-type,month,pc-code,"
            "msn,site-code,site-name,metering-type,import-mpan-core,"
            "metered-import-kwh,metered-import-net-gbp,"
            "metered-import-estimated-kwh,billed-import-kwh,"
            "billed-import-net-gbp,export-mpan-core,metered-export-kwh,"
            "metered-export-estimated-kwh,billed-export-kwh,"
            "billed-export-net-gbp,problem,timestamp",
            r'1,"Hello","sub","","2008-07-31 23:30","00","","CH017","Parbola",'
            '"hh","None","18.281","0","0","0","0","22 0470 7514 535","0","0",'
            '"0","0",""']},

    # Supply level hh data CSV, hh per row
    {
        'name': "Supply level hh data CSV, hh per row",
        'path': '/reports/187',
        'method': 'post',
        'data': {
            'supply_id': '7', 'start_year': '2008', 'start_month': '01',
            'start_day': '01', 'start_hour': '0', 'start_minute': '0',
            'finish_year': '2008', 'finish_month': '01', 'finish_day': '31',
            'finish_hour': '23', 'finish_minute': '30'},
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"040_FINISHED_watkinsexamplecom_hh_data_row_200801010000\.csv"]},
    {
        'path': '/downloads/'
        '040_FINISHED_watkinsexamplecom_hh_data_row_200801010000.csv',
        'status_code': 200,
        'regexes': [
            r'"CH023","22 4862 4512 332","","2008-01-01 00:00","3.77","A","",'
            '"","","","","","","","",""']},

    {
        'name': "Supply level hh data CSV, hh per row. MPAN core filter.",
        'path': '/reports/187',
        'method': 'post',
        'data': {
            'start_year': '2010', 'start_month': '01', 'start_day': '01',
            'start_hour': '0', 'start_minute': '0', 'finish_year': '2010',
            'finish_month': '12', 'finish_day': '31', 'finish_hour': '23',
            'finish_minute': '30', 'mpan_cores': '22 4862 4512 332'},
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"041_FINISHED_watkinsexamplecom_hh_data_row_201001010000\.csv"]},
    {
        'path': '/downloads/'
        '041_FINISHED_watkinsexamplecom_hh_data_row_201001010000.csv',
        'status_code': 200,
        'regexes': [
            r'"Export REACTIVE_EXP Status"\s'
            r'"CH023","22 4862 4512 332","","2010-02-04 20:00","30.4339","A",'
            r'"","","","","","","","","",""']},

    {
        'name': "General import of bill with start date after finish date",
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/general-bills-error.csv'},
        'status_code': 303,
        'regexes': [
            r"/general_imports/19"]},
    {
        'path': '/general_imports/19',
        'tries': {},

        # Check good error message
        'regexes': [
            r"The bill start date 2007-01-05 00:00 can&#39;t be after the "
            "finish date 2007-01-01 00:00."],
        'status_code': 200},
    {
        'name': "Manually insert a bill with errors",
        'path': '/supplier_batches/4/add_bill',
        'method': 'post',
        'data': {
            'mpan_core': "",
            'reference': "",
            'issue_year': "2014",
            'issue_month': "7",
            'issue_day': "30",
            'issue_hour': "15",
            'issue_minute': "30",
            'start_year': "2014",
            'start_month': "07",
            'start_day': "30",
            'start_hour': "15",
            'start_minute': "30",
            'finish_year': "2014",
            'finish_month': "07",
            'finish_day': "30",
            'finish_hour': "15",
            'finish_minute': "30",
            'kwh': "0",
            'net': "0",
            'vat': "0",
            'gross': "0",
            'account': "0",
            'bill_type_id': "1",
            'breakdown': "{}"},
        'status_code': 400,

        # Check good error message
        'regexes': [
            r"The MPAN core &#39;&#39; must contain exactly 13 digits\."]},

    # Must straddle two eras
    {
        'name': "HH by HH virtual bill",
        'path': '/reports/387?supply_id=5&start_year=2012&start_month=12&'
        'start_day=31&start_hour=23&start_minute=30&finish_year=2013&'
        'finish_month=1&finish_day=1&finish_hour=23&finish_minute=30',
        'status_code': 200,
        'regexes': [
            r"supply_virtual_bills_hh_5.csv",
            r'"22 0883 6932 301",']},

    # Add in reactive HH
    {
        'name': "Look at monthly report with an MD in kVA",
        'path': '/channels/55/edit',
        'method': 'post',
        'data': {
            'start_year': "2010",
            'start_month': "02",
            'start_day': "04",
            'start_hour': "20",
            'start_minute': "00",
            'insert': "Insert",
            'value': "45.7",
            'status': "A"},
        'status_code': 303,
        'regexes': [
            r"/channels/55'"]},
    {
        'path': '/supplies/7/months?is_import=true&years=1&year=2010',
        'status_code': 200,
        'regexes': [
            r"<tr>\s*<td>2010-02-01 00:00</td>\s*<td>22 4862 4512 332</td>\s*"
            "<td>\s*2010-02-04 20:00\s*</td>\s*<td>60.9</td>\s*"
            "<td>91.4</td>\s*<td>0.55</td>\s*<td>109.8</td>\s*<td>230</td>\s*"
            "<td>\s*30\s*</td>\s*</tr>"]},

    # Add in second batch
    {
        'name': "Order of HHDC batches",
        'path': '/hhdc_contracts/29/add_batch',
        'method': 'post',
        'data': {
            'reference': "7",
            'description': ""},
        'status_code': 303},
    {
        'path': '/hhdc_batches?hhdc_contract_id=29',
        'status_code': 200,
        'regexes': [
            r'<a\s*href="/hhdc_contracts/29"\s*>HH contract</a>',
            r'<tr>\s*<td>\s*'
            '<a href="/hhdc_batches/13">\s*7\s*'
            '</a>\s*</td>\s*<td></td>\s*</tr>\s*<tr>\s*<td>\s*'
            '<a href="/hhdc_batches/8">\s*'
            '001-7t\s*</a>\s*</td>\s*<td>hhdc batch</td>\s*</tr>']},

    # Add in second batch
    {
        'name': "Order of MOP batches",
        'path': '/mop_contracts/32/add_batch',
        'method': 'post',
        'data': {
            'reference': "7a",
            'description': ""},
        'status_code': 303},
    {
        'path': '/mop_batches?mop_contract_id=32',
        'status_code': 200,
        'regexes': [
            r'<tr>\s*<td>\s*'
            '<a href="/mop_batches/9">\s*'
            '99/992\s*</a>\s*</td>\s*<td>mop batch</td>\s*</tr>\s*<tr>\s*'
            '<td>\s*'
            '<a href="/mop_batches/14">\s*7a\s*'
            '</a>\s*</td>\s*<td></td>\s*</tr>']},

    {
        'name': "MTCs",
        'path': '/mtcs',
        'status_code': 200,
        'regexes': [
            r'<tr>\s*<td>\s*'
            '<a href="/mtcs/96">\s*001\s*'
            '</a>\s*</td>\s*<td>\s*'
            '<a href="/dno_contracts/15">\s*'
            '12\s*</a>\s*</td>\s*<td>Economy 7, 23.30 - 06.30</td>\s*<td>\s*'
            '<a href="/meter_types/15">\s*TP\s*'
            '</a>\s*</td>\s*<td>2</td>\s*</tr>']},

    {
        'path': '/mtcs/96',
        'status_code': 200,
        'regexes': [
            r'<tr>\s*<th>Code</th>\s*<td>001</td>\s*</tr>\s*<tr>\s*'
            '<th>DNO</th>\s*<td>\s*'
            '<a href="/dno_contracts/15">\s*'
            '12\s*</a>\s*</td>\s*</tr>']},

    {
        'path': '/mtcs/1',
        'status_code': 200,
        'regexes': [
            r"<tr>\s*<th>Code</th>\s*<td>500</td>\s*</tr>\s*<tr>\s*"
            "<th>DNO</th>\s*<td>\s*All\s*</td>\s*</tr>"]},

    {
        'name': "Move forward era with channels, when era with no channels "
        "precedes it",
        'path': '/eras/17/add_channel',
        'method': 'post',
        'data': {
            'imp_related': "true",
            'channel_type': "ACTIVE"},
        'status_code': 303},
    {
        'path': '/eras/17/edit',
        'method': 'post',
        'data': {
            'msn': "I02D89150",
            'start_year': "2010",
            'start_month': "01",
            'start_day': "06",
            'start_hour': "00",
            'start_minute': "00",
            'is_ended': "false",
            'mop_contract_id': "32",
            'mop_account': "mc-22 1065 3921 534",
            'hhdc_contract_id': "29",
            'hhdc_account': "dc-22 1065 3921 534",
            'pc_id': "3",
            'mtc_code': "801",
            'cop_id': "6",
            'ssc_code': "366",
            'imp_llfc_code': "110",
            'imp_mpan_core': "22 1065 3921 534",
            'imp_sc': "30",
            'imp_supplier_contract_id': "37",
            'imp_supplier_account': "SA342376000"},
        'status_code': 303},

    # Add new era, so that bill straddles join
    {
        'name': "NHH dumb bill that straddles dumb and AMR eras",
        'path': '/supplies/11/edit',
        'method': 'post',
        'data': {
            'start_year': "2007",
            'start_month': "07",
            'start_day': "10",
            'start_hour': "00",
            'start_minute': "00",
            'insert_era': "Insert"},
        'regexes': [
            r"/supplies/11"],
        'status_code': 303},

    # Add a channel to the new era
    {
        'path': '/eras/27/add_channel',
        'method': 'post',
        'data': {
            'imp_related': "true",
            'channel_type': "ACTIVE"},
        'status_code': 303},
    {
        'path': '/reports/111?bill_id=6',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"042_FINISHED_watkinsexamplecom_bill_check\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '042_FINISHED_watkinsexamplecom_bill_check.csv',
        'status_code': 200,
        'regexes': [
            r'06-002,23618619,N,0,49119,8596,2007-06-30 00:00,'
            '2007-07-31 00:00,22 9974 3438 105,CI005,Wheal Rodney,'
            '2007-06-30 00:00,2007-07-31 00:00,6,0,49119.0,0.0,'
            '49119.0,8596.0,0.0,8596.0,,0.0,,0.0,9.53\d*,,']},
    {
        'name': "NHH dumb bill with prev and pres dates in different eras",
        'path': '/eras/10/edit',
        'method': 'post',
        'data': {
            'start_year': "2005",
            'start_month': "09",
            'start_day': "06",
            'start_hour': "00",
            'start_minute': "00",
            'is_ended': "true",
            'finish_year': "2011",
            'finish_month': "01",
            'finish_day': "19",
            'finish_hour': "23",
            'finish_minute': "30",
            'mop_contract_id': "32",
            'mop_account': "mc-22 1065 3921 534",
            'hhdc_contract_id': "30",
            'hhdc_account': "dc-22 1065 3921 534",
            'msn': "I02D89150",
            'pc_id': "3",
            'mtc_code': "801",
            'cop_id': "5",
            'ssc_code': "0393",
            'imp_llfc_code': "110",
            'imp_mpan_core': "22 1065 3921 534",
            'imp_sc': "30",
            'imp_supplier_contract_id': "37",
            'imp_supplier_account': "SA342376"},
        'status_code': 303},

    # Check the bill
    {
        'path': '/reports/111?bill_id=13',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"043_FINISHED_watkinsexamplecom_bill_check\.csv"]},
    {
        'path': '/downloads/043_FINISHED_watkinsexamplecom_bill_check.csv',
        'status_code': 200,
        'regexes': [
            r'07-002,3423760005,N,150,98.17,15.01,'
            r'2011-01-05 00:00,2011-01-10 23:30,22 1065 3921 534,'
            r'CI017,Roselands,2011-01-05 00:00,2011-01-10 23:30,13,'
            r'692.9175824\d*,98.17,164.0999999999997,-65.92999999999971,150.0,'
            r'1641.0,,']},

    # Update register read to make the TPR a teleswitch one
    {
        'name': "Check bill with teleswitch TPR",
        'path': '/reads/16/edit',
        'method': 'post',
        'data': {
            'mpan': "22 1065 3921 534",
            'coefficient': "1",
            'msn': "I02D89150",
            'units': "kWh",
            'tpr_id': "643",
            'previous_year': "2012",
            'previous_month': "01",
            'previous_day': "04",
            'previous_hour': "23",
            'previous_minute': "30",
            'previous_value': "473",
            'previous_type_id': "1",
            'present_year': "2012",
            'present_month': "01",
            'present_day': "06",
            'present_hour': "23",
            'present_minute': "30",
            'present_value': "725",
            'present_type_id': "1",
            'update': "Update"},
        'status_code': 303},

    {
        'name': "Delete the channel to make it a dumb NHH",
        'path': '/channels/56/edit',
        'method': 'post',
        'data': {
            'delete': 'Delete'},
        'status_code': 303},

    {
        'name': "Check the bill",
        'path': '/reports/111?bill_id=21',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"044_FINISHED_watkinsexamplecom_bill_check\.csv"]},
    {
        'path': '/downloads/044_FINISHED_watkinsexamplecom_bill_check.csv',
        'status_code': 200,
        'regexes': [
            r'07-002,3423760010,N,10,9.07,0.21,2012-01-05 00:00,'
            '2012-01-10 23:30,22 1065 3921 534,CI017,Roselands,'
            '2012-01-05 00:00,2012-01-10 23:30,21,0,9.07,0,9.07,'
            '10.0,0,,']},

    # Update register read to make the TPR a teleswitch one },
    {
        'name': "CRC with read pair straddling eras",
        'path': '/reads/7/edit',
        'method': 'post',
        'data': {
            'mpan': "22 1065 3921 534",
            'coefficient': "1",
            'msn': "I02D89150",
            'units': "kWh",
            'tpr_id': "1",
            'previous_year': "2009",
            'previous_month': "04",
            'previous_day': "04",
            'previous_hour': "23",
            'previous_minute': "30",
            'previous_value': "14281",
            'previous_type_id': "1",
            'present_year': "2010",
            'present_month': "01",
            'present_day': "06",
            'present_hour': "23",
            'present_minute': "30",
            'present_value': "15924",
            'present_type_id': "1",
            'update': "Update"},
        'status_code': 303},
    {
        'path': '/reports/207?supply_id=10&year=2009',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"045_FINISHED_watkinsexamplecom_crc_2009_2010_supply_10\.csv"]},
    {
        'path': '/downloads/'
        '045_FINISHED_watkinsexamplecom_crc_2009_2010_supply_10.csv',
        'status_code': 200,
        'regexes': [
            r'"10","22 1065 3921 534","CI017","Roselands","2009-04-01 00:00",'
            r'"2010-03-31 23:30",".*?","0","0","277.0","0","0","0","365.0",'
            r'"0","277.0","365.0","Actual","0","0","2164.9638989169675","0",'
            r'"0","0","2164.9638989169675"']},

    # Add a scenario
    {
        'name': "Run a BAU scenario",
        'path': '/supplier_contracts/add',
        'method': 'post',
        'data': {
            'participant_id': "54",  # COOP
            'name': "scenario_bau",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'charge_script': "",
            'properties': """
{
    'bsuos' : {
        'start_date': None,  # Date or None for latest rate script
        'multiplier': 1.5,
        'constant': 0,
    },

    'ccl': {
        'start_date': datetime(2014, 10, 1),
        'multiplier': 1,
        'constant': 0,
    },

    'aahedc': {
        'start_date': None,
        'multiplier': 0,
        'constant': 0.00091361,
    },

    'scenario_start': datetime(2015, 6, 1),  # Date or None for this month
    'scenario_duration': 1,  # Number of months

    'kw_changes':

    # MPAN Core, Date, kW
    '''
    ''',
}
""", },
        'regexes': [
            r"/supplier_contracts/38"],
        'status_code': 303},

    {
        'name': "Run scenario for a site where there are no site groups",
        'path': '/reports/247?site_id=1&scenario_id=38',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"046_FINISHED_watkinsexamplecom_scenario_bau_20150601_0000_for_"
            r"1_months_site_CI004\.ods"]},
    {
        'path': '/downloads/'
        '046_FINISHED_watkinsexamplecom_scenario_bau_20150601_0000_for_'
        '1_months_site_CI004.ods',
        'status_code': 200,

        'regexes': [
            r'CI005',
            r'<table:table-cell office:string-value="exp-supplier-problem" '
            r'office:value-type="string"/>\s*'
            r'</table:table-row>']},

    {
        'name': "Run scenario for a site where there are site groups",
        'path': '/reports/247?site_id=3&scenario_id=38',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"047_FINISHED_watkinsexamplecom_scenario_bau_20150601_0000_for_"
            r"1_months_site_CI005\.ods"]},
    {
        'path': '/downloads/'
        '047_FINISHED_watkinsexamplecom_scenario_bau_20150601_0000_for_'
        '1_months_site_CI005.ods',
        'status_code': 200,
        'regexes': [
            r"CI005"]},

    {
        'name': "Check BSUoS automatic import page",
        'path': '/non_core_contracts/3/auto_importer',
        'status_code': 200,
        'regexes': [
            r"Is Locked\?"]},
    {
        'name': "Check RCRC automatic import page",
        'path': '/non_core_contracts/6/auto_importer',
        'status_code': 200,
        'regexes': [
            r"Is Locked\?"]},
    {
        'name': "Check TLM automatic import page",
        'path': '/non_core_contracts/9/auto_importer',
        'status_code': 200,
        'regexes': [
            r"Is Locked\?"]},

    # Add a scenario
    {
        'name': "Run an increased BSUoS scenario",
        'path': '/supplier_contracts/add',
        'method': 'post',
        'data': {
            'participant_id': "54",  # COOP
            'name': "scenario_bsuos",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'charge_script': "",
            'properties': """
{
    'bsuos' : {
        'start_date': datetime(2011, 1, 1),
        'multiplier': 1,
        'constant': 0.1,
    },

    'ccl': {
        'start_date': datetime(2014, 10, 1),
        'multiplier': 1,
        'constant': 0,
    },

    'aahedc': {
        'start_date': datetime(2011, 1, 1),
        'multiplier': 1,
        'constant': 0.1,
    },

    'scenario_start': datetime(2011, 1, 1),  # Date or None for this month
    'scenario_duration': 1,  # Number of months
    'resolution': 'hh',  # 'hh' or 'month'

    'kw_changes':

    # MPAN Core, Date, kW
    '''
    ''',
}
"""},
        'regexes': [
            r"/supplier_contracts/39"],
        'status_code': 303},

    # Run scenario for a site
    {
        'path': '/reports/247?site_id=3&scenario_id=39',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"048_FINISHED_watkinsexamplecom_scenario_bsuos_20110101_0000_"
            r"for_1_months_site_CI005\.ods"]},
    {
        'path': '/downloads/'
        '048_FINISHED_watkinsexamplecom_scenario_bsuos_20110101_0000_for_'
        '1_months_site_CI005.ods',
        'status_code': 200,
        'regexes': [
            r'<table:table-row>\s*'
            r'<table:table-cell office:string-value="22 6158 2968 220" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="22 3479 7618 470" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="hh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="net" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="1" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="00" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="CI005" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Wheal Rodney" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="CI004" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2011-01-31T23:30:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="9"/>\s*'
            r'<table:table-cell office:value="189.22680000000003" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="112.0808" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="5"/>\s*'
            r'<table:table-cell office:value="189.22680000000003" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="10" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="179.22680000000003" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0047" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="5.89" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="130" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="31" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0163" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="65.689" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="31" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0163" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="4"/>\s*'
            r'<table:table-cell office:value="0.00202" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="88" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell table:number-columns-repeated="6"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="18"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2010-01-07T17:00:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.058" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2010-01-25T17:00:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.058" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2009-12-15T17:00:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.058" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="24.031029" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="1" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.00052" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.11678" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="31" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.6338" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="19.647800000000014" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.10016297" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="4"/>\s*'
            r'<table:table-cell office:value="112.0808" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0047" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="5.89" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="20" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="31" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0163" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="10.106" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="31" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell table:number-columns-repeated="4"/>\s*'
            r'<table:table-cell office:value="0.00106" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="88" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="18"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2010-01-07T17:00:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.058" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2010-01-25T17:00:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.058" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2009-12-15T17:00:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.058" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="24.031029" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="1" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'</table:table-row>']},

    # Add a scenario
    {
        'name': "Run a used and generated scenario",
        'path': '/supplier_contracts/add',
        'method': 'post',
        'data': {
            'participant_id': "54",  # COOP
            'name': "scenario_used",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'charge_script': "",
            'properties': r"""
{
    'bsuos' : {
        'start_date': datetime(2011, 1, 1),
        'multiplier': 1,
        'constant': 0,
    },

    'ccl': {
        'start_date': datetime(2014, 10, 1),
        'multiplier': 1,
        'constant': 0,
    },

    'aahedc': {
        'start_date': None,
        'multiplier': 0,
        'constant': 0.00091361,
    },

    'scenario_start': datetime(2011, 1, 1),  # Date or None for this month
    'scenario_duration': 1,  # Number of months
    'resolution': 'hh',  # 'hh' or 'month'

    'kw_changes':
    # CSV format with the following columns
    # Site Code, Type ('used' or 'generated') , Date (yyyy-mm-dd), Multiplier
    "CI005, used, 2011-01-01, 0.5\nCI005, generated, 2011-01-01, 2"}
""", },
        'regexes': [
            r"/supplier_contracts/40"],
        'status_code': 303},

    # Run scenario for a site
    {
        'path': '/reports/247?site_id=3&scenario_id=40',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r'049_FINISHED_watkinsexamplecom_scenario_used_20110101_0000_for_'
            r'1_months_site_CI005\.ods']},
    {
        'path': '/downloads/'
        '049_FINISHED_watkinsexamplecom_scenario_used_20110101_0000_for_'
        '1_months_site_CI005.ods',
        'status_code': 200,
        'regexes': [
            r'<table:table-row>\s*'
            r'<table:table-cell office:string-value="22 0195 4836 192" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="unmetered" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="net" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="2" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="P96C93722" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="08" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="CI005" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Wheal Rodney" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="CI004" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2011-01-31T23:30:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="12.909589041095739" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="6"/>\s*'
            r'<table:table-cell office:value="12.909589041095739" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="17.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="6"/>\s*'
            r'<table:table-cell office:value="17.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="10" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="7" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="81"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="18"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="12.909589041095739" '
            r'office:value-type="float"/>\s*'
            r'</table:table-row>']},

    # Try to detach an era from its physical site
    {
        'name': "Detach an era",
        'path': '/eras/8/edit',
        'method': 'post',
        'data': {
            'site_id': "1",
            'detach': "Detach"},
        'status_code': 400,
        'regexes': [
            r"<li>You can&#39;t detach an era from the site where it is "
            "physically located.</li>"]},
    {
        'name': "Look at a DNO",
        'path': '/dno_contracts/13',
        'status_code': 200},

    {
        'name': "Look at the SSCs",
        'path': '/sscs',
        'status_code': 200},

    {
        'name': "Look at an SSC",
        'path': '/sscs/1',
        'status_code': 200},

    {
        'name': "Rate start after last rate scripts",
        'path': '/supplier_contracts/39/edit',
        'method': 'post',
        'data': {
            'party_id': "90",  # COOP
            'name': "scenario_bsuos",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'charge_script': "",
            'properties': """
{
    'bsuos' : {
        'start_date': datetime(5010, 1, 1),
        'multiplier': 1,
        'constant': 0.1,
    },

    'ccl': {
        'start_date': datetime(2014, 10, 1),
        'multiplier': 1,
        'constant': 0,
    },

    'aahedc': {
        'start_date': datetime(2011, 1, 1),
        'multiplier': 1,
        'constant': 0.1,
    },

    'scenario_start': datetime(5011, 1, 1),  # Date or None for this month
    'scenario_duration': 1,  # Number of months
    'resolution': 'hh',  # 'hh' or 'month'

    'kw_changes':

    # MPAN Core, Date, kW
    '''
    ''',
}
"""},
        'regexes': [
            r"/supplier_contracts/39"],
        'status_code': 303},

    # Run scenario for a site
    {
        'path': '/reports/247?site_id=3&scenario_id=39',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"050_FINISHED_watkinsexamplecom_scenario_bsuos_50110101_0000_"
            r"for_1_months_site_CI005\.ods"]},
    {
        'path': '/downloads/'
        '050_FINISHED_watkinsexamplecom_scenario_bsuos_50110101_0000_'
        'for_1_months_site_CI005.ods',
        'status_code': 200,
        'regexes': [
            r'<table:table-row>\s*'
            r'<table:table-cell office:string-value="22 6158 2968 220" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="22 3479 7618 470" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="hh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="net" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="1" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="00" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="CI005" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Wheal Rodney" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="CI004" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:date-value="5011-01-31T23:30:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="9"/>\s*'
            r'<table:table-cell '
            r'office:value="216.53470000000002" office:value-type="float"/>\s*'
            r'<table:table-cell office:value="103.8937" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="5"/>\s*'
            r'<table:table-cell office:value="216.53470000000002" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="10" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="206.53470000000002" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.00525288" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="5.89" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="130" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="31" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0229" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="92.287" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="31" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0229" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="4"/>\s*'
            r'<table:table-cell office:value="0.0026" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="88" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell table:number-columns-repeated="6"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="18"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2014-11-25T17:00:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.065" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2014-12-06T17:00:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.05" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2015-01-30T17:00:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.065" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="38.699518" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="1" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.00066" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.19574" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="31" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.6567" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="20.357700000000012" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.10016297" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="4"/>\s*'
            r'<table:table-cell office:value="103.8937" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.00525288" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="5.89" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="20" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="31" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell office:value="31" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell table:number-columns-repeated="4"/>\s*'
            r'<table:table-cell office:value="0.00095" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="88" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="18"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2014-11-25T17:00:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.065" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2014-12-06T17:00:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.05" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2015-01-30T17:00:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.065" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="38.699518" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="1" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'</table:table-row>']},

    # GI Delete LLFC
    {
        'name': "GI Delete LLFC",
        'path': "/general_imports",
        'method': "post",
        'files': {"import_file": "test/gi_delete_llfc.csv"},
        'status_code': 303,
        'regexes': [r"/general_imports/20"]},
    {
        'name': "Check import has succeeded",
        'path': "/general_imports/20",
        'tries': {},
        'status_code': 200,
        'regexes': [r"The file has been imported successfully\."]},

    {
        'name': "MDD Converter. Market participant",
        'path': "/reports/163",
        'method': "post",
        'files': {"file": "test/Market_Participant_233.csv"},
        'status_code': 200,
        'regexes':  [
            r'"insert","participant","BETH","Bethnal Energy Limited"',
            r'"insert","participant","PENL","Peel Electricity Networks Ltd"']},

    {
        'name': "MDD Converter. Market participant",
        'path': "/general_imports",
        'method': "post",
        'files': {'import_file': "test/gi_insert_participant.csv"},
        'status_code': 303,
        'regexes': [
            r'/general_imports/21']},
    {
        'name': "MDD Converter. Market participant",
        'path': "/general_imports/21",
        'tries': {'max': 10, 'period': 1},
        'status_code': 200,
        'regexes': [r"The file has been imported successfully\."]},

    {
        'name': "MDD Converter. Market role",
        'path': "/reports/163",
        'method': "post",
        'files': {"file": "test/Market_Role_234.csv"},
        'status_code': 200,
        'regexes':  [
            r'"insert","market_role","7","Fusion Balancer"',
            r'"update","market_role","S","Settlement System Controller"']},

    {
        'name': "MDD Converter. Market role",
        'path': "/general_imports",
        'method': "post",
        'files': {'import_file': "test/gi_insert_market_role.csv"},
        'status_code': 303,
        'regexes': [
            "/general_imports/22"]},
    {
        'name': "MDD Converter. Market role",
        'path': "/general_imports/22",
        'tries': {'max': 10, 'period': 1},
        'status_code': 200,
        'regexes': [r"The file has been imported successfully\."]},

    {
        'name': "MDD Converter. Party",
        'path': "/reports/163",
        'method': "post",
        'files': {"file": "test/Market_Participant_Role_232.csv"},
        'status_code': 200,
        'regexes':  [
            r'\s\s"insert","party","M","AMSL",'
            r'"Accrington Metering Services Ltd","2015-08-19 00:00","",""',
            r'"insert","party","X","BETH","BETHNAL ENERGY LIMITED",'
            r'"2015-08-19 00:00","",""',
            r'"insert","party","R","PENL","Peel Electricity Networks Ltd",'
            r'"2015-06-17 00:00","","30"']},

    {
        'name': "MDD Converter. Party",
        'path': "/general_imports",
        'method': "post",
        'files': {'import_file': "test/gi_party.csv"},
        'status_code': 303,
        'regexes': [
            "/general_imports/23"]},
    {
        'name': "MDD Converter. Party",
        'path': "/general_imports/23",
        'tries': {'max': 10, 'period': 1},
        'status_code': 200,
        'regexes': [r"The file has been imported successfully\."]},

    {
        'name': "MDD Converter. Check imported party looks okay",
        'path': "/participants/604",
        'status_code': 200,
        'regexes': [
            r'<tr>\s*<td>\s*'
            r'<a href="/parties/1011">Peel Electricity Networks Ltd</a>\s*'
            r'</td>\s*<td>\s*'
            r'<a href="/market_roles/27">Distributor</a>\s*'
            r'</td>\s*<td>\s*30\s*</td>\s*</tr>']},

    {
        'name': "MDD Converter. Convert LLFC.",
        'path': "/reports/163",
        'method': "post",
        'files': {"file": "test/Line_Loss_Factor_Class_225.csv"},
        'status_code': 200,
        'regexes':  [
            '"insert","llfc","19","889","PROLOGIS, BEDDINGTON - IMPORT","LV",'
            '"False","True","1996-04-01 00:00",""']},

    {
        'name': "GI Insert LLFC",
        'path': "/general_imports",
        'method': "post",
        'files': {'import_file': "test/gi_insert_llfc.csv"},
        'status_code': 303,
        'regexes': [
            "/general_imports/24"]},
    {
        'name': "GI Insert LLFC. Check it worked.",
        'path': "/general_imports/24",
        'tries': {'max': 10, 'period': 1},
        'status_code': 200,
        'regexes': [r"The file has been imported successfully\."]},

    {
        'name': "MDD Converter. MTC Meter Type",
        'path': "/reports/163",
        'method': "post",
        'files': {"file": "test/MTC_Meter_Type_234.csv"},
        'status_code': 200,
        'regexes':  [
            r'"update","meter_type","6A","COP6\(a\)  20 days memory",'
            r'"1996-04-02 00:00",""']},
    {
        'name': "MDD Converter. Meter Timeswitch Class",
        'path': "/general_imports",
        'method': "post",
        'files': {'import_file': "test/gi_mtc_meter_type.csv"},
        'status_code': 303,
        'regexes': [
            "/general_imports/25"]},
    {
        'name': "MDD Converter. Meter Timeswitch Class",
        'path': "/general_imports/25",
        'tries': {'max': 10, 'period': 1},
        'status_code': 200,
        'regexes': [r"The file has been imported successfully\."]},

    {
        'name': "MDD Converter. Meter Timeswitch Class",
        'path': "/reports/163",
        'method': "post",
        'files': {"file": "test/Meter_Timeswitch_Class_233.csv"},
        'status_code': 200,
        'regexes':  [
            r'"insert","mtc","","997","ENO - Private Network","False",'
            r'"False","True","XX","CR","0","2012-08-15 00:00",""']},
    {
        'name': "MDD Converter. Meter Timeswitch Class",
        'path': "/general_imports",
        'method': "post",
        'files': {'import_file': "test/gi_meter_timeswitch_class.csv"},
        'status_code': 303,
        'regexes': [
            "/general_imports/26"]},
    {
        'name': "MDD Converter. Meter Timeswitch Class",
        'path': "/general_imports/26",
        'tries': {'max': 10, 'period': 1},
        'status_code': 200,
        'regexes': [r"The file has been imported successfully\."]},

    {
        'name': "MDD Converter. MTC in PES area",
        'path': "/reports/163",
        'method': "post",
        'files': {"file": "test/MTC_in_PES_Area_233.csv"},
        'status_code': 200,
        'regexes':  [
            r'"insert","mtc","26","045","4 rate SToD","False","False","False",'
            r'"TN","CR","4","2015-03-18 00:00",""']},
    {
        'name': "MDD Converter. MTC in PES Area",
        'path': "/general_imports",
        'method': "post",
        'files': {'import_file': "test/gi_insert_mtc_in_pes_area.csv"},
        'status_code': 303,
        'regexes': [
            "/general_imports/27"]},
    {
        'name': "MDD Converter. Meter Timeswitch Class",
        'path': "/general_imports/27",
        'tries': {'max': 10, 'period': 1},
        'status_code': 200,
        'regexes': [r"The file has been imported successfully\."]},

    # CRC Selector
    {
        'name': "CRC Selector",
        'path': "/csv_crc",
        'status_code': 200},

    # Dumb NHH supply with DUoS pass-through
    {
        'name': "Dumb NHH supply with DUoS pass-through: "
        "Update Non half-hourlies 2010",
        'path': "/supplier_contracts/37/edit",
        'method': 'post',
        'data': {
            'party_id': '90',
            'name': 'Non half-hourlies 2010',
            'charge_script': """import chellow.duos

def virtual_bill_titles():
        return ['net-gbp', 'sum-msp-kwh', 'problem']

def virtual_bill(supply_source):
    sum_msp_kwh = sum(h['msp-kwh'] for h in supply_source.hh_data)
    bill = supply_source.supplier_bill
    bill['consumption_info'] = supply_source.consumption_info
    chellow.duos.duos_vb(supply_source)
    for rate_name, rate_set in supply_source.supplier_rate_sets.items():
        if len(rate_set) == 1:
            bill[rate_name] = rate_set.pop()
    bill['net-gbp'] = sum_msp_kwh * 0.1
    bill['sum-msp-kwh'] = sum_msp_kwh
""",
            'properties': '{}'},
        'status_code': 303},
    {
        'name': "Dumb NHH supply with DUoS pass-through: "
        "Run virtual bill",
        'path': '/reports/291?supply_id=16&start_year=2015&start_month=03&'
        'start_day=01&start_hour=00&start_minute=0&finish_year=2015&'
        'finish_month=03&finish_day=31&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"051_FINISHED_watkinsexamplecom_supply_virtual_bills_16\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '051_FINISHED_watkinsexamplecom_supply_virtual_bills_16.csv',
        'regexes': [
            r'Imp MPAN Core,Exp MPAN Core,Site Code,Site Name,'],
        'status_code': 200},

    # Forecast that includes a leap day
    {
        'name': "Leap day forecast. Create scenario",
        'path': '/supplier_contracts/add',
        'method': 'post',
        'data': {
            'participant_id': "54",  # COOP
            'name': "scenario_leap_day",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'charge_script': "",
            'properties': """
{
    'kwh_start': datetime(2009, 4, 1),
    'scenario_start': datetime(2016, 2, 1),  # Date or None for this month
    'scenario_duration': 1,  # Number of months
    'resolution': 'hh',  # 'hh' or 'month'

    'kw_changes':

    # MPAN Core, Date, kW
    '''
    ''',
}
""", },
        'regexes': [
            r"/supplier_contracts/41"],
        'status_code': 303},

    {
        'name': "Leap day forecast. Run scenario for a site",
        'path': '/reports/247?site_id=5&scenario_id=41',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"052_FINISHED_watkinsexamplecom_scenario_leap_day_20160201_0000_"
            r"for_1_months_site_CH023\.ods"]},
    {
        'path': '/downloads/'
        '052_FINISHED_watkinsexamplecom_scenario_leap_day_20160201_0000_'
        'for_1_months_site_CH023.ods',
        'status_code': 200,
        'regexes': [

            r'<table:table-row>\s*'
            r'<table:table-cell office:string-value="22 4862 4512 332" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="amr" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="net" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="1" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="04" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="CH023" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Treglisson" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2016-02-29T23:30:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="23562.049999999996" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="6"/>\s*'
            r'<table:table-cell office:value="23562.049999999996" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="10.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="6"/>\s*'
            r'<table:table-cell office:value="10.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="10" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="81"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="18"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="23562.049999999996" '
            r'office:value-type="float"/>\s*'
            r'</table:table-row>']},

    {
        'name': "Check CSV Supplies HH Data. With mpan_cores",
        'path': '/reports/169',
        'method': 'post',
        'data': {
            'mpan_cores': '22 0470 7514 535\n22 1065 3921 534 ',
            'imp_related': 'true',
            'channel_type': 'ACTIVE',
            'start_year': '2008', 'start_month': '7', 'start_day': '1',
            'start_hour': '0', 'start_minute': '0', 'finish_year': '2008',
            'finish_month': '08', 'finish_day': '1', 'finish_hour': '23',
            'finish_minute': '30'},
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"053_FINISHED_watkinsexamplecom_supplies_hh_data_200808012330_"
            r"filter\.csv"]},
    {
        'path': '/downloads/'
        '053_FINISHED_watkinsexamplecom_supplies_hh_data_200808012330_'
        'filter.csv',
        'status_code': 200,

        # Check the HH data is there
        'regexes': [
            r'NA,2008-07-06,0\.262',
            r"\A\('Connection', 'close'\)\s*"
            r"\('Content-Disposition', 'attachment; "
            r'filename="053_FINISHED_watkinsexamplecom_supplies_hh_data_'
            r'200808012330_filter.csv"'
            r"'\)\s*"
            r"\('Content-Type', 'text/csv; charset=utf-8'\)\s*"
            r"\('Date', '[^']*'\)\s*"
            r"\('Server', '[^']*'\)\s*"
            r"\('Transfer-Encoding', 'chunked'\)\s*"
            r'MPAN Core,Date,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,'
            r'19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,'
            r'40,41,42,43,44,45,46,47\s*'
            r'NA,2008-07-01,*\s*'
            r'NA,2008-07-02,*\s*'
            r'NA,2008-07-03,*\s*'
            r'NA,2008-07-04,*\s*'
            r'NA,2008-07-05,*\s*'
            r'NA,2008-07-06,0.262,,0.252,0.246,0.249,,0.25,0.249,0.244,0.239,'
            r'0.255,0.255,0.286,0.289,0.356,0.489,0.576,0.585,0.496,0.411,'
            r'0.457,0.463,0.436,0.447,0.436,0.431,0.439,0.396,0.455,0.453,'
            r'0.377,0.314,0.341,0.338,0.418,0.45,0.446,0.442,0.464,0.366,'
            r'0.314,0.386,0.395,0.444,0.346,0.288,0.263,0.255\s*'
            r'NA,2008-07-07,*\s*'
            r'NA,2008-07-08,0.299,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,'
            r',,,0.933\s*'
            r'NA,2008-07-09,*\s*'
            r'NA,2008-07-10,*\s*'
            r'NA,2008-07-11,*\s*'
            r'NA,2008-07-12,*\s*'
            r'NA,2008-07-13,*\s*'
            r'NA,2008-07-14,*\s*'
            r'NA,2008-07-15,*\s*'
            r'NA,2008-07-16,*\s*'
            r'NA,2008-07-17,*\s*'
            r'NA,2008-07-18,*\s*'
            r'NA,2008-07-19,*\s*'
            r'NA,2008-07-20,*\s*'
            r'NA,2008-07-21,*\s*'
            r'NA,2008-07-22,*\s*'
            r'NA,2008-07-23,*\s*'
            r'NA,2008-07-24,*\s*'
            r'NA,2008-07-25,*\s*'
            r'NA,2008-07-26,*\s*'
            r'NA,2008-07-27,*\s*'
            r'NA,2008-07-28,*\s*'
            r'NA,2008-07-29,*\s*'
            r'NA,2008-07-30,*\s*'
            r'NA,2008-07-31,*\s*'
            r'NA,2008-08-01,*\s*'
            r'22 1065 3921 534,2008-07-01,']},

    # Insert era with {no change} on channel
    {
        'name': "Insert era with {no change} on channel",
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/era-insert-2.csv'},
        'status_code': 303,
        'regexes': [
            r"/general_imports/28"]},
    {
        'path': '/general_imports/28',
        'tries': {},

        # Check it's loaded ok
        'regexes': [
            r"The file has been imported successfully"],
        'status_code': 200},

    # Supplies TRIAD selector
    {
        'name': "Supplies TRIAD selector",
        'path': '/csv_supplies_triad',
        'status_code': 200,
        'regexes': [
            r"<!DOCTYPE html>"]},

    # Sites TRIAD selector
    {
        'name': "Sites TRIAD selector",
        'path': '/csv_sites_triad',
        'status_code': 200,
        'regexes': [
            r"<!DOCTYPE html>"]},

    # View a MOP bill
    {
        'name': "View a MOP bill",
        'path': '/mop_bills/16',
        'status_code': 200,
        'regexes': [
            r"<!DOCTYPE html>"]},

    # CRC for HH supply with HH data
    {
        'name': "CRC for HH supply with HH data",
        'path': '/reports/207?supply_id=2&year=2005',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"054_FINISHED_watkinsexamplecom_crc_2005_2006_supply_2\.csv"]},
    {
        'path': '/downloads/'
        '054_FINISHED_watkinsexamplecom_crc_2005_2006_supply_2.csv',
        'status_code': 200,
        'regexes': [
            r'"2","22 9813 2107 763"']},

    # CRC for HH supply that straddles eras with missing data
    {
        'name': "CRC for HH supply that straddles eras with missing data",
        'path': '/reports/207?supply_id=7&year=2008',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"055_FINISHED_watkinsexamplecom_crc_2008_2009_supply_7\.csv"]},
    {
        'path': '/downloads/'
        '055_FINISHED_watkinsexamplecom_crc_2008_2009_supply_7.csv',
        'status_code': 200,
        'regexes': [
            r'"7","22 4862 4512 332","CH023","Treglisson","2008-04-01 00:00",'
            r'"2009-03-31 23:30","","0","127.0","0","0","0","365.0","0","0",'
            r'"127.0","365.0","Estimated","0","612952.9400000019","0","0","0",'
            r'"1148683.4623622093","1761636.4023622111",""']},

    {
        'name': "Contract level MOP virtual bills",
        'path': '/reports/231?mop_contract_id=32&start_year=2015&'
        'start_month=04&start_day=01&start_hour=00&start_minute=00&'
        'finish_year=2015&finish_month=04&finish_day=01&finish_hour=23&'
        'finish_minute=30',
        'regexes': [
            r'Import MPAN Core,Export MPAN Core,Start Date,Finish Date,'
            r'net-gbp,problem',

            r',22 0470 7514 535,2015-04-01 00:00,2015-04-01 23:30,"0","",'],
        'status_code': 200},

    {
        'name': "Bank holiday day change without restart. Add HH.",
        'path': '/channels/58/edit',
        'method': 'post',
        'data': {
            'start_year': "2014",
            'start_month': "06",
            'start_day': "04",
            'start_hour': "16",
            'start_minute': "00",
            'insert': "Insert",
            'value': "48.9",
            'status': "A"},
        'status_code': 303},
    {
        'name': "Bank holiday day change without restart. Before change.",
        'path': '/reports/291?supply_id=5&start_year=2014&start_month=6&'
        'start_day=04&start_hour=00&start_minute=0&finish_year=2014&'
        'finish_month=06&finish_day=4&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'name': "Check supplies snapshot at beginning of supply",
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"056_FINISHED_watkinsexamplecom_supply_virtual_bills_5\.csv"],
        'status_code': 200},
    {
        'name': "Check supplies snapshot at beginning of supply",
        'path': '/downloads/'
        '056_FINISHED_watkinsexamplecom_supply_virtual_bills_5.csv',
        'regexes': [
            r'22 0883 6932 301,,CI005,Wheal Rodney,4341,'
            r'2014-06-04 00:00,2014-06-04 23:30,,0,,,0,,,'
            r'116.1360325\d*,,,,,5.89,350,1,0.0269,'
            r'9.415000000000001,,,,,0,0.00147,0.0,,,0.0,'
            r'0,0.25405,12.423045,0.0,0.00399,0.0,1,0.0878,'
            r'0.0878,88,48.9,52.5186,0.00021361,0.011218498146,'
            r'53.02001082\d*,,-0.02242648231\d*,0,0.0,0.0,0,'
            r'0.0,0.0,48.9,52.5186,0.32906054015999997,,,,,'
            r',,,,,53.02001082\d*,,0.00233500127\d*,,,'
            r',,,,,,,,,,,,,,,,,,,,,'
            r',,,,,,,,,,,,,,,,,'
            r'duos-amber-rate,0.00344,duos-red-kwh,48.9'],
        'status_code': 200},
    {
        'name': "Bank holiday day change without restart. Edit the rate "
        "script",
        'path': '/non_core_rate_scripts/10/edit',
        'method': 'post',
        'data': {
            'start_year': "2013",
            'start_month': "01",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00",
            'has_finished': 'true',
            'finish_year': "2013",
            'finish_month': "01",
            'finish_day': "31",
            'finish_hour': "23",
            'finish_minute': "30",
            'script': """{
    "bank_holidays": [
        "2013-01-01",
        "2013-03-29",
        "2013-04-01",
        "2013-05-06",
        "2013-05-27",
        "2013-06-04",
        "2013-08-26",
        "2013-12-25",
        "2013-12-26"
    ]
}
"""}},
    {
        'name': "Bank holiday day change without restart. Check it's "
        "registered the bank holiday",
        'path': '/reports/291?supply_id=5&start_year=2014&start_month=6&'
        'start_day=04&start_hour=00&start_minute=0&finish_year=2014&'
        'finish_month=06&finish_day=4&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"057_FINISHED_watkinsexamplecom_supply_virtual_bills_5\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '057_FINISHED_watkinsexamplecom_supply_virtual_bills_5.csv',
        'regexes': [
            r'22 0883 6932 301,,CI005,Wheal Rodney,4341,'
            r'2014-06-04 00:00,2014-06-04 23:30,,0,,,0,,,'
            r'116.13603255\d*,,,,,5.89,350,1,0.0269,'
            r'9.415000000000001,,,,,0,0.00147,0.0,,,0.0,'
            r'0,0.25405,12.423045,0.0,0.00399,0.0,1,0.0878,'
            r'0.0878,88,48.9,52.5186,0.00021361,0.011218498146,'
            r'53.02001\d*,,-0.02242648231\d*,0,0.0,0.0,'
            r'48.9,52.5186,0.32906054015999997,,,,,,,,,'
            r',,,,53.02001082\d*,,0.002335001\d*,,,,'
            r',,,,,,,,,,,,,,,,,,,,,'
            r',,,,,,,,,,,,,,,,'
            r'duos-amber-rate,0.00344,duos-red-kwh,48.9'],
        'status_code': 200},

    {
        'name': "CRC report for mismatched TPRs",
        'path': '/reports/207?supply_id=10&year=2011',
        'status_code': 303},
    {
        'name': "CRC report for mismatched TPRs",
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"058_FINISHED_watkinsexamplecom_crc_2011_2012_supply_10\.csv"],
        'status_code': 200},
    {
        'name': "CRC report for mismatched TPRs",
        'path': '/downloads/'
        '058_FINISHED_watkinsexamplecom_crc_2011_2012_supply_10.csv',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r'12616.862815884477']},
    {
        'name': "Update a bill",
        'path': '/supplier_bills/21/edit',
        'method': 'post',
        'data': {
            'reference': '3423760010',
            'account': 'SA342376000',
            'issue_year': '2012',
            'issue_month': '02',
            'issue_day': '02',
            'issue_hour': '00',
            'issue_minute': '00',
            'start_year': '2012',
            'start_month': '01',
            'start_day': '05',
            'start_hour': '00',
            'start_minute': '00',
            'finish_year': '2012',
            'finish_month': '01',
            'finish_day': '10',
            'finish_hour': '23',
            'finish_minute': '30',
            'kwh': '10',
            'net': '9.07',
            'vat': '0.21',
            'gross': '0',
            'bill_type_id': '2',
            'breakdown': '{}'},
        'status_code': 303},

    {
        'name': "View edit hh datum",
        'path': '/hh_data/3/edit',
        'status_code': 200},

    {
        'name': "CRC meter change reads",
        'path': '/reads/9/edit',
        'method': 'post',
        'data': {
            'mpan': "22 1065 3921 534",
            'coefficient': "1",
            'msn': "brand new meter",
            'units': "kWh",
            'tpr_id': "1",
            'previous_year': "2011",
            'previous_month': "02",
            'previous_day': "06",
            'previous_hour': "23",
            'previous_minute': "30",
            'previous_value': "0",
            'previous_type_id': "1",
            'present_year': "2011",
            'present_month': "02",
            'present_day': "08",
            'present_hour': "23",
            'present_minute': "30",
            'present_value': "97",
            'present_type_id': "1",
            'update': "Update"},
        'status_code': 303},
    {
        'name': "CRC meter change reads",
        'path': '/reads/10/edit',
        'method': 'post',
        'data': {
            'mpan': "22 1065 3921 534",
            'coefficient': "1",
            'msn': "I02D89150",
            'units': "kWh",
            'tpr_id': "1",
            'previous_year': "2011",
            'previous_month': "02",
            'previous_day': "04",
            'previous_hour': "23",
            'previous_minute': "30",
            'previous_value': "8053",
            'previous_type_id': "1",
            'present_year': "2011",
            'present_month': "02",
            'present_day': "06",
            'present_hour': "23",
            'present_minute': "30",
            'present_value': "8553",
            'present_type_id': "1",
            'update': "Update"},
        'status_code': 303},
    {
        'name': "CRC meter change reads",
        'path': '/reads/16/edit',
        'method': 'post',
        'data': {
            'mpan': "22 1065 3921 534",
            'coefficient': "1",
            'msn': "brand new meter",
            'units': "kWh",
            'tpr_id': "1",
            'previous_year': "2012",
            'previous_month': "01",
            'previous_day': "04",
            'previous_hour': "23",
            'previous_minute': "30",
            'previous_value': "473",
            'previous_type_id': "1",
            'present_year': "2012",
            'present_month': "01",
            'present_day': "06",
            'present_hour': "23",
            'present_minute': "30",
            'present_value': "725",
            'present_type_id': "1",
            'update': "Update"},
        'status_code': 303},

    {
        'name': "CRC meter change reads",
        'path': '/reports/207?supply_id=10&year=2010',
        'status_code': 303},
    {
        'name': "CRC meter change reads",
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"059_FINISHED_watkinsexamplecom_crc_2010_2011_supply_10\.csv"],
        'status_code': 200},
    {
        'name': "CRC meter change reads",
        'path': '/downloads/'
        '059_FINISHED_watkinsexamplecom_crc_2010_2011_supply_10.csv',
        'status_code': 200,
        'regexes': [
            r'73142.39335486847']},

    # Duration report; bill with reads covered by bill without.
    {
        'name': "Bill with reads covered by bill without. Add covered bill.",
        'path': '/supplier_batches/7/add_bill',
        'method': 'post',
        'data': {
            'mpan_core': '22 1065 3921 534',
            'reference': "3423760011",
            'issue_year': "2012",
            'issue_month': "03",
            'issue_day': "02",
            'issue_hour': "00",
            'issue_minute': "00",
            'start_year': "2012",
            'start_month': "01",
            'start_day': "05",
            'start_hour': "00",
            'start_minute': "00",
            'finish_year': "2012",
            'finish_month': "01",
            'finish_day': "10",
            'finish_hour': "23",
            'finish_minute': "30",
            'kwh': "0",
            'net': "45.7",
            'vat': "4.90",
            'gross': "50.60",
            'account': "SA342376000",
            'bill_type_id': "2",
            'breakdown': "{}"},
        'regexes': [
            r"/supplier_bills/22"],
        'status_code': 303},
    {
        'name': "Reads covered by bill without. Run supplies duration.",
        'path': '/reports/149?supply_id=10&start_year=2012&start_month=01&'
        'start_day=05&start_hour=00&start_minute=00&finish_year=2012&'
        'finish_month=01&finish_day=10&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"060_FINISHED_watkinsexamplecom_supplies_duration\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '060_FINISHED_watkinsexamplecom_supplies_duration.csv',
        'regexes': [
            r'"10","2","net","","CI017","Roselands","2012-01-05 00:00",'
            r'"2012-01-10 23:30","03","801","6a","0366","1","nhh",110,'
            r'22 1065 3921 534,30,Non half-hourlies 2010,0,0,,0,,None,288,,,,,'
            r'0,0,,0,,None,288'],
        'status_code': 200},
    {
        'name': "Reads covered by bill without. Run bill check.",
        'path': '/reports/111?bill_id=21',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"061_FINISHED_watkinsexamplecom_bill_check\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '061_FINISHED_watkinsexamplecom_bill_check.csv',
        'regexes': [
            r'07-002,3423760010,N,10,9.07,0.21,2012-01-05 00:00,'
            r'2012-01-10 23:30,22 1065 3921 534,CI017,Roselands,'
            r'2012-01-05 00:00,2012-01-10 23:30,22;21,756.0,54.77,'
            r'25.200000000000003,29.57,10.0,252.0,,'],
        'status_code': 200},

    {
        'name': "Reads attached to withdrawn bill.",
        'path': '/reports/149?supply_id=10&start_year=2007&start_month=02&'
        'start_day=01&start_hour=00&start_minute=00&finish_year=2007&'
        'finish_month=02&finish_day=28&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"062_FINISHED_watkinsexamplecom_supplies_duration\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '062_FINISHED_watkinsexamplecom_supplies_duration.csv',
        'regexes': [
            r'"10","2","net","","CI017","Roselands","2007-02-01 00:00",'
            r'"2007-02-28 23:30","03","801","5","0393","0","nhh",'
            r'110,22 1065 3921 534,30,Non half-hourlies 2010,0,0,,0,,None,'
            r'1344,,,,,0,0,,0,,None,1344'],
        'status_code': 200},

    {
        'name': "Supplies duration normal reads with prev, pres the same.",
        'path': '/reads/11/edit',
        'method': 'post',
        'data': {
            'mpan': "2210653921534",
            'coefficient': "1",
            'msn': "I02D89150",
            'units': "kWh",
            'tpr_id': "1",
            'previous_year': "2007",
            'previous_month': "01",
            'previous_day': "04",
            'previous_hour': "00",
            'previous_minute': "00",
            'previous_value': "38992",
            'previous_type_id': "4",
            'present_year': "2009",
            'present_month': "04",
            'present_day': "04",
            'present_hour': "23",
            'present_minute': "30",
            'present_value': "14281",
            'present_type_id': "1",
            'update': "Update"},
        'status_code': 303},
    {
        'name': "Supplies duration normal reads with prev, pres the same.",
        'path': '/reports/149?supply_id=10&start_year=2009&start_month=04&'
        'start_day=01&start_hour=00&start_minute=00&finish_year=2009&'
        'finish_month=04&finish_day=10&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'name': "Supplies duration normal reads with prev, pres the same.",
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"063_FINISHED_watkinsexamplecom_supplies_duration\.csv"],
        'status_code': 200},
    {
        'name': "Supplies duration normal reads with prev, pres the same.",
        'path': '/downloads/'
        '063_FINISHED_watkinsexamplecom_supplies_duration.csv',
        'regexes': [
            r'"10","2","net","","CI017","Roselands","2009-04-01 00:00",'
            r'"2009-04-10 23:30","03","801","5","0393","1","nhh",'
            r'110,22 1065 3921 534,30,Non half-hourlies 2010,0,0,,0,,None,480,'
            r',,,,0,0,,0,,None,480'],
        'status_code': 200},

    {
        'name': "Group starting after report period.",
        'path': '/reports/389?site_id=3&months=1&finish_year=2003&'
        'finish_month=08',
        'regexes': [
            r'"CI005","Wheal Rodney","CI004","2003-08-03 00:00",'
            r'"2003-08-31 23:30","chp chp","","","","","0.0","","0.0","",'
            r'"0.00525288","","0.0","0","0.0","0","0.0","","0.0","","0.0",'
            r'"0.0","0","0.0","0.0","0","0.0","0.0","0","","","0.0","0","",'
            r'"0.0","0","","0.0","0","","aahedc-gbp","0.0","aahedc-gsp-kwh",'
            r'"0.0","aahedc-msp-kwh","0","aahedc-rate","0.00016456",'
            r'"duos-reactive-rate","0.0023","problem","",'
            r'"triad-estimate-1-date","2002-11-25 17:00",'
            r'"triad-estimate-1-gsp-kw","0.0","triad-estimate-1-laf","1.087",'
            r'"triad-estimate-1-msp-kw","0","triad-estimate-1-status","E",'
            r'"triad-estimate-2-date","2002-12-06 17:00",'
            r'"triad-estimate-2-gsp-kw","0.0","triad-estimate-2-laf","1.074",'
            r'"triad-estimate-2-msp-kw","0","triad-estimate-2-status","E",'
            r'"triad-estimate-3-date","2003-01-30 17:00",'
            r'"triad-estimate-3-gsp-kw","0.0","triad-estimate-3-laf","1.087",'
            r'"triad-estimate-3-msp-kw","0","triad-estimate-3-status","E",'
            r'"triad-estimate-gbp","0.0","triad-estimate-gsp-kw","0.0",'
            r'"triad-estimate-months","1","triad-estimate-rate","23.77056"'],
        'status_code': 200},

    {
        'name': "Displaced bills for a contract",
        'path': '/reports/109?supplier_contract_id=33&months=1&'
        'finish_year=2005&finish_month=11',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"064_FINISHED_watkinsexamplecom_displaced\.csv"]},
    {
        'path': '/downloads/064_FINISHED_watkinsexamplecom_displaced.csv',
        'status_code': 200,
        'regexes': [
            r'CI005,Wheal Rodney,CI004,2005-11-01 00:00,'
            r'2005-11-30 23:30,']},

    # Scenario runner with default scenario
    {
        'name': "Scenario runner with default scenario",
        'path': '/reports/247?site_id=5&months=1&finish_year=2015&'
        'finish_month=2',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"065_FINISHED_watkinsexamplecom_unified_supplies_monthly_"
            r"duration_20150201_0000_for_1_months_site_CH023\.ods"]
        },

    {
        'path': '/downloads/'
        '065_FINISHED_watkinsexamplecom_unified_supplies_monthly_'
        'duration_20150201_0000_for_1_months_site_CH023.ods',
        'status_code': 200,
        'regexes': [
            r"22 4862 4512 332"]},

    {
        'name': "CRC meter change reads",
        'path': '/reads/9/edit',
        'method': 'post',
        'data': {
            'mpan': "22 1065 3921 534",
            'coefficient': "1",
            'msn': "brand new meter",
            'units': "kWh",
            'tpr_id': "1",
            'previous_year': "2011",
            'previous_month': "02",
            'previous_day': "06",
            'previous_hour': "23",
            'previous_minute': "30",
            'previous_value': "0",
            'previous_type_id': "1",
            'present_year': "2011",
            'present_month': "02",
            'present_day': "08",
            'present_hour': "23",
            'present_minute': "30",
            'present_value': "97",
            'present_type_id': "1",
            'update': "Update"},
        'status_code': 303},
    {
        'name': "CRC meter change reads",
        'path': '/reads/10/edit',
        'method': 'post',
        'data': {
            'mpan': "22 1065 3921 534",
            'coefficient': "1",
            'msn': "I02D89150",
            'units': "kWh",
            'tpr_id': "1",
            'previous_year': "2011",
            'previous_month': "02",
            'previous_day': "04",
            'previous_hour': "23",
            'previous_minute': "30",
            'previous_value': "8053",
            'previous_type_id': "1",
            'present_year': "2011",
            'present_month': "02",
            'present_day': "06",
            'present_hour': "23",
            'present_minute': "30",
            'present_value': "8553",
            'present_type_id': "1",
            'update': "Update"},
        'status_code': 303},
    {
        'name': "CRC meter change reads",
        'path': '/reads/16/edit',
        'method': 'post',
        'data': {
            'mpan': "22 1065 3921 534",
            'coefficient': "1",
            'msn': "brand new meter",
            'units': "kWh",
            'tpr_id': "1",
            'previous_year': "2012",
            'previous_month': "01",
            'previous_day': "04",
            'previous_hour': "23",
            'previous_minute': "30",
            'previous_value': "473",
            'previous_type_id': "1",
            'present_year': "2012",
            'present_month': "01",
            'present_day': "06",
            'present_hour': "23",
            'present_minute': "30",
            'present_value': "725",
            'present_type_id': "1",
            'update': "Update"},
        'status_code': 303},
    {
        'name': "CRC meter change reads",
        'path': '/reports/207?supply_id=10&year=2010',
        'status_code': 303},
    {
        'name': "CRC meter change reads",
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"066_FINISHED_watkinsexamplecom_crc_2010_2011_supply_10\.csv"],
        'status_code': 200},
    {
        'name': "CRC meter change reads",
        'path': '/downloads/'
        '066_FINISHED_watkinsexamplecom_crc_2010_2011_supply_10.csv',
        'status_code': 200,
        'regexes': [
            r'73142.39335486847']},

    # See if unified report shows billed amounts correctly
    {
        'name': "Unified Supplies Monthly Duration - billed amounts",
        'path': '/reports/247?supply_id=10&months=1&finish_year=2010&'
        'finish_month=01',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"067_FINISHED_watkinsexamplecom_unified_supplies_monthly_"
            r"duration_20100101_0000_for_1_months_supply_10\.ods"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '067_FINISHED_watkinsexamplecom_unified_supplies_monthly_'
        'duration_20100101_0000_for_1_months_supply_10.ods',
        'status_code': 200,
        'regexes': [
            r'<table:table-row>\s*'
            r'<table:table-cell office:string-value="imp-mpan-core" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="exp-mpan-core" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="metering-type" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="source" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="generator-type" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="supply-name" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="msn" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="pc" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="site-id" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="site-name" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="associated-site-ids" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="month" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="import-net-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="export-net-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="import-gen-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="export-gen-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="import-3rd-party-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="export-3rd-party-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="displaced-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="used-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="used-3rd-party-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="import-net-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="export-net-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="import-gen-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="export-gen-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="import-3rd-party-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="export-3rd-party-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="displaced-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="used-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="used-3rd-party-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="billed-import-net-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="billed-import-net-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="mop-net-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="mop-problem" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="dc-net-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="dc-problem" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-net-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-sum-msp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-problem" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'</table:table-row>',

            r'<table:table-row>\s*'
            r'<table:table-cell office:string-value="22 1065 3921 534" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="nhh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="net" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="2" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="I02D89150" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="03" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="CI017" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Roselands" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2010-01-31T23:30:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="5886.085064894785" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="6"/>\s*'
            r'<table:table-cell office:value="5886.085064894785" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="605.6085064894786" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="6"/>\s*'
            r'<table:table-cell office:value="605.6085064894786" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="150.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="98.17" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="10" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="7" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="588.6085064894786" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="5886.085064894785" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'</table:table-row>']},

    # Supplier contract 66
    {
        'name': "3rd party in unified report. Make 3rd-party-reverse.",
        'path': '/supplies/16/edit',
        'method': 'post',
        'data': {
            'name': "3",
            'source_id': "6",
            'generator_type_id': "1",
            'gsp_group_id': "3"},
        'status_code': 303},
    {
        'name': "3rd party in unified report.",
        'path': '/supplier_batches/7/add_bill',
        'method': 'post',
        'data': {
            'mpan_core': "22 9789 0534 938",
            'reference': "3Pb",
            'issue_year': "2014",
            'issue_month': "01",
            'issue_day': "06",
            'issue_hour': "00",
            'issue_minute': "00",
            'start_year': "2014",
            'start_month': "12",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00",
            'finish_year': "2014",
            'finish_month': "12",
            'finish_day': "31",
            'finish_hour': "23",
            'finish_minute': "30",
            'kwh': "10",
            'net': "2",
            'vat': "0.5",
            'gross': "2.5",
            'account': "taa2",
            'bill_type_id': "1",
            'breakdown': "{}"},
        'regexes': [
            r"/supplier_bills/23"],
        'status_code': 303},
    {
        'name': "3rd party in unified report.",
        'path': '/supplier_bills/23/add_read',
        'method': 'post',
        'data': {
            'mpan': "03 801 111 22 9789 0534 938",
            'coefficient': "1",
            'msn': "",
            'units': "kWh",
            'tpr_id': "1",
            'previous_year': "2014",
            'previous_month': "12",
            'previous_day': "01",
            'previous_hour': "00",
            'previous_minute': "00",
            'previous_value': "0",
            'previous_type_id': "1",
            'present_year': "2014",
            'present_month': "12",
            'present_day': "31",
            'present_hour': "23",
            'present_minute': "30",
            'present_value': "100",
            'present_type_id': "1"},
        'regexes': [
            r"/supplier_bills/23"],
        'status_code': 303},
    {
        'name': "3rd party in unified report.",
        'path': '/supplier_bills/23',
        'regexes': [
            r"/reads/17"],
        'status_code': 200},
    {
        'name': "3rd party in unified report.",
        'path': '/reports/247?supply_id=16&months=1&finish_year=2014&'
        'finish_month=12',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r'068_FINISHED_watkinsexamplecom_unified_supplies_monthly_'
            r'duration_20141201_0000_for_1_months_supply_16\.ods'],
        'status_code': 200},
    {
        'path': '/downloads/'
        '068_FINISHED_watkinsexamplecom_unified_supplies_monthly_'
        'duration_20141201_0000_for_1_months_supply_16.ods',
        'status_code': 200,
        'regexes': [
            r'<table:table table:name="Supply Level">\s*'
            r'<table:table-column/>\s*'
            r'<table:table-row>\s*'
            r'<table:table-cell office:string-value="imp-mpan-core" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="exp-mpan-core" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="metering-type" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="source" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="generator-type" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="supply-name" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="msn" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="pc" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="site-id" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="site-name" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="associated-site-ids" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="month" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="import-net-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="export-net-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="import-gen-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="export-gen-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="import-3rd-party-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="export-3rd-party-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="displaced-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="used-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="used-3rd-party-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="import-net-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="export-net-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="import-gen-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="export-gen-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="import-3rd-party-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="export-3rd-party-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="displaced-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="used-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="used-3rd-party-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="billed-import-net-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="billed-import-net-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="4"/>\s*'
            r'</table:table-row>\s*'
            r'<table:table-row>\s*'
            r'<table:table-cell office:string-value="22 '
            r'9789 0534 938" office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="nhh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="3rd-party-reverse" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="3" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="03" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="CI017" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Roselands" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:date-value="2014-12-31T23:30:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="5"/>\s*'
            r'<table:table-cell office:value="100.06724949562901" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="-100.06724949562901" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="5"/>\s*'
            r'<table:table-cell office:value="10" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="10.006724949562901" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="-0.006724949562901372" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="10.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="2.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="3"/>\s*'
            r'</table:table-row>\s*'
            r'</table:table>']},

    {
        'name': "Dumb NHH supply with DUoS pass-through: "
        "Update Non half-hourlies 2010",
        'path': "/supplier_contracts/37/edit",
        'method': 'post',
        'data': {
            'party_id': '90',
            'name': 'Non half-hourlies 2010',
            'charge_script': """import chellow.duos

def virtual_bill_titles():
    return ['net-gbp', 'sum-msp-kwh', 'problem']

def virtual_bill(supply_source):
    sum_msp_kwh = sum(h['msp-kwh'] for h in supply_source.hh_data)
    bill = supply_source.supplier_bill
    chellow.duos.duos_vb(supply_source)
    for rate_name, rate_set in supply_source.supplier_rate_sets.items():
        if len(rate_set) == 1:
            bill[rate_name] = rate_set.pop()
    bill['net-gbp'] += sum_msp_kwh * 0.1
    bill['sum-msp-kwh'] += sum_msp_kwh
""",
            'properties': '{}'},
        'status_code': 303},
    {
        'name': "Dumb NHH supply with DUoS pass-through: "
        "Run virtual bill",
        'path': '/reports/291?supply_id=16&start_year=2015&start_month=03&'
        'start_day=01&start_hour=00&start_minute=0&finish_year=2015&'
        'finish_month=03&finish_day=31&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"069_FINISHED_watkinsexamplecom_supply_virtual_bills_16\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '069_FINISHED_watkinsexamplecom_supply_virtual_bills_16.csv',
        'regexes': [
            r'Imp MPAN Core,Exp MPAN Core,Site Code,Site Name,'],
        'status_code': 200},

    {
        'name': "Update a bill",
        'path': '/supplier_bills/21/edit',
        'method': 'post',
        'data': {
            'reference': '3423760010',
            'account': 'SA342376000',
            'issue_year': '2012',
            'issue_month': '02',
            'issue_day': '02',
            'issue_hour': '00',
            'issue_minute': '00',
            'start_year': '2012',
            'start_month': '01',
            'start_day': '05',
            'start_hour': '00',
            'start_minute': '00',
            'finish_year': '2012',
            'finish_month': '01',
            'finish_day': '10',
            'finish_hour': '23',
            'finish_minute': '30',
            'kwh': '10',
            'net': '9.07',
            'vat': '0.21',
            'gross': '0',
            'bill_type_id': '2',
            'breakdown': '{}'},
        'status_code': 303},


    {
        'name': "Unified report for a gen-net supply",
        'path': '/supplies/5/edit',
        'method': 'post',
        'data': {
            'name': "Hello",
            'source_id': "3",
            'generator_type_id': "1",
            'gsp_group_id': "11"},
        'status_code': 303},
    {
        'name': "Unified report for a gen-net supply",
        'path': '/reports/247?supply_id=5&months=1&finish_year=2015&'
        'finish_month=05',
        'status_code': 303},
    {
        'name': "Unified report for a gen-net supply",
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r'070_FINISHED_watkinsexamplecom_unified_supplies_monthly_'
            r'duration_20150501_0000_for_1_months_supply_5\.ods'],
        'status_code': 200},
    {
        'name': "Unified report for a gen-net supply",
        'path': '/downloads/'
        '070_FINISHED_watkinsexamplecom_unified_supplies_monthly_'
        'duration_20150501_0000_for_1_months_supply_5.ods',
        'status_code': 200,
        'regexes': [
            r'chp']},

    {
        'name': "Supplies duration normal reads with prev, pres the same.",
        'path': '/reads/11/edit',
        'method': 'post',
        'data': {
            'mpan': "2210653921534",
            'coefficient': "1",
            'msn': "I02D89150",
            'units': "kWh",
            'tpr_id': "1",
            'previous_year': "2007",
            'previous_month': "01",
            'previous_day': "04",
            'previous_hour': "00",
            'previous_minute': "00",
            'previous_value': "38992",
            'previous_type_id': "4",
            'present_year': "2009",
            'present_month': "04",
            'present_day': "04",
            'present_hour': "23",
            'present_minute': "30",
            'present_value': "14281",
            'present_type_id': "1",
            'update': "Update"},
        'status_code': 303},
    {
        'name': "Supplies duration normal reads with prev, pres the same.",
        'path': '/reports/149?supply_id=10&start_year=2009&start_month=04&'
        'start_day=01&start_hour=00&start_minute=00&finish_year=2009&'
        'finish_month=04&finish_day=10&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'name': "Supplies duration normal reads with prev, pres the same.",
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"071_FINISHED_watkinsexamplecom_supplies_duration\.csv"],
        'status_code': 200},
    {
        'name': "Supplies duration normal reads with prev, pres the same.",
        'path': '/downloads/'
        '071_FINISHED_watkinsexamplecom_supplies_duration.csv',
        'regexes': [
            r'"10","2","net","","CI017","Roselands","2009-04-01 00:00",'
            r'"2009-04-10 23:30","03","801","5","0393","1","nhh",'
            r'110,22 1065 3921 534,30,Non half-hourlies 2010,0,0,,0,,None,480,'
            r',,,,0,0,,0,,None,480'],
        'status_code': 200},

    {
        'name': "Unified Supplies Monthly Duration - displaced kWh",
        'path': '/channels/10/edit',
        'method': 'post',
        'data': {
            'start_year': "2015",
            'start_month': "05",
            'start_day': "04",
            'start_hour': "20",
            'start_minute': "00",
            'insert': "Insert",
            'value': "45",
            'status': "A", },
        'status_code': 303},
    {
        'name': "Unified Supplies Monthly Duration - displaced kWh",
        'path': '/reports/247?site_id=3&months=1&finish_year=2015&'
        'finish_month=05',
        'status_code': 303},
    {
        'name': "Unified Supplies Monthly Duration - displaced kWh",
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'regexes': [
            r'072_FINISHED_watkinsexamplecom_unified_supplies_monthly_'
            r'duration_20150501_0000_for_1_months_site_CI005\.ods'],
        'status_code': 200},
    {
        'name': "Unified Supplies Monthly Duration - displaced kWh",
        'path': '/downloads/'
        '072_FINISHED_watkinsexamplecom_unified_supplies_monthly_'
        'duration_20150501_0000_for_1_months_site_CI005.ods',
        'status_code': 200,
        'regexes': [
            r'-45']},

    {
        'name': "Unified supply starts after period",
        'path': '/reports/247?supply_id=7&months=1&finish_year=2003&'
        'finish_month=08',
        'status_code': 303},
    {
        'name': "Unified supply starts after period",
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'regexes': [
            r'073_FINISHED_watkinsexamplecom_unified_supplies_monthly_'
            r'duration_20030801_0000_for_1_months_supply_7\.ods'],
        'status_code': 200},
    {
        'name': "Unified supply starts after period",
        'path': '/downloads/'
        '073_FINISHED_watkinsexamplecom_unified_supplies_monthly_'
        'duration_20030801_0000_for_1_months_supply_7.ods',
        'status_code': 200,
        'regexes': [
            r'22 4862 4512 332']},

    {
        'name': "Monthly sites duration: multiple site groups",
        'path': '/reports/161?site_id=3&months=1&finish_year=2010&'
        'finish_month=04',
        'status_code': 303},
    {
        'name': "Monthly sites duration: multiple site groups",
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'regexes': [
            r'074_FINISHED_watkinsexamplecom_site_monthly_duration_for_CI005_'
            r'1_to_2010_4\.csv'],
        'status_code': 200},
    {
        'name': "Monthly sites duration: multiple site groups",
        'path': '/downloads/'
        '074_FINISHED_watkinsexamplecom_site_monthly_duration_for_CI005_'
        '1_to_2010_4.csv',
        'status_code': 200,
        'regexes': [
            r'"CI005","Wheal Rodney","CI004","gen,gen-net,net","chp",'
            r'"2010-04-30 23:30","10.8797\d*","0","0","10.8797\d*","0","0",'
            r'"0","0","2606.8380000\d*","0.0","0","2606.838000\d*","0",'
            r'"0","0","hh",""']},

    {
        'name': "Monthly sites duration: non-primary site",
        'path': '/reports/161?site_id=1&months=1&finish_year=2015&'
        'finish_month=07',
        'status_code': 303},
    {
        'name': "Monthly sites duration: non-primary site",
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'regexes': [
            r'075_FINISHED_watkinsexamplecom_site_monthly_duration_for_CI004_'
            r'1_to_2015_7\.csv'],
        'status_code': 200},
    {
        'name': "Monthly sites duration: multiple site groups",
        'path': '/downloads/'
        '075_FINISHED_watkinsexamplecom_site_monthly_duration_for_CI004_'
        '1_to_2015_7.csv',
        'status_code': 200,
        'regexes': [
            r'"CI004","Lower Treave","CI005","gen,gen-net,net","chp",'
            r'"2015-07-31 23:30","0","0","0","0","0","0","0","0","0","0","0",'
            r'"0","0","0","0","hh",""']},

    {
        'name': "Metered report: correct MOP / DC costs",
        'path': '/eras/3/edit',
        'method': 'post',
        'data': {
            'start_year': "2003",
            'start_month': "08",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'is_ended': "false",
            'mop_contract_id': "32",
            'mop_account': "mc-22 7907 4116 080",
            'hhdc_contract_id': "30",
            'hhdc_account': "01",
            'msn': "",
            'pc_id': "9",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'exp_llfc_code': "581",
            'exp_mpan_core': "22 7907 4116 080",
            'exp_sc': "600",
            'exp_supplier_contract_id': "31",
            'exp_supplier_account': ""},
        'status_code': 303},
    {
        'name': "Metered report: correct MOP / DC costs",
        'path': '/reports/161?site_id=3&months=1&finish_year=2015&'
        'finish_month=07',
        'status_code': 303},
    {
        'name': "Metered report: correct MOP / DC costs",
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'regexes': [
            r'076_FINISHED_watkinsexamplecom_site_monthly_duration_for_CI005_'
            r'1_to_2015_7\.csv'],
        'status_code': 200},
    {
        'name': "Monthly sites duration: multiple site groups",
        'path': '/downloads/'
        '076_FINISHED_watkinsexamplecom_site_monthly_duration_for_CI005_'
        '1_to_2015_7.csv',
        'status_code': 200,
        'regexes': [
            r'"CI005","Wheal Rodney","CI004","gen,gen-net,net","chp",'
            r'"2015-07-31 23:30","25.819178082191478","0","0",'
            r'"25.819178082191478","0","0","0","0","1114.2003000000002","0.0",'
            r'"0","1114.2003000000002","0","0","0","hh",""']},

    {
        'name': "Unified report, billed: add batch to Dynamat contract",
        'path': '/hhdc_contracts/30/add_batch',
        'method': 'post',
        'data': {
            'reference': "Zathustra",
            'description': "Thus spoke."},
        'status_code': 303,
        'regexes': [
            r"/hhdc_batches/15"]},
    {
        'name': "Unified report, billed: add bill to batch",
        'path': '/hhdc_batches/15/add_bill',
        'method': 'post',
        'data': {
            'mpan_core': '22 7907 4116 080',
            'reference': '001',
            'issue_year': '2015',
            'issue_month': '09',
            'issue_day': '02',
            'issue_hour': '10',
            'issue_minute': '00',
            'start_year': '2015',
            'start_month': '08',
            'start_day': '01',
            'start_hour': '00',
            'start_minute': '00',
            'finish_year': '2015',
            'finish_month': '08',
            'finish_day': '31',
            'finish_hour': '23',
            'finish_minute': '30',
            'kwh': '0',
            'net': '11.20',
            'vat': '3.05',
            'gross': '14.25',
            'account': '22 7907 4116 080',
            'bill_type_id': '2',
            'breakdown': '{}'},
        'status_code': 303,
        'regexes': [
            r"/hhdc_bills/24"]},
    {
        'name': "Unified report, billed",
        'path': '/reports/247?site_id=3&months=1&finish_year=2015&'
        'finish_month=08',
        'status_code': 303},
    {
        'name': "Unified report, billed",
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'regexes': [
            r'077_FINISHED_watkinsexamplecom_unified_supplies_monthly_'
            r'duration_20150801_0000_for_1_months_site_CI005\.ods'],
        'status_code': 200},
    {
        'name': "Unified report, billed",
        'path': '/downloads/'
        '077_FINISHED_watkinsexamplecom_unified_supplies_monthly_'
        'duration_20150801_0000_for_1_months_site_CI005.ods',
        'status_code': 200,
        'regexes': [
            r'<table:table-row>'
            r'<table:table-cell/>'
            r'<table:table-cell office:string-value="22 7907 4116 080" '
            r'office:value-type="string"/>'
            r'<table:table-cell office:string-value="hh" '
            r'office:value-type="string"/>'
            r'<table:table-cell office:string-value="gen" '
            r'office:value-type="string"/>'
            r'<table:table-cell office:string-value="chp" '
            r'office:value-type="string"/>'
            r'<table:table-cell office:string-value="2" '
            r'office:value-type="string"/>'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>'
            r'<table:table-cell office:string-value="00" '
            r'office:value-type="string"/>'
            r'<table:table-cell office:string-value="CI005" '
            r'office:value-type="string"/>'
            r'<table:table-cell office:string-value="Wheal Rodney" '
            r'office:value-type="string"/>'
            r'<table:table-cell office:string-value="CI004" '
            r'office:value-type="string"/>'
            r'<table:table-cell office:date-value="2015-08-31T23:30:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="9"/>\s*'
            r'<table:table-cell office:value="17" office:value-type="float"/>'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="6"/>\s*'
            r'<table:table-cell office:value="17" office:value-type="float"/>'
            r'<table:table-cell office:value="0" office:value-type="float"/>'
            r'<table:table-cell office:value="0.0" office:value-type="float"/>'
            r'<table:table-cell office:value="11.2" '
            r'office:value-type="float"/>'
            r'<table:table-cell/>'
            r'<table:table-cell office:value="10" office:value-type="float"/>'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>'
            r'<table:table-cell/>'
            r'<table:table-cell office:value="7" office:value-type="float"/>'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>'
            r'<table:table-cell table:number-columns-repeated="106"/>\s*'
            r'<table:table-cell office:value="93.89" '
            r'office:value-type="float"/>'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.00525288" '
            r'office:value-type="float"/>'
            r'<table:table-cell/>'
            r'<table:table-cell office:value="5.89" '
            r'office:value-type="float"/>'
            r'<table:table-cell office:value="600" office:value-type="float"/>'
            r'<table:table-cell office:value="31" office:value-type="float"/>'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell office:value="31" office:value-type="float"/>'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell table:number-columns-repeated="4"/>\s*'
            r'<table:table-cell office:value="0.00151" '
            r'office:value-type="float"/>'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>'
            r'<table:table-cell/>'
            r'<table:table-cell office:value="88" office:value-type="float"/>'
            r'<table:table-cell office:value="0" office:value-type="float"/>'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float"/>'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float"/>'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float"/>'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float"/>'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell/>'
            r'<table:table-cell office:value="0.0" office:value-type="float"/>'
            r'<table:table-cell table:number-columns-repeated="18"/>\s*'
            r'<table:table-cell office:date-value="2014-11-25T17:00:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>'
            r'<table:table-cell office:value="0" office:value-type="float"/>'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>'
            r'<table:table-cell office:value="1.087" '
            r'office:value-type="float"/>'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>'
            r'<table:table-cell office:date-value="2014-12-06T17:00:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>'
            r'<table:table-cell office:value="0" office:value-type="float"/>'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>'
            r'<table:table-cell office:value="1.074" '
            r'office:value-type="float"/>'
            r'<table:table-cell office:value="0.0" office:value-type="float"/>'
            r'<table:table-cell office:date-value="2015-01-30T17:00:00" '
            r'office:value-type="date" table:style-name="cDateISO"/>'
            r'<table:table-cell office:value="0" office:value-type="float"/>'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>'
            r'<table:table-cell office:value="1.087" '
            r'office:value-type="float"/>'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>']},

    {
        'name': "Displaying bill raw lines",
        'path': '/supplier_bills/11',
        'regexes': [
            r"Customer Name,",
            r'triad-estimate'],
        'status_code': 200},

    {
        'name': "Error when adding pre-existing MPAN core, to era",
        'path': '/eras/28/edit',
        'method': 'post',
        'data': {
            'start_year': "2014",
            'start_month': "01",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00",
            'mop_contract_id': "32",
            'mop_account': "22 0883 6932 301",
            'hhdc_contract_id': "29",
            'hhdc_account': "22 0883 6932 301",
            'msn': "",
            'pc_id': "9",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'imp_llfc_code': "510",
            'imp_mpan_core': "22 0883 6932 301",
            'imp_sc': "350",
            'imp_supplier_contract_id': "33",
            'imp_supplier_account': "4341",
            'exp_llfc_code': "521",
            'exp_mpan_core': "22 6158 2968 220",
            'exp_sc': "20",
            'exp_supplier_contract_id': "33",
            'exp_supplier_account': "5bb8"},
        'status_code': 400},
    {
        'name': "General Importer: Deleting an era",
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/gi_delete_era.csv'},
        'status_code': 303,
        'regexes': [
            r"/general_imports/29"]},
    {
        'path': '/general_imports/29',
        'tries': {'max': 10, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"The file has been imported successfully\."]},

    {
        'name': "TRIAD, no historical data, but eras exist",
        'path': '/eras/28/edit',
        'method': 'post',
        'data': {
            'start_year': "2014",
            'start_month': "01",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00",
            'is_ended': "false",
            'mop_contract_id': "32",
            'mop_account': "22 0883 6932 301",
            'hhdc_contract_id': "29",
            'hhdc_account': "22 0883 6932 301",
            'msn': "",
            'pc_id': "9",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'imp_llfc_code': "570",
            'imp_mpan_core': "22 0883 6932 301",
            'imp_sc': "350",
            'imp_supplier_contract_id': "33",
            'imp_supplier_account': "413",
            'exp_llfc_code': "581",
            'exp_mpan_core': "22 7824 9120 097",
            'exp_sc': "150",
            'exp_supplier_contract_id': "33",
            'exp_supplier_account': "669"},
        'status_code': 303},
    {
        'name': "TRIAD, no historical data, but eras exist",
        'path': '/reports/291?supply_id=5&start_year=2014&start_month=01&'
        'start_day=01&start_hour=00&start_minute=0&finish_year=2014&'
        'finish_month=01&finish_day=31&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"078_FINISHED_watkinsexamplecom_supply_virtual_bills_5\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '078_FINISHED_watkinsexamplecom_supply_virtual_bills_5.csv',
        'regexes': [r'22 7824 9120 097'],
        'status_code': 200},

    {
        'name': "Supply level virtual bill, with readfull bill covered "
        "by readless bill",
        'path': '/reports/291?supply_id=10&start_year=2012&start_month=01&'
        'start_day=01&start_hour=00&start_minute=0&finish_year=2012&'
        'finish_month=01&finish_day=31&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"079_FINISHED_watkinsexamplecom_supply_virtual_bills_10\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '079_FINISHED_watkinsexamplecom_supply_virtual_bills_10.csv',
        'regexes': [
            r'3409.15883838'],
        'status_code': 200},

    {
        'name': "Test displaced virtual bill with generation",
        'path': '/reports/389?site_id=3&months=1&finish_year=2005&'
        'finish_month=11',
        'regexes': [
            r'"CI005"']},

    {
        'name': "GSP Groups",
        'path': '/gsp_groups',
        'status_code': 200},

    {
        'name': 'Wildcard user. Add config.',
        'path': '/non_core_contracts/5/edit',
        'method': 'post',
        'data': {
            'name': "configuration",
            'properties': """
{
    'ips': {'*.*.*.*': 'watkins@example.com'},
    'site_links': [
        {'name': 'Google Maps', 'href': 'https://maps.google.com/maps?q='}],
    'batch_reports': [1],
    'elexonportal_scripting_key': 'xxx',
    'ecoes': {
        'user_name': 'a',
        'password': 'a',
        'prefix': 'http://localhost:8080/ecoes/'},
    'background_colour': 'aquamarine'}
""", },
        'status_code': 303},
    {
        'name': "Test that we can change the role",
        'path': '/users/2',
        'method': 'post',
        'data': {
            'email_address': "watkins@example.com",
            'user_role_code': "viewer"},
        'status_code': 303},
    {
        'name': 'Wildcard user. Try viewing a page as unknown person',
        'path': '/gsp_groups',
        'auth': None,
        'status_code': 200},
    {
        'name': "Wildcard user. Check 401 still occurs.",
        'path': '/sites/8/edit',
        'method': 'post',
        'data': {
            'site_name': "Ishmael",
            'code': "MOBY",
            'update': "Update"},
        'status_code': 401},

    {
        'name': "Update a local report",
        'path': '/local_reports/1',
        'auth': ('admin@example.com', 'admin'),
        'method': 'post',
        'data': {
            'name': 'Minority Report',
            'script': "response = 'Henriki'",
            'template': ''},
        'status_code': 303},
    {
        'name': "Run a local report",
        'path': '/local_reports/1/output',
        'status_code': 200,
        'regexes': [
            r'Henriki']},
    {
        'name': "Delete downloaded reports",
        'path': '/downloads',
        'method': 'post',
        'status_code': 303},

    {
        'name': "Enable bank_holidays downloader",
        'path': '/non_core_contracts/2/edit',
        'method': 'post',
        'data': {
            'properties': """
{
            'enabled': True,
                'url':
                    'https://www.gov.uk/bank-holidays/england-and-wales.ics'}
"""},
        'status_code': 303},
    {
        'name': "Do an 'import now'.",
        'path': '/non_core_contracts/2/auto_importer',
        'method': 'post',
        'data': {
            'now': 'Now'},
        'status_code': 303},
    {
        'name': "Check that an import has happened.",
        'path': '/non_core_contracts/2/auto_importer',
        'tries': {},
        'regexes': [
            r'<ul>\s*<li>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} - '
            r'Finished checking bank holidays.</li>',
            r'Updating rate script starting at',
            r'<a href="/non_core_contracts/2/auto_importer">Refresh page</a>'],
        'status_code': 200},
    {
        'name': "Set up RCRC downloader",
        'path': '/non_core_contracts/6/edit',
        'method': 'post',
        'data': {
            'properties': """
{
            'enabled': True,
            'url': 'http://127.0.0.1:8080/elexonportal/',
            'limit': True}
"""},
        'status_code': 303},
    {
        'name': "Do an 'import now' on RCRC.",
        'path': '/non_core_contracts/6/auto_importer',
        'method': 'post',
        'data': {
            'now': 'Now'},
        'status_code': 303},
    {
        'name': "Check that an RCRC import has happened.",
        'path': '/non_core_contracts/6/auto_importer',
        'tries': {},
        'regexes': [
            r"Added new rate script\."],
        'status_code': 200},

    {
        'name': "Bill import error. Supplier contract",
        'path': '/supplier_bill_imports',
        'method': 'post',
        'data': {
            'supplier_batch_id': '4'},
        'files': {'import_file': 'test/bills_fail.csv'},
        'status_code': 303,
        'regexes': [
            r"/supplier_bill_imports/11"]},
    {
        'name': "Supplier contract 31, batch 4",
        'path': '/supplier_bill_imports/11',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"Can&#39;t find an era with contract &#39;Half-hourlies 2007&#39;"
            r" and account &#39;Landau&#39;\."]},

    {
        'name': "CSV Sites Duration",
        'path': '/csv_sites_duration',
        'status_code': 200},

    {
        'name': "View channel edit",
        'path': '/channels/40/edit',
        'status_code': 200,
        'regexes': [
            r'Channel Import\s*ACTIVE']},

    {
        'name': "Look at a LLFC",
        'path': '/llfcs/6128',
        'status_code': 200},

    {
        'name': "A DNO's LLFCs",
        'path': '/llfcs?dno_contract_id=25',
        'status_code': 200,
        'regexes': [
            r'<a href="/dno_contracts">DNO Contracts</a>']},

    {
        'name': "Comparison against ECOES",
        'path': '/reports/ecoes_comparison',
        'status_code': 200},

    {
        'name': "View a CoP",
        'path': '/cops/5',
        'status_code': 200},

    {
        'name': "View an HHDC bill",
        'path': '/hhdc_bills/15',
        'status_code': 200},

    {
        'name': "Edit view of an HHDC bill",
        'path': '/hhdc_bills/15/edit',
        'status_code': 200},

    {
        'name': "Non-core contracts",
        'path': '/non_core_contracts',
        'status_code': 200,
        'regexes': [
            r'Non-Core Contracts\s*</p>']},

    {
        'name': "View meter types",
        'path': '/meter_types',
        'status_code': 200},

    {
        'name': "View bill types",
        'path': '/bill_types',
        'status_code': 200},

    {
        'name': "View read types",
        'path': '/read_types',
        'status_code': 200},

    {
        'name': "View sources",
        'path': '/sources',
        'status_code': 200},

    {
        'name': "View generator types",
        'path': '/generator_types',
        'status_code': 200},

    {
        'name': "Check supplies snapshot at beginning of supply",
        'path': '/reports/33?supply_id=4&date_year=2003&date_month=08&'
        'date_day=03&date_hour=00&date_minute=00',
        'status_code': 303},
    {
        'name': "Check supplies snapshot at beginning of supply",
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"000_FINISHED_adminexamplecom_supplies_snapshot\.csv"],
        'status_code': 200},
    {
        'name': "Check supplies snapshot at beginning of supply",
        'path': '/downloads/'
        '000_FINISHED_adminexamplecom_supplies_snapshot.csv',
        'regexes': [
            r'CI005'],
        'status_code': 200},

    {
        'name': "Site level HH data with 3rd party supply",
        'path': '/supplies/1/edit',
        'method': 'post',
        'data': {
            'name': "Hello",
            'source_id': "5",
            'generator_type_id': "1",
            'gsp_group_id': "11"},
        'status_code': 303},
    {
        'name': "Site level HH data with 3rd party supply",
        'path': '/sites/7/hh_data?year=2008&month=07',
        'status_code': 200,
        'regexes': [
            r'<tr>\s*'
            r'<td>2008-07-06 03:30</td>\s*'
            r'<td>0</td>\s*'
            r'<td>0.249</td>\s*'
            r'<td>0</td>\s*'
            r'<td>0</td>\s*'
            r'<td>0</td>\s*'
            r'<td>0</td>\s*'
            r'<td>0.249</td>\s*'
            r'<td>A</td>\s*'
            r'<td></td>\s*'
            r'<td></td>\s*'
            r'</tr>']},

    {
        'name': "Graph with export",
        'path': '/sites/3/gen_graph?months=1&finish_year=2005&finish_month=09',
        'status_code': 200,
        'regexes': [
            r'<rect\s*'
            r'x="672px" y="64.0px" width="1px"\s*'
            r'height="16.0px" fill="blue" />']},

    {
        'name': "Site generation graph stradling groups",
        'path': '/sites/3/gen_graph?months=2&finish_year=2005&finish_month=10',
        'status_code': 200,
        'regexes': [
            r'<text x="672px" y="78.54368932038835px">\s*',
            r'September\s*'
            r'</text>\s*'
            r'<text x="2112px" y="78.54368932038835px">\s*'
            r'October\s*'
            r'</text>']},

    {
        'name': "Confirm delete supplier bill",
        'path': '/supplier_bills/11/edit?confirm_delete=Delete',
        'status_code': 200,
        'regexes': [
            r'<form method="post" action="">\s*',
            r'<fieldset>\s*',
            r'<input type="submit" name="delete" value="Delete">']},

    {
        'name': "Delete supplier bill",
        'path': '/supplier_bills/11/edit',
        'method': 'post',
        'data': {
            'delete': 'Delete'},
        'status_code': 303},

    {
        'name': "Ignore channel snag",
        'path': '/channel_snags/100/edit',
        'method': 'post',
        'data': {
            'ignore': 'true'},
        'status_code': 303},

    {
        'name': "Collapsing bills. Edit bill to make it collapsible",
        'path': '/supplier_bills/2/edit',
        'method': 'post',
        'data': {
            'reference': '00009',
            'account': '141 5532',
            'issue_year': '2006',
            'issue_month': '10',
            'issue_day': '08',
            'issue_hour': '23',
            'issue_minute': '00',
            'start_year': '2006',
            'start_month': '10',
            'start_day': '08',
            'start_hour': '23',
            'start_minute': '00',
            'finish_year': '2006',
            'finish_month': '10',
            'finish_day': '31',
            'finish_hour': '00',
            'finish_minute': '00',
            'kwh': '0',
            'net': '-641.67',
            'vat': '-290.87',
            'gross': '0',
            'bill_type_id': '2',
            'breakdown': '{}'},
        'status_code': 303},
    {
        'name': "Fetch bootstrap css",
        'path': '/bootstrap',
        'status_code': 200},
    {
        'name': "Fetch bootstrap js",
        'path': '/bootstrapjs',
        'status_code': 200},
    {
        'name': "Bill check with exception",
        'path': "/supplier_contracts/37/edit",
        'method': 'post',
        'data': {
            'party_id': '90',
            'name': 'Non half-hourlies 2010',
            'charge_script': """import chellow.duos
from werkzeug.exceptions import BadRequest


def virtual_bill_titles():
    return ['net-gbp', 'sum-msp-kwh', 'problem']

def virtual_bill(supply_source):
    raise BadRequest("Theory laden.")
    sum_msp_kwh = sum(h['msp-kwh'] for h in supply_source.hh_data)
    bill = supply_source.supplier_bill
    chellow.duos.duos_vb(supply_source)
    for rate_name, rate_set in supply_source.supplier_rate_sets.items():
        if len(rate_set) == 1:
            bill[rate_name] = rate_set.pop()
    bill['net-gbp'] += sum_msp_kwh * 0.1
    bill['sum-msp-kwh'] += sum_msp_kwh
""",
            'properties': '{}'},
        'status_code': 303},
    {
        'name': "Bill check with exception",
        'path': '/reports/111?bill_id=12',
        'status_code': 303},
    {
        'name': "Bill check with exception",
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"001_FINISHED_adminexamplecom_bill_check\.csv"],
        'status_code': 200},
    {
        'name': "Bill check with exception",
        'path': '/downloads/'
        '001_FINISHED_adminexamplecom_bill_check.csv',
        'regexes': [
            r'Theory laden\.'],
        'status_code': 200},
    {
        'name': "System Page",
        'path': '/system',
        'status_code': 200},
    {
        'name': "Virtual bill with exception",
        'path': '/reports/291?supply_id=10&start_year=2016&start_month=06&'
        'start_day=01&start_hour=00&start_minute=0&finish_year=2016&'
        'finish_month=06&finish_day=30&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"002_FINISHED_adminexamplecom_supply_virtual_bills_10\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '002_FINISHED_adminexamplecom_supply_virtual_bills_10.csv',
        'regexes': [
            r'Theory laden\.'],
        'status_code': 200},
    {
        'name': "Reverse proxy authentication",
        'path': '/non_core_contracts/5/edit',
        'method': 'post',
        'data': {
            'name': "configuration",
            'properties': """
{
    'site_links': [
        {'name': 'Google Maps', 'href': 'https://maps.google.com/maps?q='}],
    'batch_reports': [1],
    'elexonportal_scripting_key': 'xxx',
    'ecoes': {
        'user_name': 'a',
        'password': 'a',
        'prefix': 'http://localhost:8080/ecoes/'},
    'background_colour': 'aquamarine',
    'ad_authentication': {
        'on': True,
        'default_user': 'admin@example.com'}}
""", },
        'status_code': 303},
    {
        'name': "Reverse proxy authentication",
        'path': '/',
        'auth': None,
        'headers': {
            'X-Isrw-Proxy-Logon-User': 'admin@example.com'},
        'status_code': 200},
    {
        'name': "Reverse proxy authentication. Forbidden.",
        'path': '/sites/7/edit',
        'method': 'post',
        'data': {
            'code': "CH017",
            'name': "Parbola"},
        'auth': None,
        'headers': {
            'X-Isrw-Proxy-Logon-User': 'watkins@example.com'},
        'status_code': 403},
    {
        'name': "Reverse proxy authentication: revert to basic auth",
        'path': '/non_core_contracts/5/edit',
        'method': 'post',
        'headers': {
            'X-Isrw-Proxy-Logon-User': 'admin@example.com'},
        'data': {
            'name': "configuration",
            'properties': """
{
    'site_links': [
        {'name': 'Google Maps', 'href': 'https://maps.google.com/maps?q='}],
    'batch_reports': [1],
    'elexonportal_scripting_key': 'xxx',
    'ecoes': {
        'user_name': 'a',
        'password': 'a',
        'prefix': 'http://localhost:8080/ecoes/'},
    'background_colour': 'aquamarine'}
""", },
        'status_code': 303},

    {
        'name': "View site snag edit",
        'path': '/site_snags/41/edit',
        'auth': ('admin@example.com', 'admin'),
        'regexes': [
            r'<form action=""'],
        'status_code': 200},
]
