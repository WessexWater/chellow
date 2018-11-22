[
    {
        'name': "View users' page",
        'port': '8080',
        'host': 'localhost',
        'path': '/users',
        'auth': ('admin@example.com', 'admin'),
        'status_code': 200,
        'regexes': [
            r'"/chellowcss"'
        ]
    },
    {
        'name': "Manipulating users",
        'path': '/users',
        'method': 'post',
        'data': {
            'email_address': "watkin\\s@example.com",
            'user_role_code': "editor",
            'password': "alan"
        },
        'status_code': 303,
        'tries': {},
        'regexes': [
            r"http://localhost:8080/users/2"
        ]
    },
    {
        'path': '/users',
        'method': 'post',
        'data': {
            'email_address': "lydgate@localhost",
            'user_role_code': "editor",
            'password': "science"
        },
        'status_code': 303,
        'regexes': [
            r"/users/3"
        ]
    },

    {
        'path': '/users/3',
        'regexes': [
            r'<form method="post">\s*'
            r'<fieldset>\s*'
            r'<input type="hidden" name="change_password">\s*',
            r'<form>\s*'
            r'<fieldset>\s*'
            r'<input type="hidden" name="Delete this user">\s*'
        ],
        'status_code': 200},

    {
        'name': "Check that a duplicate email gives a proper error message",
        'path': '/users',
        'method': 'post',
        'data': {
            'email_address': "lydgate@localhost",
            'user_role_code': "editor",
            'password': "science"
        },
        'regexes': [
            r"already a user with this email address"
        ],
        'status_code': 400
    },

    {
        'name': "Test that we're able to change the password",
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
        'name': "Valid general import of sites",
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
        'path': '/non_core_contracts/2/edit',
        'method': 'post',
        'data': {
            'name': 'system_price',
            'properties': """
{
    "enabled": true,
    "urls": ["http://127.0.0.1:8080/nationalgrid/sf_bsuos.xls"]}
"""},
        'status_code': 303},
    {
        'name': "Do an 'import now'",
        'path': '/non_core_contracts/2/auto_importer',
        'method': 'post',
        'regexes': [
            '/non_core_contracts/2/auto_importer'],
        'status_code': 303},
    {
        'name': 'BSUoS',
        'path': '/non_core_contracts/2/auto_importer',
        'tries': {'max': 80, 'period': 1},
        'regexes': [
            r" - Added rate at 2014-09-06 06:00 for run SF\."],
        'status_code': 200},
    {
        'name': 'BSUoS',
        'path': '/non_core_rate_scripts/15',
        'regexes': [
            r'&#34;01 00:00&#34;: {\s*'
            r'&#34;SF&#34;: 1.66425\s*'
            r'},'],
        'status_code': 200},

    {
        'name': "Set configuration properties",
        'path': '/non_core_contracts/3/edit',
        'method': 'post',
        'data': {
            'properties': """
{
    "ips": {"127.0.0.1": "implicit-user@localhost"},
    "site_links": [
        {"name": "Google Maps", "href": "https://maps.google.com/maps?q="}],
    "elexonportal_scripting_key": "xxx",
    "background_colour": "aquamarine"}
"""},
        'status_code': 303},

    {
        'name': "Set up TLM downloader",
        'path': '/non_core_contracts/7/edit',
        'method': 'post',
        'data': {
            'properties': """
{
            "enabled": true,
            "url": "http://127.0.0.1:8080/elexonportal/"}
"""},
        'status_code': 303},
    {
        'name': "Do an 'import now' on TLM.",
        'path': '/non_core_contracts/7/auto_importer',
        'method': 'post',
        'data': {
            'now': 'Now'},
        'status_code': 303},
    {
        'name': "Check that an TLM import has happened.",
        'path': '/non_core_contracts/7/auto_importer',
        'tries': {'max': 70, 'period': 1},
        'regexes': [
            r" - Found rate at 2014-03-02 08:30 for GSP Group _L and run "
            r"RF\.",
            r"Finished checking TLM rates."],
        'status_code': 200},

    {
        'name': "Check it's been parsed properly",
        'path': '/non_core_rate_scripts/22',
        'regexes': [
            r'&#34;28 23:30&#34;: \{\s*'
            r'&#34;_A&#34;: \{\s*'
            r'&#34;RF&#34;: \{\s*'
            r'&#34;delivering&#34;: 0.9891357,\s*'
            r'&#34;off_taking&#34;: 1.0122079\s*'
            r'\}\s*'
            r'\},'],
        'status_code': 200},

    {
        'name': "DC contracts",
        'path': '/dc_contracts/add',
        'method': 'post',
        'data': {
            'party_id': "116",  # HHDC DASL
            'name': "HH contract",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'has_finished': "false"},
        'status_code': 303,
        'regexes': [
            r"/dc_contracts/8"]},

    {
        'name': "Update Contract",
        'path': '/dc_contracts/8/edit',
        'method': 'post',
        'data': {
            'party_id': "116",  # HHDC DASL
            'name': "HH contract",
            'charge_script': """
def virtual_bill_titles():
    return ['net-gbp', 'problem']

def virtual_bill(ds):
    level = ds.sess.execute("show transaction isolation level;").fetchone()[0]
    if level != 'serializable':
        raise Exception(
            "Transaction isolation level is " + level +
            ", but it should be serializable!")
    bill = ds.dc_bill
    for hh in ds.hh_data:
        if hh['utc-is-month-end']:
            bill['net-gbp'] += 10
""",
            'properties': '{"mpan_map": {"maptest": "2292056799106"}}'},
        'status_code': 303},

    {
        'path': '/dc_contracts/8',
        'regexes': [
            r'HH contract\s*\[<a href="/dc_contracts/8/edit">edit</a>\]',
            r'<form action="/reports/81">'],
        'status_code': 200},

    {
        'name': "Check that we can see DC rate script okay. Contract 8.",
        'path': '/dc_rate_scripts/24',

        # Check that 'has_finished' field is there
        'regexes': [
            r'HH contract'],
        'status_code': 200},

    {
        'name': "Check that we can see the edit view of the DC rate "
        "script okay. Contract 8.",
        'path': '/dc_rate_scripts/24/edit',

        # Check that 'has_finished' field is there
        'regexes': [
            r"has_finished"],

        'status_code': 200},

    {
        'name': "Check that we can update an DC rate script okay",
        'path': '/dc_rate_scripts/24/edit',
        'method': 'post',
        'data': {
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'script': "{}"},
        'status_code': 303,
        'regexes': [
            r'/dc_rate_scripts/24']},

    {
        'name': "Add another DC contract",
        'path': '/dc_contracts/add',
        'method': 'post',
        'data': {
            'party_id': "116",  # HHDC DASL
            'name': "Dynamat data",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00"},
        'status_code': 303,
        'regexes': [
            r"/dc_contracts/9"]},

    {
        'name': "Update the newly added DC",
        'path': '/dc_contracts/9/edit',
        'method': 'post',
        'data': {
            'party_id': "116",  # HHDC DASL
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
        'name': "Update state of Dynamat DC",
        'path': '/dc_contracts/9/edit',
        'method': 'post',
        'data': {
            'update_state': "",
            'state': '{"stat": 2}'},
        'status_code': 303},

    {
        'name': "View edit Dynamat DC",
        'path': '/dc_contracts/9/edit',
        'status_code': 200,
        'regexes': [
            r'<textarea name="charge_script" rows="40" cols="80">\s*'
            r'def virtual_bill_title',
            r'<textarea name="properties" rows="40" cols="80">\{\s*'
            r'&#34;props&#34;: 1\s*'
            r'\}</textarea>',
            r'<textarea name="state" rows="40" cols="80">\{\s*'
            r'&#34;stat&#34;: 2\s*'
            r'\}</textarea>']},
    {
        'name': "Check one can update the participant for an DC contract.",
        'path': '/dc_contracts/9/edit',
        'method': 'post',
        'data': {
            'party_id': "1121",  # UKDC
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
            'properties': '{"enables": "false"}'},
        'status_code': 303},

    {
        'name': "Check it's still there",
        'path': '/dc_contracts/9/edit',
        'status_code': 200,
        'regexes': [
            r'option value="1121" selected']},

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
            'participant_id': "33",  # BIZZ
            'name': "Half-hourlies 2007",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'charge_script': "",
            'properties': '{"hydrogen": "sonata"}'},
        'regexes': [
            r"/supplier_contracts/10"]},

    {
        'name': "Check that it's displayed properly",
        'path': '/supplier_contracts/10/edit',
        'regexes': [
            r'<option value="28" selected>',
            r'<textarea name="properties" rows="20" cols="80">\{\s*'
            r'&#34;hydrogen&#34;: &#34;sonata&#34;\s*'
            r'\}</textarea>'],
        'status_code': 200},
    {
        'path': '/supplier_contracts/10',
        'regexes': [
            r'<legend>Download Displaced Virtual Bills</legend>\s*<br/>\s*'
            r'For <input name="months" value="1" maxlength="2" size="2">\s*'
            r'month\(s\) until the end of\s*'
            r'<input name="finish_year" maxlength="4" size="4" '
            r'value="201\d">',
            r'Rate Scripts\s*\[<a\s*'
            r'href="/supplier_contracts/10/add_rate_script"\s*>add</a>\]'],
        'status_code': 200},

    {
        'name': "Update the associated rate script. Supplier contract 15",
        'path': '/supplier_rate_scripts/26/edit',
        'method': 'post',
        'data': {
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'has_finished': "false",
            'script': """{
  "gsp_gbp_per_kwh": {
  "winter-pk": 0.0193918,
  "winter-low-pk": 0.0501474,
  "winter-off-pk": 0.0062656,
  "summer-pk": 0.0062656,
  "night": 0.0062656,
  "other": 0.0062656}}
"""},
        'status_code': 303},
    {
        'name': "View supplier rate script",
        'path': '/supplier_rate_scripts/26',
        'regexes': [
            r'"/supplier_rate_scripts/26/edit"'],
        'status_code': 200},
    {
        'name': "Edit view of supplier rate script",
        'path': '/supplier_rate_scripts/26/edit',
        'regexes': [
            r'"/supplier_rate_scripts/26"'],
        'status_code': 200},

    {
        'name': "View add MOP contract",
        'path': '/mop_contracts/add',
        'regexes': [
            r'Lowri Beck Services Limited'],
        'status_code': 200},

    {
        'name': "Insert MOP contract",
        'path': '/mop_contracts/add',
        'method': 'post',
        'data': {
            'participant_id': "487",  # LENG
            'name': "MOP Contract",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00"},
        'status_code': 303,
        'regexes': [
            r"/mop_contracts/11"]},

    {
        'name': "Update with a charge script",
        'path': '/mop_contracts/11/edit',
        'method': 'post',
        'data': {
            'party_id': "788",  # LENG
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
            r"/mop_contracts/11"]},

    {
        'name': "Check we can see the rate scripts",
        'path': '/mop_contracts/11',
        'status_code': 200},

    {
        'name': "Insert a modern supplier contract. Create a new supplier "
        "contract for 2013",
        'path': '/supplier_contracts/add',
        'method': 'post',
        'data': {
            'participant_id': "70",  # COOP
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
            r"/supplier_contracts/12"],
        'status_code': 303},
    {
        'name': "Update the associated rate script. Supplier contract 39",
        'path': '/supplier_rate_scripts/28/edit',
        'method': 'post',
        'data': {
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'has_finished': "false",
            'script': """{
"gsp_gbp_per_kwh": {
  "winter-pk": 0.0193918,
  "winter-low-pk": 0.0501474,
  "winter-off-pk": 0.0062656,
  "summer-pk": 0.0062656,
  "night": 0.0062656,
  "other": 0.0062656}}
"""},
        'status_code': 303,
        'regexes': [
            r'/supplier_rate_scripts/28']},

    {
        'name': "Create a new supplier contract",
        'path': '/supplier_contracts/add',
        'method': 'post',
        'data': {
            'participant_id': "459",  # HYDE
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
            'properties': "{}"},
        'regexes': [
            r"/supplier_contracts/13"],
        'status_code': 303},

    {
        'name': "supplies",
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/supplies-too-few-fields.csv'},
        'regexes': [
            r"/general_imports/2"
        ],
        'status_code': 303
    },

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

    {
        'name': "Line 2 has a DNO that doesn't exist",
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/supplies_dno.csv'},
        'regexes': [
            r"/general_imports/4"
        ],
        'status_code': 303
    },

    {
        'path': '/general_imports/4',
        'tries': {},

        # check that it knows that line 2 has a DNO that doesn't exist
        'regexes': [
            r"There is no DNO with the code &#39;79&#39;\."],
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
            r"the form yyyy-mm-dd hh:MM. invalid literal for int\(\) with "
            r"base 10: "],
        'status_code': 200},

    {
        'name': "Check for a sensible error message if the site doesn't exist",
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/supplies_no_site.csv'},
        'regexes': [
            r"/general_imports/6"],
        'status_code': 303},
    {
        'path': '/general_imports/6',
        'tries': {},

        # check that it knows that line 1 has a malformed date
        'regexes': [
            r"There isn&#39;t a site with the code zzznozzz\."],
        'status_code': 200},

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

    {
        'name': "Check that a supply with only an import MPAN is there",
        'path': '/sites/4/edit',
        'regexes': [
            r'22 6354 2983 570',
            r'<form action="/sites/4/edit" method="post">\s*'
            r'<fieldset>\s*'
            r'<legend>Insert a gas supply</legend>',
            r'<select name="g_exit_zone_id">\s*'
            r'<option',
            r'<input name="insert_electricity" type="submit" value="Insert">'],
        'status_code': 200},

    # Can we see a site ok?
    {
        'path': '/sites/1/edit',

        # Is the era displayed?
        'regexes': [
            r"<tr>\s*<td>2003-08-03 00:00</td>\s*<td>Ongoing</td>\s*"
            r"<td>gen</td>\s*<td>2</td>\s*<td>\s*</td>\s*<td>\s*"
            r"22 7907 4116 080\s*</td>\s*</tr>",

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
            r'<table class="DataTable widthAuto">\s',

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
            'gsp_group_id': "10"},
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
            'gsp_group_id': "10"},
        'status_code': 303},

    {
        'name': "View era in edit mode. Supply 1",
        'path': '/eras/1/edit',

        # Check start date year is there
        'regexes': [
            r"start_year",
            r'<option value="8" selected>HH contract</option>',
            r'"imp_supplier_contract_id">\s*'
            r'<option value="10" selected>Half-hourlies 2007',

            # Can we see the MOP account?
            r'"mc-22 9205 6799 106"',

            # Export Supplier Account
            r'<input name="exp_supplier_account" value="04">'
        ],

        'status_code': 200
    },

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

    {
        'name': "When a supply era is ended, check that the snags are "
        "updated. Supply 5",
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
            'gsp_group_id': "10",
            'mop_contract_id': "11",
            'mop_account': "22 0883 6932 301",
            'dc_contract_id': "9",
            'dc_account': "22 0883 6932 301",
            'msn': "",
            'pc_id': "0",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'properties': "{}",
            'imp_llfc_code': "570",
            'imp_mpan_core': "22 0883 6932 301",
            'imp_sc': "350",
            'imp_supplier_contract_id': "10",
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
            r'<a\s*'
            r'title="2003-08-13 23:30"\s*'
            r'>2003-08-13</a>',
            r'<form action="/reports/187" method="post">',
            r'<legend>TRIAD</legend>\s*<input type="hidden" name="supply_id"',
            r'<a href="/supplies/5/months\?'
            r'is_import=true&amp;year=\d{4}&amp;years=1">Import</a>',
            r'<a href="/supplies/5/virtual_bill']},

    # Supply 5, Era 5
    {
        'path': '/channels/18',
        'status_code': 200,

        # Check the end date is right
        'regexes': [
            r"Channel Export\s*REACTIVE_EXP",
            r"<td>2003-08-03 00:00</td>\s*<td>2003-08-13 23:30</td>\s*"
            r"<td>Missing</td>"]},

    # Check that if the dc contract is changed, the dc contract of the
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
            'mop_contract_id': "11",
            'mop_account': "22 0883 6932 301",
            'dc_contract_id': "8",
            'dc_account': "22 0883 6932 301",
            'pc_id': "0",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'properties': "{}",
            'imp_llfc_code': "570",
            'imp_mpan_core': "22 0883 6932 301",
            'imp_gsp_group_id': "10",
            'imp_sc': "430",
            'imp_supplier_contract_id': "10",
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
            r"<td>Missing</td>"]},

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
            'mop_contract_id': "11",
            'mop_account': "22 0883 6932 301",
            'dc_contract_id': "8",
            'dc_account': "22 0883 6932 301",
            'pc_id': "0",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'properties': "{}",
            'imp_llfc_code': "570",
            'imp_mpan_core': "22 0883 6932 301",
            'imp_sc': "350",
            'imp_supplier_contract_id': "10",
            'imp_supplier_account': "4341"},
        'status_code': 303},

    {
        'name': "View general imports",
        'path': '/general_imports',
        'status_code': 200,
        'regexes': [
            r'"/chellowcss"']},

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
            r"supply\."],
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
            'mop_contract_id': "11",
            'mop_account': "mc-22 9813 2107 763",
            'dc_contract_id': "8",
            'dc_account': "01",
            'pc_id': "0",
            'mtc_code': "845",
            'cop_id': "3",
            'ssc_code': "",
            'properties': "{}",
            'imp_llfc_code': "570",
            'imp_mpan_core': "2276930477695",
            'imp_sc': "430",
            'imp_supplier_contract_id': "10",
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
            'mop_contract_id': "11",
            'mop_account': "mc-22 9813 2107 763",
            'dc_contract_id': "8",
            'dc_account': "01",
            'pc_id': "0",
            'mtc_code': "845",
            'cop_id': "3",
            'ssc_code': "",
            'properties': "{}",
            'imp_llfc_code': "521",
            'imp_mpan_core': "22 9813 2107 763",
            'imp_sc': "430",
            'imp_supplier_contract_id': "10",
            'imp_supplier_account': "01"},
        'status_code': 400,
        'regexes': [
            r"The imp line loss factor 521 is actually an exp one\."]},

    # Check it gives a sensible error message if the files doesn't start
    # with #F2
    {
        'name': "Import hh data",
        'path': '/dc_contracts/8/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/no_hash.df2'},
        'regexes': [
            r"/dc_contracts/8/hh_imports/0"],
        'status_code': 303},
    {
        'path': '/dc_contracts/8/hh_imports/0',
        'tries': {},
        'regexes': [
            r"The first line must be &#39;#F2&#39;"],
        'status_code': 200},

    {
        'name': "Import some hh Stark DF2 data",
        'path': '/dc_contracts/8/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/ftp/hh_data.df2'},
        'status_code': 303,
        'regexes': [
            r"/dc_contracts/8/hh_imports/1"]},
    {
        'path': '/dc_contracts/8/hh_imports/1',
        'tries': {},

        # Check it's loaded ok and has ignored the blank line and the #F2 line
        'regexes': [
            r"The import has completed.*successfully.",

            # Check link to dc is correct
            r"/dc_contracts/8"],
        'status_code': 200},

    {
        'name': 'Supply 1, era 1',
        'path': '/channels/4',
        'regexes': [
            r"Channel Export\s*REACTIVE_EXP",
            r'<tr>\s*<td>\s*'
            r'<a href="/channel_snags/4">view</a>\s*'
            r'</td>\s*<td>2003-08-03 00:00</td>\s*<td>Ongoing</td>\s*'
            r'<td>Missing</td>'],
        'status_code': 200},

    {
        'name': "Check if more hh data imports ok",
        'path': '/dc_contracts/8/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh_data2.df2'},
        'status_code': 303},

    # This relies on the datum 15/11/2005,00:30,1.0,A being already loaded,
    # with a gap before it.
    {
        'name': "Detect if hh import still works if first hh datum is "
        "missing.",
        'path': '/dc_contracts/8/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/missing.df2'},
        'regexes': [
            r"/dc_contracts/8/hh_imports/3"],
        'status_code': 303},
    {
        'path': '/dc_contracts/8/hh_imports/3',
        'tries': {},
        'regexes': [
            r"The import has completed.*successfully."],
        'status_code': 200},

    # This relies on the default timezone being BST },
    {
        'name': "Do we handle BST ok?",
        'path': '/dc_contracts/8/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh_data_timezone.df2'},
        'regexes': [
            r"/dc_contracts/8/hh_imports/4"],
        'status_code': 303},
    {
        'path': '/dc_contracts/8/hh_imports/4',

        # Check it's loaded ok
        'tries': {},
        'regexes': [
            r"The import has completed.*successfully."],
        'status_code': 200},

    # Test that 3 non-actual reads in a row generate a single snag
    {
        'name': "Actual reads snags combined properly",
        'path': '/dc_contracts/8/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh_data_not_actual.df2'},
        'regexes': [
            r"/dc_contracts/8/hh_imports/5"],
        'status_code': 303},
    {
        'path': '/dc_contracts/8/hh_imports/5',
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
            r'<a href="/channel_snags/45">view</a>\s*'
            r'</td>\s*<td>2005-12-15 07:00</td>\s*<td>2005-12-15 08:00</td>\s*'
            r'<td>Estimated</td>',
            r'<tr>\s*<td>\s*'
            r'<a href="/channel_snags/3">view</a>\s*'
            r'</td>\s*<td>2003-08-03 00:00</td>\s*<td>2005-12-15 06:30</td>\s*'
            r'<td>Missing</td>'],
        'status_code': 200},
    {
        'path': '/dc_contracts/8/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh_data_not_actual2.df2'},
        'regexes': [
            r'/dc_contracts/8/hh_imports/6'],
        'status_code': 303},
    {
        'path': '/dc_contracts/8/hh_imports/6',
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
            r'<a href="/channel_snags/45">view</a>\s*'
            r'</td>\s*<td>2005-12-15 07:00</td>\s*<td>2005-12-15 09:30</td>\s*'
            r'<td>Estimated</td>'],
        'status_code': 200},

    # Test if a CSV HH file can be imported },
    {
        'name': "Importing simple CSV data",
        'path': '/dc_contracts/8/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh_data.simple.csv'},
        'regexes': [
            r"/dc_contracts/8/hh_imports/7"],
        'status_code': 303},
    {
        'path': '/dc_contracts/8/hh_imports/7',
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
        'path': '/dc_contracts/8/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh_data_malformed.df2'},
        'regexes': [
            r"/dc_contracts/8/hh_imports/8"],
        'status_code': 303},
    {
        'path': '/dc_contracts/8/hh_imports/8',
        'tries': {},
        'regexes': [
            r"Problem at line number: 4"],
        'status_code': 200},

    # Check it gives a sensible error message if the first mpan is malformed
    {
        'path': '/dc_contracts/8/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh_data_bad_beginning.df2'},
        'regexes': [
            r"/dc_contracts/8/hh_imports/9"],
        'status_code': 303},
    {
        'path': '/dc_contracts/8/hh_imports/9',
        'tries': {},
        'regexes': [
            r"The MPAN core &#39;2204707514535,,,&#39; must contain exactly "
            "13 digits"],
        'status_code': 200},

    {
        'name': "Check sensible error message if header but no data",
        'path': '/dc_contracts/8/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh_data_header_but_no_data.df2'},
        'regexes': [
            r"/dc_contracts/8/hh_imports/10"],
        'status_code': 303},
    {
        'path': '/dc_contracts/8/hh_imports/10',
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
            r'<tr>\s*'
            r'<td>\s*'
            r'<a href="/site_snags/41">view</a>\s*'
            r'\[<a href="/site_snags/41/edit">edit</a>\]\s*'
            r'</td>\s*'
            r'<td>\d\d\d\d-\d\d-\d\d \d\d:\d\d</td>\s*'
            r'<td>\s*'
            r'<a href="/sites/1">CI004</a>\s*'
            r'</td>\s*'
            r'<td>Lower Treave</td>\s*'
            r'<td>Export to net &gt; import from generators.</td>\s*'
            r'<td>2005-11-14 23:30</td>\s*'
            r'<td>2005-11-15 00:00</td>\s*'
            r'</tr>\s*'
            r'<tr>\s*'
            r'<td>\s*'
            r'<a href="/site_snags/43">view</a>\s*'
            r'\[<a href="/site_snags/43/edit">edit</a>\]\s*'
            r'</td>\s*<td>[^<]*</td>\s*'
            r'<td>\s*'
            r'<a href="/sites/1">CI004</a>\s*'
            r'</td>\s*<td>Lower Treave</td>\s*'
            r'<td>Export to net &gt; import from generators.</td>\s*'
            r'<td>2005-10-29 23:30</td>\s*<td>\s*2005-10-30 01:00</td>\s*'
            r'</tr>\s*</tbody>'],
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
            r'<a href="/channel_snags\?dc_contract_id=8&amp;days_hidden=5">'
            r'Channel Snags</a>']},

    {
        'name': "Check edit view of channel level snag",
        'path': '/channel_snags/1/edit',
        'status_code': 200,
        'regexes': [
            r'<form method="post">\s*'
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

    # Check it gives an error if the dc contract is removed from a supply era
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
            'gsp_group_id': "10",
            'pc_id': "0",
            'dc_contract_id': "null",
            'dc_account': "01",
            'properties': "{}",
            'imp_mtc_code': "845",
            'imp_llfc_code': "550",
            'imp_mpan_core': "22 9205 6799 106",
            'imp_ssc_code': "",
            'imp_sc': "450",
            'imp_supplier_contract_id': "9",
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
        'path': '/dc_contracts/8/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/ftp/hh_data.df2'},
        'regexes': [
            r"/dc_contracts/8/hh_imports/11"],
        'status_code': 303},
    {
        'path': '/dc_contracts/8/hh_imports/11',
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
            r"<td>A</td>",
        ],
        'status_code': 200},

    # Create a new batch
    {
        'name': "Batches",
        'path': '/supplier_contracts/10/add_batch',
        'method': 'post',
        'data': {
            'reference': "04-003",
            'description': "Contract 4, batch number 3"},
        'status_code': 303},

    # Check it gives a good error message for a duplicate name
    {
        'path': '/supplier_contracts/10/add_batch',
        'method': 'post',
        'data': {
            'reference': "04-003",
            'description': "dup batch"},
        'regexes': [
            r"There&#39;s already a batch attached to the contract "
            r"Half-hourlies 2007 with the reference 04-003\."],
        'status_code': 400},

    # Create a new import. Supplier contract 31
    {
        'name': "Bill imports",
        'path': '/supplier_bill_imports',
        'method': 'post',
        'data': {
            'supplier_batch_id': '1'},
        'files': {'import_file': 'test/bills.mm'},
        'status_code': 303,
        'regexes': [
            r'/supplier_bill_imports/0']},

    {
        'name': "Supplier contract 10, batch 1",
        'path': '/supplier_bill_imports/0',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"<td>2007-02-28 00:00</td>\s*<td>0.00</td>\s*<td>4463.08</td>",
            r"All the bills have been successfully loaded and attached to the "
            r"batch\."]},

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
        'path': '/supplier_contracts/13/add_batch',
        'method': 'post',
        'data': {
            'reference': "06-002",
            'description': "Bgb batch"},
        'status_code': 303},

    {
        'name': "Supplier contract 13",
        'path': '/supplier_bill_imports',
        'method': 'post',
        'data': {
            'supplier_batch_id': '3'},
        'files': {'import_file': 'test/bills.bgb.edi'},
        'status_code': 303,
        'regexes': [
            r"/supplier_bill_imports/1"]},

    {
        'name': "Supplier contract 19, batch 3",
        'path': '/supplier_bill_imports/1',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"All the bills have been successfully loaded and attached to the "
            r"batch\."]},

    # Set a previously estimated HH to actual, supply 1, era 1, channel 3
    {
        'name': "Check that resolved HH estimates have their snags cleared.",
        'path': '/hh_data/13/edit',
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
            r"<td>Estimated</td>"]},

    # Change it back. supply 1, era 1.
    {
        'path': '/hh_data/13/edit',
        'method': 'post',
        'data': {
            'value': "0.5",
            'status': "E"},
        'status_code': 303},
    {
        'name': "Test of BGlobal HH data import",
        'path': '/dc_contracts/8/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh_data.bg.csv'},
        'status_code': 303,
        'regexes': [
            r"/dc_contracts/8/hh_imports/12"]
        },
    {
        'path': '/dc_contracts/8/hh_imports/12',
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
            'pc_id': "0",
            'mtc_code': "535",
            'llfc_code': "510",
            'imp_mpan_core': "22 0195 4836 192",
            'ssc_code': "0127",
            'gsp_group_id': "10",
            'imp_sc': "30",
            'dc_contract_id': "HH contract",
            'dc_account': "",
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
        'path': '/supplier_contracts/10/add_batch',
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

    # Supplier contract 59, batch 4
    {
        'path': '/supplier_bill_imports/2',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"All the bills have been successfully loaded and attached to the "
            r"batch\."]},

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
            r'\[<a href="/hh_data/67/edit">'
            r'edit</a>\]\s*</td>\s*<td>2008-07-07 00:00</td>\s*'
            r'<td>0.247</td>\s*<td>A</td>'
        ],
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
            r"0000_FINISHED_watkinsexamplecom_supplies_duration\.csv"],
        'status_code': 200},

    {
        'path': '/downloads/'
        '0000_FINISHED_watkinsexamplecom_supplies_duration.csv',
        'regexes': [
            # Check starts with titles
            r'\)\s\sEra Start',

            r'(1,1,net,,CH017,){1}',

            # Check full line
            r'2006-07-20 00:00,,2,1,net,,CI004,Lower Treave,,2008-07-01 00:00,'
            r'2008-07-31 23:30,00,845,5,,\{\},MOP Contract,'
            r'mc-22 9813 2107 763,HH contract,01,0,hh,2003-08-03 00:00,,'
            r'570,22 9813 2107 763,430,Half-hourlies 2007,0,0,0.0,0,,None,'
            r'1488,581,22 3475 1614 211,900,Half-hourlies 2007,0,0,0.0,0,,'
            r'None,1488'],
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
            r'\[<a href="/hh_data/115/edit">edit</a>\]\s*'
            r'</td>\s*<td>2008-07-08 00:00</td>\s*'
            r'<td>0.299</td>\s*'
            r'<td>A</td>'],
        'status_code': 200},

    # supply 1, era 1, channel 1
    {
        'name': "Check one is redirected to hh data when a datum is deleted.",
        'path': '/hh_data/24/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'status_code': 303,
        'regexes': [
            r"/channels/1"]},

    # Supply 5
    {
        'name': "Test that it gives an error if the dc_contract_id is null.",
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
            'mop_contract_id': "11",
            'mop_account': "22 0883 6932 301",
            'dc_contract_id': "null",
            'pc_id': "0",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'imp_llfc_code': "570",
            'imp_mpan_core': "22 0883 6932 301",
            'imp_sc': "350",
            'imp_supplier_contract_id': "64",
            'imp_supplier_account': "01"},
        'status_code': 400,
        'regexes': [
            r"Problem parsing the field dc_contract_id as an integer: "
            r"invalid literal for int\(\) with base 10: .*null"]},
    {
        'name': "Test that profile 05 is displayed for an era. Supply 9",
        'path': '/eras/9/edit',
        'regexes': [
            r'<option value="5" selected>05 - Non-domestic, MD, load factor '
            r'0-20%</option>'],
        'status_code': 200},
    {
        'name': "Try adding a party viewer.",
        'path': '/users',
        'method': 'post',
        'data': {
            'email_address': "mishka@localhost",
            'password': "fyodor",
            'user_role_code': "party-viewer",
            'party_id': "116"},  # DASL DC

        'status_code': 303,
        'regexes': [
            r"/users/5"]},
    {
        'name': "Check that the party viewer is able to view snags.",
        'path': '/channel_snags?dc_contract_id=8&days_hidden=5',
        'auth': ('mishka@localhost', 'fyodor'),
        'regexes': [
            r"<td>\s*22 0470 7514 535\s*</td>\s*<td>\s*<ul>\s*<li>\s*"
            r"CH017 Parbola\s*</li>",
            r"There are 46 snag\(s\) older than\s*5 days\s*"
            r"that aren't ignored\.",
            r'<a href="/dc_contracts/8">HH contract</a>',
            r'<li>\s*'
            r'<a href="/channel_snags/1">view</a>\s*'
            r'\[<a href="/channel_snags/1/edit">edit</a>\]\s*'
            r'</li>',
            r'<form action="/reports/233">'],
        'status_code': 200},
    {
        'name': "Make sure everything's there on the home page.",
        'path': '/',
        'auth': ('watkin\\s@example.com', 'alan'),
        'regexes': [
            r'csv_register_reads',
            r'<a href="/participants">Market Participants</a>',
            r'<a href="/meter_payment_types">Meter Payment Types</a>',
            r'<a href="/sources">\s*Sources\s*</a>',
            r'<a href="/generator_types">\s*Generator Types\s*'
            r'</a>',
            r'<a\s*'
            r'href="/ods_scenario_runner"\s*'
            r'>\s*'
            r'Scenario Runner\s*'
            r'</a>'],
        'status_code': 200},

    {
        'name': "Show confirm-delete supplier rate script"
        "contract.",
        'path': '/supplier_rate_scripts/26/edit?delete=Delete',
        'status_code': 200,
        'regexes': [
            r'<form\s*'
            r'method="post"\s*'
            r'action="/supplier_rate_scripts/26/edit"\s*'
            r'>\s*'
            r'<fieldset>\s*'
            r'<input type="submit" name="delete" value="Delete">']},

    {
        'name': "Test deleting the only rate script attached to a supplier "
        "contract.",
        'path': '/supplier_rate_scripts/26/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'regexes': [
            r"You can&#39;t delete the last rate script\."],
        'status_code': 400},
    {
        'name': "Try adding a second rate script (set to 'ongoing'), and see "
        "if the era can be updated.",
        'path': '/supplier_contracts/10/add_rate_script',
        'method': 'post',
        'data': {
            'start_year': "2009",
            'start_month': "08",
            'start_day': "16",
            'start_hour': "00",
            'start_minute': "00",
            'script': ""},
        'status_code': 303},

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
            'mop_contract_id': "11",
            'mop_account': "mc-22 0470 7514 535",
            'dc_contract_id': "8",
            'dc_account': "01",
            'msn': "",
            'pc_id': "0",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'properties': "{}",
            'exp_llfc_code': "581",
            'exp_mpan_core': "22 0470 7514 535",
            'exp_sc': "150",
            'exp_supplier_contract_id': "10",
            'exp_supplier_account': "010"},
        'status_code': 303},
    {
        'name': "Check updating of DC contract state.",
        'path': '/dc_contracts/8/edit',
        'method': 'post',
        'data': {
            'state': """{
"last_import_keys": {".": "1960-11-30 00:00_example.csv"}}
""",
            'update_state': "Update State"},
        'status_code': 303},
    {
        'path': '/dc_contracts/8',
        'status_code': 200,
        'regexes': [
            r"\{\s*&#34;last_import_keys&#34;: \{\s*"
            r'&#34;.&#34;: &#34;1960-11-30 00:00_example.csv&#34;\s*'
            r'\}\s*'
            r'\}',

            # Check link to channel snags
            r"days_hidden",

            # Check link to add a rate script
            r'Rate Scripts\s*'
            r'\[<a href="/dc_contracts/8/add_rate_script">'
            r'add</a>\]']},

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
        'path': '/supplier_contracts/10/add_rate_script',
        'regexes': [
            r"/supplier_contracts/10"]},
    {
        'name': "Check 'HH Contract' option is there. Supply 9.",
        'path': '/eras/9/edit',
        'regexes': [
            r'<option value="8">HH contract</option>\s*</select>']},
    {
        'name': "Try bulk delete of DC snags.",
        'path': '/dc_contracts/8/edit',
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
        'path': '/supplier_contracts/10/edit',
        'method': 'post',
        'data': {
            'party_id': "28",  # BIZZ
            'name': "Half-hourlies 2007",
            'charge_script': """
def virtual_bill(supply, startDate, finishDate, pw):
    syntax error
""",
            'properties': "{}"},
        'regexes': [
            r'<li>\s*'
            r'invalid syntax \(&lt;unknown&gt;, line 3\)\s*'
            r'</li>'],
        'status_code': 400},

    # Put back to how it was before
    {
        'path': '/supplier_contracts/10/edit',
        'method': 'post',
        'data': {
            'party_id': "28",  # BIZZ
            'name': "Half-hourlies 2007",
            'charge_script': """
from operator import itemgetter
from dateutil.relativedelta import relativedelta
from chellow.utils import HH, utc_datetime
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
    chellow.triad.hh(supply_source)
    chellow.triad.bill(supply_source)
    chellow.tlms.hh(supply_source)
    chellow.bsuos.hh(supply_source)

    for hh in supply_source.hh_data:
        hh_start = hh['start-date']
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
            db_id, hh_start)['gsp_gbp_per_kwh']
        bill[slot_keys['gbp']] += hh['gsp-kwh'] * float(rates[slot_name])
        bill['bsuos-kwh'] += hh['nbp-kwh']
        bill['bsuos-gbp'] += hh['bsuos-gbp']

        if hh['utc-is-month-end']:
            month_start = utc_datetime(hh_start.year, hh_start.month, 1)
            ccl_kwh = 0
            ccl_gbp = 0
            for ds in supply_source.get_data_sources(month_start, hh_start):
                chellow.ccl.ccl(ds)
                for h in ds.hh_data:
                    ccl_kwh += h['ccl-kwh']
                    ccl_gbp += h['ccl-gbp']

            if ccl_kwh > 999:
                bill['ccl-kwh'] += ccl_kwh
                bill['ccl-gbp'] += ccl_gbp

    chellow.system_price.hh(supply_source)

    for rate_name, rate_set in rate_sets.items():
        bill[rate_name] = rate_set

    for k in list(bill.keys()):
        if k.startswith('duos-reactive-'):
            del bill[k]

    bill['net-gbp'] = sum(v for k, v in bill.items() if k[-4:] == '-gbp')


def virtual_bill(supply_source):
    chellow.duos.duos_vb(supply_source)
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
    chellow.tlms.hh(supply_source)
    chellow.bsuos.hh(supply_source)

    for hh in supply_source.hh_data:
        hh_start = hh['start-date']
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

        if hh['utc-is-month-end']:
            month_start = utc_datetime(hh_start.year, hh_start.month, 1)
            ccl_kwh = 0
            ccl_gbp = 0
            for ds in supply_source.get_data_sources(month_start, hh_start):
                chellow.ccl.ccl(ds)
                for h in ds.hh_data:
                    ccl_kwh += h['ccl-kwh']
                    rate_sets['ccl-rate'].add(h['ccl-rate'])
                    ccl_gbp += h['ccl-gbp']

            if ccl_kwh > 999:
                bill['ccl-kwh'] += ccl_kwh
                bill['ccl-gbp'] += ccl_gbp

        bill['bsuos-kwh'] += hh['nbp-kwh']
        bill['bsuos-gbp'] += hh['bsuos-gbp']

    month_begin = utc_datetime(
        supply_source.start_date.year, supply_source.start_date.month, 1)
    month_end = month_begin + relativedelta(months=1) - HH

    bill['data-collection-gbp'] += 5.89
    bill['settlement-gbp'] += 88

    chellow.system_price.hh(supply_source)
    rates = supply_source.hh_rate(
        db_id, supply_source.finish_date)['gsp_gbp_per_kwh']
    for slot_name in slot_names:
        slot_keys = slots[slot_name]
        bill[slot_keys['gbp']] = bill[slot_keys['gsp-kwh']] * float(
            rates[slot_name])

    for rate_name, rate_set in rate_sets.items():
        bill[rate_name] = rate_set

    bill['net-gbp'] = sum(v for k, v in bill.items() if k.endswith('-gbp'))
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
            'mop_contract_id': "11",
            'mop_account': "mc-22 0470 7514 535",
            'dc_contract_id': "8",
            'dc_account': "01",
            'msn': "",
            'pc_id': "0",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'properties': "{}",
            'exp_llfc_code': "581",
            'exp_mpan_core': "22 0470 7514 535",
            'exp_sc': "150",
            'exp_supplier_contract_id': "10",
            'exp_supplier_account': "010"},
        'status_code': 303},

    # Supply 1
    {
        'path': '/eras/14/edit',
        'regexes': [
            r'<select name="finish_day">\s*<option value="1">01</option>\s*'
            r'<option value="2">02</option>\s*<option value="3">03</option>\s*'
            r'<option value="4">04</option>\s*'
            r'<option value="5" selected>05</option>']},
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
            r"0001_FINISHED_watkinsexamplecom_supplies_snapshot\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0001_FINISHED_watkinsexamplecom_supplies_snapshot.csv',
        'tries': {'max': 10, 'period': 1},
        'status_code': 200,
        'regexes': [
            r'2005-12-31 23:30,CI005,Wheal Rodney,,,11,net,,_L,'
            r'22,LV,nhh,no,05,803,5,0154,2,MOP Contract,'
            r'mc-22 9974 3438 105,Dynamat data,dc-22 9974 3438 105,'
            r'K87D74429,2005-10-06 00:00,,,,,2005-10-06 00:00,,false,false,'
            r'false,false,false,false,22 9974 3438 105,20,540,'
            r'PC 5-8 & HH S/S,Non half-hourlies 2007,341665,,,,,,,,,,']},

    {
        'name': "Check supplies snapshot mandatory kw",
        'path': '/reports/33?supply_id=1&date_year=2008&date_month=9&'
        'date_day=30&date_hour=23&date_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"0002_FINISHED_watkinsexamplecom_supplies_snapshot\.csv"],
        'status_code': 200, },
    {
        'path': '/downloads/'
        '0002_FINISHED_watkinsexamplecom_supplies_snapshot.csv',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r'Date,Physical Site Id,Physical Site Name,Other Site Ids,'
            r'Other Site Names,Supply Id,Source,Generator Type,GSP Group,'
            r'DNO Name,'
            r'Voltage Level,Metering Type,Mandatory HH,PC,MTC,CoP,SSC,'
            r'Number Of Registers,MOP Contract,Mop Account,DC Contract,'
            r'DC Account,Meter Serial Number,Meter Installation Date,'
            r'Latest Normal Meter Read Date,Latest Normal Meter Read Type,'
            r'Latest DC Bill Date,Latest MOP Bill Date,Supply Start Date,'
            r'Supply Finish Date,Import ACTIVE\?,'
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
            r'hh,,,,2003-08-03 00:00,,true,true,false,true,false,true,,,'
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
            'pc_id': "0",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'properties': "{}",
            'mop_contract_id': "11",
            'mop_account': "mc-22 0883 6932 301",
            'dc_contract_id': "8",
            'dc_account': "22 0883 6932 301",
            'imp_llfc_code': "570",
            'imp_mpan_core': "22 0883 6932 301",
            'imp_sc': "350",
            'imp_supplier_contract_id': "10",
            'imp_supplier_account': "01"},
        'status_code': 400,
        'regexes': [
            r"There are orphaned HH data between 2003-08-03 00:00 and "
            r"2010-08-02 23:30\."]},

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
            'pc_id': "0",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'properties': "{}",
            'mop_contract_id': "11",
            'mop_account': "mc-22 0883 6932 301",
            'dc_contract_id': "8",
            'dc_account': "22 0883 6932 301",
            'imp_llfc_code': "570",
            'imp_mpan_core': "22 0883 6932 301",
            'imp_sc': "350",
            'imp_supplier_contract_id': "10",
            'imp_supplier_account': "01"},
        'status_code': 400,
        'regexes': [
            r"There are orphaned HH data between 2003-08-03 00:30 and "
            r"ongoing\."]},

    # Test deleting of supplier contracts
    {
        'name': "Create a new supplier contract",
        'path': '/supplier_contracts/add',
        'method': 'post',
        'data': {
            'participant_id': "605",  # RWED
            'name': "GDF",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'charge_script': "",
            'properties': "{}", },
        'regexes': [
            r"/supplier_contracts/14"],
        'status_code': 303},

    {
        'name': "Now delete the contract",
        'path': '/supplier_contracts/14/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'status_code': 303},

    {
        'name': "Check that it's really gone",
        'path': '/supplier_contracts/14',
        'status_code': 404},

    # Create an DC contract
    {
        'name': "Test deleting of DC contracts",
        'path': '/dc_contracts/add',
        'method': 'post',
        'data': {
            'party_id': "1121",  # HHDC UKDC
            'name': "Siemens Contract",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00"},
        'status_code': 303,
        'regexes': [
            r"/dc_contracts/15"]},

    {
        'name': "Now delete the contract",
        'path': '/dc_contracts/15/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'status_code': 303},

    # Check that it's really gone
    {
        'path': '/dc_contracts/15',
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
        'tries': {'max': 20},
        'regexes': [
            r"0003_FINISHED_watkinsexamplecom_supply_virtual_bills_7\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0003_FINISHED_watkinsexamplecom_supply_virtual_bills_7.csv',
        'regexes': [
            r'Imp MPAN Core,Exp MPAN Core,Site Code,Site Name,'
            r'Account,From,To,,mop-net-gbp,mop-problem,,'
            r'dc-net-gbp,dc-problem,,imp-supplier-net-gbp,'
            r'imp-supplier-tlm,imp-supplier-ccl-kwh,'
            r'imp-supplier-ccl-rate,imp-supplier-ccl-gbp,'
            r'imp-supplier-data-collection-gbp,'
            r'imp-supplier-duos-availability-kva,'
            r'imp-supplier-duos-availability-days,'
            r'imp-supplier-duos-availability-rate,'
            r'imp-supplier-duos-availability-gbp,'
            r'imp-supplier-duos-excess-availability-kva,'
            r'imp-supplier-duos-excess-availability-days,'
            r'imp-supplier-duos-excess-availability-rate,'
            r'imp-supplier-duos-excess-availability-gbp,'
            r'imp-supplier-duos-day-kwh,imp-supplier-duos-day-gbp,'
            r'imp-supplier-duos-night-kwh,imp-supplier-duos-night-gbp,'
            r'imp-supplier-duos-reactive-rate,'
            r'imp-supplier-duos-reactive-gbp,'
            r'imp-supplier-duos-standing-gbp,imp-supplier-settlement-gbp,'
            r'imp-supplier-night-msp-kwh,imp-supplier-night-gsp-kwh,'
            r'imp-supplier-night-gbp,imp-supplier-other-msp-kwh,'
            r'imp-supplier-other-gsp-kwh,imp-supplier-other-gbp,'
            r'imp-supplier-summer-pk-msp-kwh,'
            r'imp-supplier-summer-pk-gsp-kwh,imp-supplier-summer-pk-gbp,'
            r'imp-supplier-winter-low-pk-msp-kwh,'
            r'imp-supplier-winter-low-pk-gsp-kwh,'
            r'imp-supplier-winter-low-pk-gbp,'
            r'imp-supplier-winter-off-pk-msp-kwh,'
            r'imp-supplier-winter-off-pk-gsp-kwh,'
            r'imp-supplier-winter-off-pk-gbp,'
            r'imp-supplier-winter-pk-msp-kwh,'
            r'imp-supplier-winter-pk-gsp-kwh,imp-supplier-winter-pk-gbp,'
            r'imp-supplier-bsuos-kwh,imp-supplier-bsuos-rate,'
            r'imp-supplier-bsuos-gbp,imp-supplier-triad-actual-1-date,'
            r'imp-supplier-triad-actual-1-msp-kw,'
            r'imp-supplier-triad-actual-1-status,'
            r'imp-supplier-triad-actual-1-laf,'
            r'imp-supplier-triad-actual-1-gsp-kw,'
            r'imp-supplier-triad-actual-2-date,'
            r'imp-supplier-triad-actual-2-msp-kw,'
            r'imp-supplier-triad-actual-2-status,'
            r'imp-supplier-triad-actual-2-laf,'
            r'imp-supplier-triad-actual-2-gsp-kw,'
            r'imp-supplier-triad-actual-3-date,'
            r'imp-supplier-triad-actual-3-msp-kw,'
            r'imp-supplier-triad-actual-3-status,'
            r'imp-supplier-triad-actual-3-laf,'
            r'imp-supplier-triad-actual-3-gsp-kw,'
            r'imp-supplier-triad-actual-gsp-kw,'
            r'imp-supplier-triad-actual-rate,'
            r'imp-supplier-triad-actual-gbp,'
            r'imp-supplier-triad-estimate-1-date,'
            r'imp-supplier-triad-estimate-1-msp-kw,'
            r'imp-supplier-triad-estimate-1-status,'
            r'imp-supplier-triad-estimate-1-laf,'
            r'imp-supplier-triad-estimate-1-gsp-kw,'
            r'imp-supplier-triad-estimate-2-date,'
            r'imp-supplier-triad-estimate-2-msp-kw,'
            r'imp-supplier-triad-estimate-2-status,'
            r'imp-supplier-triad-estimate-2-laf,'
            r'imp-supplier-triad-estimate-2-gsp-kw,'
            r'imp-supplier-triad-estimate-3-date,'
            r'imp-supplier-triad-estimate-3-msp-kw,'
            r'imp-supplier-triad-estimate-3-status,'
            r'imp-supplier-triad-estimate-3-laf,'
            r'imp-supplier-triad-estimate-3-gsp-kw,'
            r'imp-supplier-triad-estimate-gsp-kw,'
            r'imp-supplier-triad-estimate-rate,'
            r'imp-supplier-triad-estimate-months,'
            r'imp-supplier-triad-estimate-gbp,'
            r'imp-supplier-triad-all-estimates-months,'
            r'imp-supplier-triad-all-estimates-gbp'
            r',imp-supplier-problem',
            r'22 4862 4512 332,,CH023,Treglisson,11640077,'
            r'2009-03-01 00:00,2009-03-31 23:30,,10,,,10,,,'
            r'10614.7229832\d*,,148925.71000000002,0.00456 | 0.0047,'
            r'679.10640\d*,5.89,230,31,0.0368,262.384,'
            r'169.72000000000003,31,0.0368,193.616576,'
            r'105487.43999999983,770.0583120000015,43438.26999999999,'
            r'112.946888\d*,0.0033,0.0,,88,43401.25000000001,'
            r'46092.12750000003,288.79483406400016,54364.72999999998,'
            r'57735.34326,361.746566729856,0,0,0.0,0,0,0.0,'
            r'51159.730000000054,54331.63325999999,340.4202813538559,'
            r'0,0,0.0,160047.0212\d*,,147.22086540\d*,'
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

    {
        'name': "Try looking at it using the TRIAD report",
        'path': '/reports/41?supply_id=4&year=2010',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"0004_FINISHED_watkinsexamplecom_supplies_triad\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0004_FINISHED_watkinsexamplecom_supplies_triad.csv',
        'status_code': 200,
        'regexes': [
            r'CI005,Wheal Rodney,1,net,,22 6158 2968 220,'
            r'2010-01-07 17:00,0,X,1.058,0.0,2010-01-25 17:00,0,'
            r'X,1.058,0.0,2009-12-15 17:00,0,X,1.058,0.0,'
            r'0.0,25.631634000000002,0.0,22 3479 7618 470,'
            r'2010-01-07 17:00,0,X,1.058,0.0,2010-01-25 17:00,0,'
            r'X,1.058,0.0,2009-12-15 17:00,0,X,1.058,0.0,'
            r'0.0,25.631634000000002,0.0']},
    {
        'name': "Check we can delete a rate script (when it's not the only "
        "one). Supplier contract 33.",
        'path': '/supplier_rate_scripts/30/edit',
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
        'status_code': 200,
        'regexes': [
            r'<title>0.524 kW at 2008-07-06 00:00</title>']},
    {
        'name': "Try generation graph report.",
        'path': '/sites/7/gen_graph?finish_year=2008&finish_month=7&months=1',
        'status_code': 200},

    {
        'name': "Try 'Site HH bulk figures' report.",
        'path': '/reports/29?site_id=5&type=used&months=1&finish_year=2008&'
        'finish_month=01',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"0005_FINISHED_watkinsexamplecom_site_hh_data_200801010000\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0005_FINISHED_watkinsexamplecom_site_hh_data_200801010000.csv',
        'regexes': [
            r"CH023,used,2008-01-01,3.77"],
        'status_code': 200},

    {
        'name': "Try DC virtual bills.",
        'path': '/reports/81?dc_contract_id=8&months=1&end_year=2008&'
        'end_month=7',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"0006_FINISHED_watkinsexamplecom_dc_virtual_bills\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0006_FINISHED_watkinsexamplecom_dc_virtual_bills.csv',
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
            'gsp_group_id': "10"},
        'regexes': [
            r"/supplies/1"],
        'status_code': 303},
    {
        'path': '/reports/183?start_year=2008&start_month=07&start_day=1&'
        'finish_year=2008&finish_month=07&finish_day=31',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"0007_FINISHED_watkinsexamplecom_supplies_hh_data_"
            r"200807312330\.zip"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0007_FINISHED_watkinsexamplecom_supplies_hh_data_200807312330.zip',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r'CH017,Parbola,,sub,,2008-07-01 00:00,'
            r'2008-07-31 23:30,used,2008-07-01,0,0,0,0,0,0,0,0,0,0,0,0,'
            r'0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'
            r'0,0,0,0']},

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
            r"0008_FINISHED_watkinsexamplecom_supplies_duration\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0008_FINISHED_watkinsexamplecom_supplies_duration.csv',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r'2003-08-03 00:00,,7,1,net,,CH023,Treglisson,,2009-03-01 00:00,'
            r'2009-03-31 23:30,00,845,5,,\{\},MOP Contract,'
            r'mc-22 4862 4512 332,'
            r'HH contract,01,0,hh,2003-08-03 00:00,,540,'
            r'22 4862 4512 332,230,Half-hourlies 2007,148925.71000000002,0,'
            r'158159.10402,399.72,2009-03-13 08:00,None,0,,,,,0,0,0,0,,'
            r'None,'
        ]
    },

    {
        'name': "View DNOs",
        'path': '/dnos',
        'status_code': 200,
        'regexes': [
            r'option']},

    {
        'name': "View a DNO rate script",
        'path': '/dnos/160/rate_scripts/200001010000',
        'status_code': 200},

    {
        'name': "Supplies Monthly Duration",
        'path': '/reports/247?site_id=5&months=1&finish_year=2009&'
        'finish_month=03&compression=False',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 40, 'period': 1},
        'regexes': [
            r'0009_FINISHED_watkinsexamplecom_monthly_'
            r'duration_20090301_0000_for_1_months_site_CH023\.ods'],
        'status_code': 200},
    {
        'name': "CSV Sites TRIAD",
        'path': '/reports/181?site_id=3&year=2010',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"0010_FINISHED_watkinsexamplecom_output\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0010_FINISHED_watkinsexamplecom_output.csv',
        'regexes': [
            r'Site Code,',
            r'CI005,Wheal Rodney,2010-01-07 17:00,'],
        'status_code': 200},

    {
        'name': "Monthly Duration - no virtual bill function",
        'path': '/reports/247?site_id=4&months=1&finish_year=2009&'
        'finish_month=04&compression=False',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'regexes': [
            r'0011_FINISHED_watkinsexamplecom_monthly_'
            r'duration_20090401_0000_for_1_months_site_CI017\.ods'],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0011_FINISHED_watkinsexamplecom_monthly_'
        'duration_20090401_0000_for_1_months_site_CI017.ods',
        'status_code': 200,
        'regexes': [
            r'<table:table table:name="Era Level">\s*'
            r'<table:table-column/>\s*'
            r'<table:table-row>\s*'
            r'<table:table-cell office:string-value="creation-date" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-mpan-core" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-contract" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="exp-mpan-core" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="exp-supplier-contract" '
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
            r'<table:table-cell office:string-value="imp-supplier-00001-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00001-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00001-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00039-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00039-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00039-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00080-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00080-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00080-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00148-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00148-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00148-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00221-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00221-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00221-gbp" '
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
            r'</table:table-row>',

            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:string-value="22 6354 2983 570" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Half-hourlies 2007" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
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
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="9"/>\s*'
            r'<table:table-cell office:value="2894.59" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="6"/>\s*'
            r'<table:table-cell office:value="2894.59" '
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
            r'<table:table-cell office:value="2874.59" '
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
            r'<table:table-cell office:value="0.039" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="2780.7\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="31" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
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
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
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
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
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
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
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
            r'<table:table-cell table:number-columns-repeated="15"/>\s*'
            r'</table:table-row>\s*'
            r'</table:table>\s*'
            r'</office:spreadsheet>',

            r"The supplier contract Non half-hourlies 2007 "
            r"doesn't have the virtual_bill\(\) function."]},

    {
        'name': "Update the supplier contract",
        'path': '/supplier_contracts/12/edit',
        'method': 'post',
        'data': {
            'party_id': "28",  # BIZZ
            'name': "Half-hourlies 2013",
            'charge_script': """
from operator import itemgetter
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_
import chellow.duos
import chellow.ccl
import chellow.triad
import chellow.tlms
import chellow.rcrc
import chellow.bsuos
import chellow.aahedc
import chellow.ro
from chellow.utils import utc_datetime
import chellow.computer


def virtual_bill_titles():
    return [
        'net-gbp', 'tlm', 'ccl-kwh', 'ccl-rate', 'ccl-gbp',
        'data-collection-gbp', 'duos-availability-kva',
        'duos-availability-days', 'duos-availability-rate',
        'duos-availability-gbp', 'duos-excess-availability-kva',
        'duos-excess-availability-days', 'duos-excess-availability-rate',
        'duos-excess-availability-gbp','duos-green-kwh', 'duos-green-rate',
        'duos-green-gbp', 'duos-amber-kwh', 'duos-amber-rate',
        'duos-amber-gbp', 'duos-red-kwh', 'duos-red-rate', 'duos-red-gbp',
        'duos-reactive-kvarh', 'duos-reactive-rate', 'duos-reactive-gbp',
        'duos-fixed-days', 'duos-fixed-rate', 'duos-fixed-gbp',
        'settlement-gbp', 'aahedc-gsp-kwh', 'aahedc-rate', 'aahedc-gbp',
        'rcrc-kwh', 'rcrc-rate', 'rcrc-gbp', 'night-msp-kwh', 'night-gsp-kwh',
        'night-gbp', 'other-msp-kwh', 'other-gsp-kwh', 'other-gbp',
        'summer-pk-msp-kwh', 'summer-pk-gsp-kwh', 'summer-pk-gbp',
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
    chellow.triad.hh(supply_source)
    chellow.triad.bill(supply_source)
    chellow.tlms.hh(supply_source)
    chellow.bsuos.hh(supply_source)

    for datum in supply_source.hh_data:
        hh_start = datum['start-date']
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
        bill['bsuos-kwh'] += datum['nbp-kwh']
        bill['bsuos-gbp'] += datum['bsuos-gbp']

        if datum['utc-is-month-end']:
            month_start = utc_datetime(hh_start.year, hh_start.month, 1)
            ccl_kwh = 0
            ccl_gbp = 0
            for ds in supply_source.get_data_sources(month_start, hh_start):
                chellow.ccl.ccl(ds)
                for h in ds.hh_data:
                    ccl_kwh += h['ccl-kwh']
                    ccl_gbp += h['ccl-gbp']

            if ccl_kwh > 999:
                bill['ccl-kwh'] += ccl_kwh
                bill['ccl-gbp'] += ccl_gbp

    chellow.aahedc.hh(supply_source)

    rates = supply_source.hh_rate(
        db_id, supply_source.finish_date)['gsp_gbp_per_kwh']
    for slot_name in slot_names:
        slot_keys = slots[slot_name]
        bill[slot_keys['gbp']] = bill[slot_keys['gsp-kwh']] * float(
            rates[slot_name])

    for rate_name, rate_set in supply_source.supplier_rate_sets.items():
        bill[rate_name] = rate_set

    bill['net-gbp'] = sum(v for k, v in bill.items() if k[-4:] == '-gbp')


def virtual_bill(supply_source):
    chellow.duos.duos_vb(supply_source)
    chellow.triad.hh(supply_source)
    chellow.triad.bill(supply_source)
    chellow.tlms.hh(supply_source)
    chellow.rcrc.hh(supply_source)
    chellow.bsuos.hh(supply_source)
    chellow.aahedc.hh(supply_source)

    bill = supply_source.supplier_bill
    supply_source.is_green = False

    for hh in supply_source.hh_data:
        hh_start = hh['start-date']
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
        rates = supply_source.hh_rate(db_id, hh_start)['gsp_gbp_per_kwh']
        bill[slot_keys['gbp']] += hh['gsp-kwh'] * float(rates[slot_name])

        bill['bsuos-kwh'] += hh['nbp-kwh']
        bill['bsuos-gbp'] += hh['bsuos-gbp']

        if hh['utc-is-month-end']:
            month_start = utc_datetime(hh_start.year, hh_start.month, 1)
            ccl_kwh = 0
            ccl_gbp = 0
            for ds in supply_source.get_data_sources(month_start, hh_start):
                chellow.ccl.ccl(ds)
                for h in ds.hh_data:
                    ccl_kwh += h['ccl-kwh']
                    ccl_gbp += h['ccl-gbp']

            if ccl_kwh > 999:
                bill['ccl-kwh'] += ccl_kwh
                bill['ccl-gbp'] += ccl_gbp

    bill['data-collection-gbp'] += 5.89
    bill['settlement-gbp'] += 88

    for rate_name, rate_set in supply_source.supplier_rate_sets.items():
        bill[rate_name] = rate_set

    bill['net-gbp'] = sum(v for k, v in bill.items() if k[-4:] == '-gbp')

""",
            'properties': "{}"},
        'status_code': 303,
        'regexes': [
            r'/supplier_contracts/12']},
    {
        'path': '/supplier_contracts/13/edit',
        'method': 'post',
        'data': {
            r'name': "Non half-hourlies 2007",
            r'party_id': "759",  # HYDE
            r'charge_script': """
import chellow.ccl
import chellow.computer
from chellow.utils import utc_datetime, HH


def virtual_bill_titles():
    return [
        'ccl-kwh', 'ccl-rate', 'ccl-gbp', 'net-gbp', 'vat-gbp', 'gross-gbp',
        'sum-msp-kwh', 'problem']

def virtual_bill(supply_source):
    bill = supply_source.supplier_bill
    rate_sets = supply_source.supplier_rate_sets

    if supply_source.supply.find_era_at(
            supply_source.sess, supply_source.finish_date + HH) is None:
        sup_end = supply_source.finish_date
    else:
        sup_end = None

    for hh in supply_source.hh_data:
        hh_start = hh['start-date']
        bill['sum-msp-kwh'] += hh['msp-kwh']

        if hh['utc-is-month-end'] or hh_start == sup_end:
            month_start = utc_datetime(hh_start.year, hh_start.month, 1)
            ccl_kwh = 0
            ccl_gbp = 0
            for ds in supply_source.get_data_sources(month_start, hh_start):
                chellow.ccl.ccl(ds)
                for h in ds.hh_data:
                    ccl_kwh += h['ccl-kwh']
                    ccl_gbp += h['ccl-gbp']
                    rate_sets['ccl-rate'].add(h['ccl-rate'])


            if ccl_kwh > 999:
                bill['ccl-kwh'] += ccl_kwh
                bill['ccl-gbp'] += ccl_gbp

    for rate_name, rate_set in supply_source.supplier_rate_sets.items():
        bill[rate_name] = rate_set
    bill.update(
        {
            'net-gbp': 0.0, 'vat-gbp':0.0, 'gross-gbp': 0.0,})
""",
            'properties': "{}"},
        'status_code': 303},
    {
        'name': "Site In View World",
        'path': '/sites/3',
        'status_code': 200,
        'regexes': [
            r'<a\s*'
            r'href="/supplies/2"\s*'
            r'>view</a>',
            r'<a href="https://maps.google.com/maps\?q=CI005">Google Maps</a>',
            r'<option value="imp_net">Imported</option>',
            r'<form action="/reports/csv_site_hh_data">\s*'
            r'<fieldset>\s*'
            r'<input type="hidden" name="site_id" value="3">\s*'
            r'<legend>HH Data: HH Per Row Format</legend>',
            r'<fieldset>\s*'
            r'<input type="hidden" name="site_id" value="3">\s*'
            r'<legend>Monthly Duration</legend>']},

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
            'mop_contract_id': "11",
            'mop_account': "mc-22 9974 3438 105",
            'dc_contract_id': "8",
            'dc_account': "dc-22 9974 3438 105",
            'msn': "K87D74429",
            'pc_id': "5",
            'mtc_code': "803",
            'cop_id': "5",
            'ssc_code': "0154",
            'properties': "{}",
            'imp_llfc_code': "540",
            'imp_mpan_core': "22 9974 3438 105",
            'imp_sc': "20",
            'imp_supplier_contract_id': "13",
            'imp_supplier_account': "SA341665"},
        'status_code': 303},
    {
        'path': '/sites/3',
        'status_code': 200,
        'regexes': [
            r'<td>\s*'
            r'<a\s*'
            r'href="/supplies/11"\s*'
            r'>view</a>\s*'
            r'</td>\s*<td>3</td>\s*<td>2005-10-03 00:00</td>\s*<td>\s*'
            r'2010-04-13 23:30\s*</td>']},

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
            'gsp_group_id': "7",
            'pc_id': "0",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'properties': "{}",
            'mop_contract_id': "11",
            'mop_account': "mc-22 6354 2983 570",
            'dc_contract_id': "9",
            'dc_account': "01",
            'imp_llfc_code': "453",
            'imp_mpan_core': "20 6354 2983 571",
            'imp_sc': "2300",
            'imp_supplier_contract_id': "10",
            'imp_supplier_account': "141 5532",
            'insert_electricity': "insert_electricity"},
        'regexes': [
            r"/supplies/12"],
        'status_code': 303},

    {
        'name': "Add import related ACTIVE channel. Supply 12",
        'path': '/eras/16/add_channel',
        'method': 'post',
        'data': {
            'imp_related': "true",
            'channel_type': "ACTIVE"},
        'regexes': [
            r"/channels/42"],
        'status_code': 303},

    {
        'path': '/dc_contracts/9/hh_imports',
        'name': "Try out simple.csv hh import format.",
        'method': 'post',
        'files': {'import_file': 'test/hh_dyn.simple.csv'},
        'status_code': 303,
        'regexes': [
            r"/dc_contracts/9/hh_imports/0"]},
    {
        'path': '/dc_contracts/9/hh_imports/0',
        'tries': {},
        'regexes': [
            r"The import has completed.*successfully."],
        'status_code': 200},

    {
        'name': "Try out simple.csv hh import format.",
        'path': '/dc_contracts/8/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh_con.simple.csv'},
        'status_code': 303,
        'regexes': [
            r"/dc_contracts/8/hh_imports/13"]},
    {
        'path': '/dc_contracts/8/hh_imports/13',
        'tries': {},
        'regexes': [
            r"The import has completed.*successfully."],
        'status_code': 200},

    {
        'name': "that the first datum has been correctly loaded in",
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
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"0012_FINISHED_watkinsexamplecom_supply_virtual_bills_12\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0012_FINISHED_watkinsexamplecom_supply_virtual_bills_12.csv',
        'regexes': [
            r'Imp MPAN Core,Exp MPAN Core,Site Code,Site Name,'
            r'Account,From,To,,mop-net-gbp,mop-problem,,'
            r'dc-net-gbp,dc-problem,,imp-supplier-net-gbp,'
            r'imp-supplier-tlm,imp-supplier-ccl-kwh,'
            r'imp-supplier-ccl-rate,imp-supplier-ccl-gbp,'
            r'imp-supplier-data-collection-gbp,'
            r'imp-supplier-duos-availability-kva,'
            r'imp-supplier-duos-availability-days,'
            r'imp-supplier-duos-availability-rate,'
            r'imp-supplier-duos-availability-gbp,'
            r'imp-supplier-duos-excess-availability-kva,'
            r'imp-supplier-duos-excess-availability-days,'
            r'imp-supplier-duos-excess-availability-rate,'
            r'imp-supplier-duos-excess-availability-gbp,'
            r'imp-supplier-duos-day-kwh,imp-supplier-duos-day-gbp,'
            r'imp-supplier-duos-night-kwh,imp-supplier-duos-night-gbp,'
            r'imp-supplier-duos-reactive-rate,'
            r'imp-supplier-duos-reactive-gbp,'
            r'imp-supplier-duos-standing-gbp,imp-supplier-settlement-gbp,'
            r'imp-supplier-night-msp-kwh,imp-supplier-night-gsp-kwh,'
            r'imp-supplier-night-gbp,imp-supplier-other-msp-kwh,'
            r'imp-supplier-other-gsp-kwh,imp-supplier-other-gbp,'
            r'imp-supplier-summer-pk-msp-kwh,'
            r'imp-supplier-summer-pk-gsp-kwh,imp-supplier-summer-pk-gbp,'
            r'imp-supplier-winter-low-pk-msp-kwh,'
            r'imp-supplier-winter-low-pk-gsp-kwh,'
            r'imp-supplier-winter-low-pk-gbp,'
            r'imp-supplier-winter-off-pk-msp-kwh,'
            r'imp-supplier-winter-off-pk-gsp-kwh,'
            r'imp-supplier-winter-off-pk-gbp,'
            r'imp-supplier-winter-pk-msp-kwh,'
            r'imp-supplier-winter-pk-gsp-kwh,imp-supplier-winter-pk-gbp,'
            r'imp-supplier-bsuos-kwh,imp-supplier-bsuos-rate,'
            r'imp-supplier-bsuos-gbp,imp-supplier-triad-actual-1-date,'
            r'imp-supplier-triad-actual-1-msp-kw,'
            r'imp-supplier-triad-actual-1-status,'
            r'imp-supplier-triad-actual-1-laf,'
            r'imp-supplier-triad-actual-1-gsp-kw,'
            r'imp-supplier-triad-actual-2-date,'
            r'imp-supplier-triad-actual-2-msp-kw,'
            r'imp-supplier-triad-actual-2-status,'
            r'imp-supplier-triad-actual-2-laf,'
            r'imp-supplier-triad-actual-2-gsp-kw,'
            r'imp-supplier-triad-actual-3-date,'
            r'imp-supplier-triad-actual-3-msp-kw,'
            r'imp-supplier-triad-actual-3-status,'
            r'imp-supplier-triad-actual-3-laf,'
            r'imp-supplier-triad-actual-3-gsp-kw,'
            r'imp-supplier-triad-actual-gsp-kw,'
            r'imp-supplier-triad-actual-rate,'
            r'imp-supplier-triad-actual-gbp,'
            r'imp-supplier-triad-estimate-1-date,'
            r'imp-supplier-triad-estimate-1-msp-kw,'
            r'imp-supplier-triad-estimate-1-status,'
            r'imp-supplier-triad-estimate-1-laf,'
            r'imp-supplier-triad-estimate-1-gsp-kw,'
            r'imp-supplier-triad-estimate-2-date,'
            r'imp-supplier-triad-estimate-2-msp-kw,'
            r'imp-supplier-triad-estimate-2-status,'
            r'imp-supplier-triad-estimate-2-laf,'
            r'imp-supplier-triad-estimate-2-gsp-kw,'
            r'imp-supplier-triad-estimate-3-date,'
            r'imp-supplier-triad-estimate-3-msp-kw,'
            r'imp-supplier-triad-estimate-3-status,'
            r'imp-supplier-triad-estimate-3-laf,'
            r'imp-supplier-triad-estimate-3-gsp-kw,'
            r'imp-supplier-triad-estimate-gsp-kw,'
            r'imp-supplier-triad-estimate-rate,'
            r'imp-supplier-triad-estimate-months,'
            r'imp-supplier-triad-estimate-gbp,'
            r'imp-supplier-triad-all-estimates-months,'
            r'imp-supplier-triad-all-estimates-gbp,'
            r'imp-supplier-problem',
            r'20 6354 2983 571,,CI004,Lower Treave,141 5532,'
            r'2009-03-01 00:00,2009-03-31 23:30,,10,,,7,,,'
            r'2274.51875\d*,,,0.00456 | 0.0047,,5.89,2300,,,'
            r'2165.0,0,,,,0,0.0,86.9732,0.10262837600000001,'
            r',,14.91,88,86.9732,93.49619,0.585809728064,0,'
            r'0.0,0.0,0,0,0.0,0,0,0.0,0,0.0,0.0,0,0,'
            r'0.0,94.83563511\d*,,0.0303161074779\d*,'
            r'2009-01-06 17:00,0,X,1.095,0.0,2008-12-01 17:00,0,'
            r'X,1.095,0.0,2008-12-15 17:00,0,X,1.095,0.0,'
            r'0.0,22.19481,0.0,2007-12-17 17:00,0,X,1.095,0.0,'
            r'2008-01-03 17:00,0,X,1.079,0.0,2007-11-26 17:00,0,'
            r'X,1.095,0.0,0.0,22.19481,1,0.0,12,0.0,'],
        'status_code': 200},

    {
        'name': "DNO rate script contains a double LLFC 453,470",
        'path': '/reports/291?supply_id=12&start_year=2009&start_month=6&'
        'start_day=01&start_hour=00&start_minute=0&finish_year=2009&'
        'finish_month=06&finish_day=30&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'regexes': [
            r"0013_FINISHED_watkinsexamplecom_supply_virtual_bills_12\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0013_FINISHED_watkinsexamplecom_supply_virtual_bills_12.csv',
        'regexes': [
            r'20 6354 2983 571,,CI004,Lower Treave,141 5532,'
            r'2009-06-01 00:00,2009-06-30 23:30,'],
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
            'participant_id': "70",  # COOP
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
        bill[rate_name] = rate_set

    for h in supply_source.hh_data:
        msp_kwh = h['msp-kwh']
        bill['sum-msp-kwh'] += msp_kwh
        bill['net-gbp'] += msp_kwh * 0.1
        if h['utc-is-month-end']:
            pass
""",
            'properties': "{}"},
        'regexes': [
            r"/supplier_contracts/16"],
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
            'mop_contract_id': "11",
            'mop_account': "mc-22 1065 3921 534",
            'dc_contract_id': "8",
            'dc_account': "dc-22 1065 3921 534",
            'msn': "I02D89150",
            'pc_id': "3",
            'mtc_code': "801",
            'cop_id': "6",
            'ssc_code': "0393",
            'properties': "{}",
            'imp_llfc_code': "110",
            'imp_mpan_core': "22 1065 3921 534",
            'imp_sc': "30",
            'imp_supplier_contract_id': "16",
            'imp_supplier_account': "SA342376000"},
        'status_code': 303},

    # Create a new batch
    {
        'path': '/supplier_contracts/16/add_batch',
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

    # Supplier contract 42.
    {
        'path': '/supplier_bill_imports/3',
        'tries': {},
        'regexes': [
            r'<th>Reference</th>\s*<th>Account</th>\s*<th>Bill Type</th>\s*'
            r'<th>MPAN Cores</th>\s*<th>Issue Date</th>\s*'
            r'<th>Start Date</th>\s*'
            r"<th>Finish Date</th>\s*<th>kWh</th>\s*<th>Net</th>\s*"
            r"<th>VAT</th>\s*<th>Gross</th>\s*<th>R1 MPAN</th>\s*"
            r"<th>R1 Meter Serial Number</th>\s*<th>R1 Coefficient</th>\s*"
            r"<th>R1 Units</th>\s*<th>R1 TPR</th>\s*"
            r"<th>R1 Previous Read Date</th>\s*"
            r"<th>R1 Previous Read Value</th>\s*"
            r"<th>R1 Previous Read Type</th>\s*"
            r"<th>R1 Present Read Date</th>\s*"
            r"<th>R1 Present Read Value</th>\s*"
            r"<th>R1 Present Read Type</th>\s*"
            r"<th>Breakdown</th>",
            r"<td>3423760005</td>\s*<td>SA342376000</td>\s*<td>N</td>\s*"
            r'<td>2210653921534</td>\s*'
            r"<td>2010-05-12 00:00</td>\s*<td>2010-01-19 00:00</td>\s*"
            r"<td>2010-04-20 23:30</td>\s*<td>253</td>\s*<td>36.16</td>\s*"
            r"<td>1.80</td>\s*<td>37.96</td>\s*"
            r"<td>03 801 110 22 1065 3921 534</td>\s*<td>K87D74429</td>\s*"
            r"<td>1</td>\s*<td>kWh</td>\s*<td>00001</td>\s*"
            r"<td>2010-01-18 23:30</td>\s*<td>16963</td>\s*<td>E</td>\s*"
            r"<td>2010-04-20 23:30</td>\s*<td>17216</td>\s*<td>E</td>",
            r"All the bills have been successfully loaded and attached to the "
            r"batch\."],

        'status_code': 200},

    {

        'name': "Test the supplier batch checking",
        'path': '/reports/111?batch_id=5',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 40, 'period': 1},
        'regexes': [
            r"0014_FINISHED_watkinsexamplecom_bill_check\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/0014_FINISHED_watkinsexamplecom_bill_check.csv',
        'regexes': [
            r'batch,bill-reference,bill-type,bill-kwh,bill-net-gbp,'
            r'bill-vat-gbp,bill-start-date,bill-finish-date,imp-mpan-core,'
            r'exp-mpan-core,site-code,site-name,covered-from,covered-to,'
            r'covered-bills,metered-kwh,covered-net-gbp,virtual-net-gbp,'
            r'difference-net-gbp,covered-sum-msp-kwh,virtual-sum-msp-kwh,'
            r'covered-problem,virtual-problem',
            r'07-008,3423760005,N,253,36.16,1.80,'
            r'2010-01-19 00:00,2010-04-20 23:30,22 1065 3921 534,,'
            r'CI017,Roselands,2010-01-19 00:00,2010-04-20 23:30,10,'
            r'0.0,36.16,0,36.16,253.0,253.0\d*,,'],
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
            'gsp_group_id': "2",
            'mop_contract_id': "11",
            'mop_account': "mc-22 9879 0084 358",
            'dc_contract_id': "8",
            'dc_account': "dc-22 9879 0084 358",
            'pc_id': "0",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'properties': "{}",
            'imp_mpan_core': "22 9879 0084 358",
            'imp_llfc_code': "540",
            'imp_sc': "700",
            'imp_supplier_contract_id': "10",
            'imp_supplier_account': "d",
            'insert_electricity': "Insert"},
        'regexes': [
            r"/supplies/13"],
        'status_code': 303},

    {
        'name': "Check that the generator type 'chp' has been ignored.",
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
        'path': '/supplier_contracts/10/add_batch',
        'method': 'post',
        'data': {
            'reference': "008",
            'description': "GDF CSV batch"},
        'status_code': 303},

    {
        'name': "Supplier contract 15",
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
        'name': "Supplier contract 10, batch 6",
        'path': '/supplier_bill_imports/4',
        'tries': {},
        'regexes': [
            r"<th>Reference</th>\s*<th>Account</th>\s*<th>Bill Type</th>\s*"
            r'<th>MPAN Cores</th>\s*<th>Issue Date</th>\s*'
            r'<th>Start Date</th>\s*'
            r"<th>Finish Date</th>\s*<th>kWh</th>\s*<th>Net</th>\s*"
            r"<th>VAT</th>\s*<th>Gross</th>\s*<th>Breakdown</th>",
            r"<td>KUH773</td>\s*<td>02</td>\s*<td>N</td>\s*<td></td>\s*"
            r"<td>2010-06-09 00:00</td>\s*<td>2010-05-01 00:00</td>\s*"
            r"<td>2010-05-31 23:30</td>\s*<td>32124.5</td>\s*"
            r'<td>2219.41</td>\s*<td>388.40</td>\s*<td>2607.81</td>\s*'
            r'<td>\[\(&#39;aahedc-gbp&#39;, Decimal\(&#39;5.29&#39;\)\),',
            r"All the bills have been successfully loaded and attached to "
            r"the batch\."],
        'status_code': 200},

    {
        'name': "Check the bill appears correctly in batch view",
        'path': '/supplier_batches/6',
        'regexes': [
            r'\[<a href="/supplier_batches/6/edit">edit</a>\]',
            r"<td>2010-06-09 00:00</td>\s*<td>2010-05-01 00:00</td>\s*"
            r"<td>2010-05-31 23:30</td>\s*<td>32124.5</td>\s*"
            r"<td>2219.41</td>\s*<td>388.40</td>\s*<td>2607.81</td>",
            r'<a\s*href="/reports/111\?batch_id=6"\s*>Check Bills</a>'],
        'status_code': 200},
    {
        'name': "Test displaced virtual bill.",
        'path': '/reports/247?site_id=1&months=1&finish_year=2010&'
        'finish_month=06&compression=False',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 60, 'period': 1},
        'regexes': [
            r'0015_FINISHED_watkinsexamplecom_monthly_duration_20100601_0000_'
            r'for_1_months_site_CI004\.ods'],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0015_FINISHED_watkinsexamplecom_monthly_duration_20100601_0000_for_1_'
        'months_site_CI004.ods',
        'regexes': [
            r'<table:table-row>\s*'
            r'<table:table-cell office:string-value="creation-date" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-mpan-core" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-contract" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="exp-mpan-core" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="exp-supplier-contract" '
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
            r'office:string-value='
            r'"imp-supplier-duos-excess-availability-days" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value='
            r'"imp-supplier-duos-excess-availability-rate" '
            r'office:value-type="string"/>\s*'
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
            r'<table:table-cell '
            r'office:string-value="imp-supplier-night-gbp" '
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
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-green-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-green-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-green-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-amber-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-amber-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-amber-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-red-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-red-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-red-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-reactive-kvarh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-fixed-days" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-fixed-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-fixed-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-aahedc-gsp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-aahedc-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-aahedc-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-rcrc-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-rcrc-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-rcrc-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-vat-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-gross-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-sum-msp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00001-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00001-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00001-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00080-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00080-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00080-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00148-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00148-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00148-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00221-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00221-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00221-gbp" '
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
            r'office:string-value='
            r'"exp-supplier-duos-excess-availability-days" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value='
            r'"exp-supplier-duos-excess-availability-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-duos-excess-availability-gbp" '
            r'office:value-type="string"/>\s*'
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
            r'<table:table-cell '
            r'office:string-value="exp-supplier-night-gbp" '
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
            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="Half-hourlies 2007" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:string-value="hh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="displaced" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="4"/>\s*'
            r'<table:table-cell office:string-value="CI004" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Lower Treave" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:date-value="2010-06-30T23:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="15"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell table:number-columns-repeated="7"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0047" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="18"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="18"/>\s*'
            r'<table:table-cell office:date-value="2010-01-07T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="E" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.078" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:date-value="2010-01-25T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="E" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.078" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:date-value="2009-12-15T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="E" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.078" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
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
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.00147" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.16146" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="25"/>\s*'
            r'</table:table-row>\s*'],
        'status_code': 200},

    {
        'name': "Try a 12 month run",
        'path': '/reports/247?site_id=1&months=12&finish_year=2011&'
        'finish_month=06&compression=False',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 210, 'period': 1},
        'regexes': [
            r'0016_FINISHED_watkinsexamplecom_monthly_duration_20100701_0000_'
            r'for_12_months_site_CI004\.ods'],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0016_FINISHED_watkinsexamplecom_monthly_duration_20100701_0000_for_'
        '12_months_site_CI004.ods',
        'regexes': [
            r'<table:table-cell office:date-value="2011-06-30T23:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>'],
        'status_code': 200},

    {
        'name': "Test bulk ignore.",
        'path': '/dc_contracts/9/edit',
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
        'name': "Check a contract virtual bill that crosses an era boundary "
        "comes out correctly.",
        'path': '/reports/291?supply_id=11&start_year=2010&start_month=04&'
        'start_day=01&start_hour=00&start_minute=00&finish_year=2010&'
        'finish_month=04&finish_day=30&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"0017_FINISHED_watkinsexamplecom_supply_virtual_bills_11\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0017_FINISHED_watkinsexamplecom_supply_virtual_bills_11.csv',
        'regexes': [
            r'Imp MPAN Core,Exp MPAN Core,Site Code,Site Name,'
            r'Account,From,To,,mop-net-gbp,mop-problem,,'
            r'dc-net-gbp,dc-problem,,imp-supplier-ccl-kwh,'
            r'imp-supplier-ccl-rate,imp-supplier-ccl-gbp,imp-supplier-net-gbp,'
            r'imp-supplier-vat-gbp,imp-supplier-gross-gbp,'
            r'imp-supplier-sum-msp-kwh,imp-supplier-problem',
            r'22 9974 3438 105,,CI005,Wheal Rodney,SA341665,'
            r'2010-04-01 00:00,2010-04-13 23:30,,0,,,,,,'
            r',0.0047,,0.0,0.0,0.0,0.0,'],
        'status_code': 200},
    {
        'name': "NHH CSV import",
        'path': '/supplier_contracts/16/add_batch',
        'method': 'post',
        'data': {
            'reference': "07-002",
            'description': "nhh csv batch"},
        'status_code': 303},

    {
        'name': "Supplier contract 16",
        'path': '/supplier_bill_imports',
        'method': 'post',
        'data': {
            'supplier_batch_id': "7"},
        'files': {'import_file': 'test/bills-nhh.csv'},
        'status_code': 303,
        'regexes': [
            r"/supplier_bill_imports/5"]},

    {
        'name': "Supplier contract 16, batch 7",
        'path': '/supplier_bill_imports/5',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"All the bills have been successfully loaded and attached to "
            r"the batch\."]},

    # Supplier contract 16, batch 7, bill 10
    {
        'path': '/reads/7/edit',
        'regexes': [
            r'31</option>\s*</select>\s*<select name="present_hour">\s*'
            r'<option value="0">00</option>\s*<option value="1">01</option>\s*'
            r'<option value="2">02</option>\s*<option value="3">03</option>\s*'
            r'<option value="4">04</option>\s*<option value="5">05</option>\s*'
            r'<option value="6">06</option>\s*<option value="7">07</option>\s*'
            r'<option value="8">08</option>\s*<option value="9">09</option>\s*'
            r'<option value="10">10</option>\s*'
            r'<option value="11">11</option>\s*'
            r'<option value="12">12</option>\s*'
            r'<option value="13">13</option>\s*'
            r'<option value="14">14</option>\s*'
            r'<option value="15">15</option>\s*'
            r'<option value="16">16</option>\s*'
            r'<option value="17">17</option>\s*'
            r'<option value="18">18</option>\s*'
            r'<option value="19">19</option>\s*'
            r'<option value="20">20</option>\s*'
            r'<option value="21">21</option>\s*'
            r'<option value="22">22</option>\s*'
            r'<option value="23" selected>23</option>\s*'
            r'</select>:<select name="present_minute">\s*'
            r'<option value="0">00</option>\s*'
            r'<option value="30" selected>30</option>\s*</select>']},
    {
        'name': "Test viewers' search",
        'path': '/supplies?search_pattern=',
        'regexes': [
            r'<td>\s*'
            r'<a href="/supplies/9">supply</a>\s*'
            r'</td>\s*<td>P96C93722</td>',
            r"<td>\s*</td>\s*<td>\s*</td>\s*<td>\s*</td>\s*<td>\s*"
            r"00 845\s*581\s*22 0470 7514 535\s*</td>"],
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
            r'<a\s*'
            r'href="/sites/1"\s*'
            r'title="Lower Treave"\s*'
            r'>CI004</a>',

            # Check a link to supplier bill is correct
            r'<a href="/supplier_bills/11">View</a>',

            # Check link to supply duration is correct
            r'<form action="/reports/149">\s*<fieldset>\s*'
            r'<input type="hidden" name="supply_id"',
            r'<td rowspan="4">\s*'
            r'<a\s*'
            r'href="/pcs/0"\s*'
            r'title="Half-hourly">00</a>\s*'
            r'</td>\s*'
            r'<td rowspan="4"></td>\s*'
            r'<td rowspan="4">\s*'
            r'<a href="/mtcs/51"\s*'
            r'title="HH COP5 And Above With Comms">845</a>\s*</td>'],
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
            'mop_contract_id': "11",
            'mop_account': "mc-22 1065 3921 534",
            'dc_contract_id': "9",
            'dc_account': "dc-22 1065 3921 534",
            'msn': "I02D89150",
            'pc_id': "3",
            'mtc_code': "801",
            'cop_id': "5",
            'ssc_code': "0393",
            'properties': "{}",
            'imp_llfc_code': "110",
            'imp_mpan_core': "22 1065 3921 534",
            'imp_sc': "30",
            'imp_supplier_contract_id': "13",
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
            r'href="/read_types/4">E</a>\s*</td>\s*'
            r'<td>2007-01-17 00:00</td>\s*<td>39000\s*</td>\s*<td>\s*'
            r'<a title="Estimated"\s*'
            r'href="/read_types/4">E</a>\s*</td>'],
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

    {
        'name': "Add batch to DC contract",
        'path': '/dc_contracts/8/add_batch',
        'method': 'post',
        'data': {
            'reference': "001-7t",
            'description': "dc batch"},
        'status_code': 303,
        'regexes': [
            r"/dc_batches/8"]},

    {
        'name': "Check that it's there to edit. DC contract 35",
        'path': '/dc_batches/8/edit',
        'status_code': 200},
    {
        'name': "View DC bill imports. Contract 13",
        'path': '/dc_bill_imports?dc_batch_id=8',
        'status_code': 200,
        'regexes': [
            r'<a href="/dc_batches/8">001-7t</a>']},
    {
        'name': "Try adding bills to the DC batch. Contract 9",
        'path': '/dc_bill_imports',
        'method': 'post',
        'data': {
            'dc_batch_id': "8"},
        'files': {'import_file': 'test/dc-bill.csv'},
        'status_code': 303,
        'regexes': [
            r"/dc_bill_imports/6"]},

    {
        'name': "Contract 34 batch 8",
        'path': '/dc_bill_imports/6',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"All the bills have been successfully loaded and attached to "
            r"the batch\."]},

    {
        'name': "Add batch to MOP contract",
        'path': '/mop_contracts/11/add_batch',
        'method': 'post',
        'data': {
            'reference': "99/992",
            'description': "mop batch"},
        'status_code': 303,
        'regexes': [
            r"/mop_batches/9"]},

    {
        'name': "Check that it's there in edit mode. Contract 15",
        'path': '/mop_batches/9/edit',
        'status_code': 200,
        'regexes': [
            r'<input type="hidden" name="mop_batch_id" value="9">']},

    {
        'name': "Check confirm-delete page. Contract 'MOP Contract'",
        'path': '/mop_batches/9/edit?confirm_delete=Delete',
        'status_code': 200,
        'regexes': [
            r'<input type="hidden" name="mop_batch_id" value="9">']},
    {
        'name': "Supplier Batch: confirm-delete page.",
        'path': '/supplier_batches/6/edit?confirm_delete=Delete',
        'status_code': 200,
        'regexes': [
            r'<input type="submit" name="delete" value="Delete">']},
    {
        'name': "Check we can see it in 'view' mode. Contract 'MOP Contract'",
        'path': '/mop_batches/9',
        'status_code': 200},

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

    {
        'path': '/mop_bill_imports/7',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"All the bills have been successfully loaded and attached to "
            r"the batch\."]},
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
            'gsp_group_id': "2",
            'mop_contract_id': "11",
            'mop_account': "mc-22 9879 0084 358",
            'dc_contract_id': "8",
            'dc_account': "dc-22 9879 0084 358",
            'pc_id': "0",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'properties': "{}",
            'imp_mpan_core': "22 9879 0084 358",
            'imp_llfc_code': "",
            'imp_sc': "700",
            'imp_supplier_contract_id': "10",
            'imp_supplier_account': "d",
            'insert_electricity': "Insert"},
        'regexes': [
            r"There is no LLFC with the code &#39;&#39; associated with the "
            r"DNO 22 at the date 2010-05-26 00:00\.",
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
            'gsp_group_id': "2",
            'mop_contract_id': "11",
            'mop_account': "mc-22 9879 0084 358",
            'dc_contract_id': "8",
            'dc_account': "dc-22 9879 0084 358",
            'pc_id': "0",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'properties': "{}",
            'imp_mpan_core': "22 9879 0084 358",
            'imp_llfc_code': "570",
            'imp_sc': "",
            'imp_supplier_contract_id': "10",
            'imp_supplier_account': "d",
            'insert_electricity': "Insert"},
        'regexes': [
            r"Problem parsing the field imp_sc as an integer: invalid literal "
            r"for int\(\) with base 10: "],
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
            'gsp_group_id': "2",
            'mop_contract_id': "11",
            'mop_account': "mc-22 9879 0084 358",
            'dc_contract_id': "8",
            'dc_account': "dc-22 9879 0084 358",
            'pc_id': "0",
            'mtc_code': "",
            'cop_id': "5",
            'ssc_code': "",
            'properties': "{}",
            'imp_mpan_core': "22 9879 0084 358",
            'imp_llfc_code': "570",
            'imp_sc': "700",
            'imp_supplier_contract_id': "10",
            'imp_supplier_account': "d",
            'insert_electricity': "Insert"},
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
            'gsp_group_id': '10',
            'mop_contract_id': "11",
            'mop_account': "mc-22 9789 0534 938",
            'dc_contract_id': "8",
            'dc_account': "dc-22 9789 0534 938",
            'pc_id': "3",
            'mtc_code': "801",
            'cop_id': "5",
            'ssc_code': "393",
            'properties': "{}",
            'imp_mpan_core': "22 9789 0534 938",
            'imp_llfc_code': "110",
            'imp_sc': "0",
            'imp_supplier_contract_id': "16",
            'imp_supplier_account': "taa2",
            'insert_electricity': "Insert"},
        'regexes': [
            r"/supplies/16"],
        'status_code': 303},

    {
        'path': '/reports/247?site_id=4&months=1&finish_year=2010&'
        'finish_month=07&compression=False',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'regexes': [
            r'0018_FINISHED_watkinsexamplecom_monthly_'
            r'duration_20100701_0000_for_1_months_site_CI017\.ods'],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0018_FINISHED_watkinsexamplecom_monthly_'
        'duration_20100701_0000_for_1_months_site_CI017.ods',
        'regexes': [
            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:string-value="22 6354 2983 570" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Half-hourlies 2007" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
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
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
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
            r'<table:table-cell table:number-columns-repeated="8"/>\s*'
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
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
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
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
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
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
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
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.00147" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
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
            r'<table:table-cell table:number-columns-repeated="21"/>\s*'
            r'</table:table-row>\s*'
            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:string-value="22 1065 3921 534" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Non half-hourlies 2010" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
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
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
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
            r'<table:table-cell table:number-columns-repeated="21"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="12"/>\s*'
            r'</table:table-row>\s*'
            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:string-value="22 9789 0534 938" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Non half-hourlies 2010" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
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
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" '
            r'table:number-columns-repeated="4"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="4"/>\s*'
            r'<table:table-cell office:value="20.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="20.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
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
            r'<table:table-cell table:number-columns-repeated="21"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="12"/>\s*'
            r'</table:table-row>\s*'
            r'</table:table>'],
        'status_code': 200},
    {
        'name': "Try creating and deleting a rate script for a non-core "
        "contract (configuration).",
        'path': '/non_core_contracts/3/add_rate_script',
        'method': 'post',
        'data': {
            'start_year': "2010",
            'start_month': "05",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00",
            'insert': "Insert"},
        'regexes': [
            r"/non_core_rate_scripts/34"],
        'status_code': 303},
    {
        'path': '/non_core_rate_scripts/34/edit?delete=Delete',
        'regexes': [
            r"Are you sure you want to delete this rate script\?"],
        'status_code': 200},
    {
        'path': '/non_core_rate_scripts/34/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'status_code': 303},
    {
        'path': '/non_core_rate_scripts/34',
        'status_code': 404},
    {
        'name': "Try adding a rate script before other rate scripts.",
        'path': '/non_core_contracts/3/add_rate_script',
        'method': 'post',
        'data': {
            'start_year': "1999",
            'start_month': "04",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00",
            'insert': "Insert"},
        'regexes': [
            r"/non_core_rate_scripts/35"],
        'status_code': 303},
    {
        'path': '/non_core_rate_scripts/35/edit',
        'regexes': [
            r'<input name="finish_year" maxlength="4" size="4" value="2010">',

            # Check that the start hour of a non-core rate script is correct."
            r'<select name="start_hour">\s*'
            r'<option value="0" selected>00</option>'],
        'status_code': 200},
    {
        'path': '/non_core_rate_scripts/35/edit',
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
            'net': "0.00",
            'vat': "0.00",
            'gross': "0.00",
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
            r'<select name="start_day">\s*'
            r'<option value="1">01</option>\s*'
            r'<option value="2">02</option>\s*'
            r'<option value="3">03</option>\s*'
            r'<option value="4">04</option>\s*'
            r'<option value="5">05</option>\s*'
            r'<option value="6" selected>06</option>\s*'
            r'<option value="7">07</option>\s*'
            r'<option value="8">08</option>\s*'
            r'<option value="9">09</option>\s*'
            r'<option value="10">10</option>\s*'
            r'<option value="11">11</option>\s*'
            r'<option value="12">12</option>\s*'
            r'<option value="13">13</option>\s*'
            r'<option value="14">14</option>\s*'
            r'<option value="15">15</option>\s*'
            r'<option value="16">16</option>\s*'
            r'<option value="17">17</option>\s*'
            r'<option value="18">18</option>\s*'
            r'<option value="19">19</option>\s*'
            r'<option value="20">20</option>\s*'
            r'<option value="21">21</option>\s*'
            r'<option value="22">22</option>\s*'
            r'<option value="23">23</option>\s*'
            r'<option value="24">24</option>\s*'
            r'<option value="25">25</option>\s*'
            r'<option value="26">26</option>\s*'
            r'<option value="27">27</option>\s*'
            r'<option value="28">28</option>\s*'
            r'<option value="29">29</option>\s*'
            r'<option value="30">30</option>\s*'
            r'<option value="31">31</option>\s*'
            r'</select>\s*<select name="start_hour">\s*'
            r'<option value="0" selected>00</option>\s*'
            r'<option value="1">01</option>\s*'
            r'<option value="2">02</option>\s*'
            r'<option value="3">03</option>\s*'
            r'<option value="4">04</option>\s*'
            r'<option value="5">05</option>\s*'
            r'<option value="6">06</option>\s*'
            r'<option value="7">07</option>\s*'
            r'<option value="8">08</option>\s*'
            r'<option value="9">09</option>\s*'
            r'<option value="10">10</option>\s*'
            r'<option value="11">11</option>\s*'
            r'<option value="12">12</option>\s*'
            r'<option value="13">13</option>\s*'
            r'<option value="14">14</option>\s*'
            r'<option value="15">15</option>\s*'
            r'<option value="16">16</option>\s*'
            r'<option value="17">17</option>\s*'
            r'<option value="18">18</option>\s*'
            r'<option value="19">19</option>\s*'
            r'<option value="20">20</option>\s*'
            r'<option value="21">21</option>\s*'
            r'<option value="22">22</option>\s*'
            r'<option value="23">23</option>\s*'
            r'</select>:<select name="start_minute">\s*'
            r'<option value="0" selected>00</option>\s*'
            r'<option value="30">30</option>\s*</select>',
            r'<select name="finish_day">\s*'
            r'<option value="1">01</option>\s*'
            r'<option value="2">02</option>\s*'
            r'<option value="3">03</option>\s*'
            r'<option value="4">04</option>\s*'
            r'<option value="5">05</option>\s*'
            r'<option value="6" selected>06</option>\s*'
            r'<option value="7">07</option>\s*'
            r'<option value="8">08</option>\s*'
            r'<option value="9">09</option>\s*'
            r'<option value="10">10</option>\s*'
            r'<option value="11">11</option>\s*'
            r'<option value="12">12</option>\s*'
            r'<option value="13">13</option>\s*'
            r'<option value="14">14</option>\s*'
            r'<option value="15">15</option>\s*'
            r'<option value="16">16</option>\s*'
            r'<option value="17">17</option>\s*'
            r'<option value="18">18</option>\s*'
            r'<option value="19">19</option>\s*'
            r'<option value="20">20</option>\s*'
            r'<option value="21">21</option>\s*'
            r'<option value="22">22</option>\s*'
            r'<option value="23">23</option>\s*'
            r'<option value="24">24</option>\s*'
            r'<option value="25">25</option>\s*'
            r'<option value="26">26</option>\s*'
            r'<option value="27">27</option>\s*'
            r'<option value="28">28</option>\s*'
            r'<option value="29">29</option>\s*'
            r'<option value="30">30</option>\s*'
            r'<option value="31">31</option>\s*'
            r'</select>\s*<select name="finish_hour">\s*'
            r'<option value="0" selected>00</option>\s*'
            r'<option value="1">01</option>\s*'
            r'<option value="2">02</option>\s*'
            r'<option value="3">03</option>\s*'
            r'<option value="4">04</option>\s*'
            r'<option value="5">05</option>\s*'
            r'<option value="6">06</option>\s*'
            r'<option value="7">07</option>\s*'
            r'<option value="8">08</option>\s*'
            r'<option value="9">09</option>\s*'
            r'<option value="10">10</option>\s*'
            r'<option value="11">11</option>\s*'
            r'<option value="12">12</option>\s*'
            r'<option value="13">13</option>\s*'
            r'<option value="14">14</option>\s*'
            r'<option value="15">15</option>\s*'
            r'<option value="16">16</option>\s*'
            r'<option value="17">17</option>\s*'
            r'<option value="18">18</option>\s*'
            r'<option value="19">19</option>\s*'
            r'<option value="20">20</option>\s*'
            r'<option value="21">21</option>\s*'
            r'<option value="22">22</option>\s*'
            r'<option value="23">23</option>\s*'
            r'</select>:<select name="finish_minute">\s*'
            r'<option value="0" selected>00</option>\s*'
            r'<option value="30">30</option>\s*</select>'],
        'status_code': 200},
    {
        'name': "Check that bill with two sets of register reads gets "
        "displayed correctly.",
        'path': '/supplies/10',
        'regexes': [
            r'<td rowspan="2">\s*'
            r'<a\s*'
            r'href="/bill_types/2"\s*'
            r'title="Normal"\s*'
            r'>N</a>\s*'
            r'</td>\s*'
            r'<td style="border-right: none;">\s*'
            r'<a title="2011-02-04 23:30 I02D89150">34285</a>\s*</td>',
            r'25927</a>\s*'
            r'</td>\s*'
            r'<td style="border-left: none; text-align: right;">\s*'
            r'E\s*'
            r'</td>\s*'
            r'<td>\s*'
            r'</td>\s*'
            r'<td style="border-right: none;">\s*'
            r'</td>\s*'
            r'<td style="border-left: none; text-align: right;">\s*'
            r'</td>\s*'
            r'<td style="border-right: none;">\s*'
            r'</td>\s*'
            r'<td style="border-left: none; text-align: right;">\s*'
            r'</td>\s*'
            r'</tr>',

            # Check form action for virtual bills is correct
            r'<form action="/reports/291">',

            # Check link to TPR from outer read
            r'<td>\s*'
            r'<a href="/tprs/1">00003</a>\s*'
            r'</td>'],
        'status_code': 200},

    # Supplier contract 63
    {
        'name': "Deleting a batch with bills with register reads.",
        'path': '/supplier_batches/5/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'status_code': 303,
        'regexes': [
            r'/supplier_batches\?supplier_contract_id=16']},
    {
        'name': "Check 'insert supplier batch' page.",
        'path': '/supplier_contracts/16/add_batch',
        'regexes': [
            r'="description"']},
    {
        'name': "Viewing the insert batch page of a DC contract.",
        'path': '/dc_contracts/9/add_batch',
        'regexes': [
            r'="description"']},
    {
        'name': "Viewing a batch in view mode, when it has a custom report.",
        'path': '/non_core_contracts/3/edit',
        'method': 'post',
        'data': {
            'name': "configuration",
            'properties': """{
  "ips": {
    "127.0.0.1": "implicit-user@localhost"},
  "site_links": [
    {
      "name": "Google Maps", "href": "https://maps.google.com/maps?q="}],
  "batch_reports": [
    1],
  "elexonportal_scripting_key": "xxx"}
""", },
        'status_code': 303},

    {
        'name': "Check that we can see a MOP batch okay. Contract 47",
        'path': '/mop_batches/9',
        'regexes': [
            r"/local_reports/1/output",
            r'<a href="/mop_bill_imports\?mop_batch_id=9">Bill Imports</a>'],
        'status_code': 200},

    {
        'name': "Check that we can see a supplier batch okay. Contract 58",
        'path': '/supplier_batches/4',
        'regexes': [
            r'/local_reports/1/output\?batch_id=4'],
        'status_code': 200},
    {
        'name': "Check 'no channel' error when importing hh data.",
        'path': '/dc_contracts/8/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh-no-channel.simple.csv'},
        'status_code': 303,
        'regexes': [
            r"/dc_contracts/8/hh_imports/14"]},
    {
        'path': '/dc_contracts/8/hh_imports/14',
        'tries': {},
        'regexes': [
            r'There is no channel under the contract HH contract for the '
            r'datum \(22 4862 4512 332, '
            r'2010-02-04 20:00, REACTIVE_EXP, 30.4339, A\)\.'],
        'status_code': 200},
    {
        'name': "Check the bill import page.",
        'path': '/dc_contracts/8/hh_imports',
        'status_code': 200,
        'regexes': [
            r"/dc_contracts/8"]},

    # Can we add a new era ok?
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
            r'<a href="/dc_batches/8">001-7t'
            r'</a>\s*</td>\s*<td>00031</td>\s*<td>22 0883 6932 301</td>\s*'
            r'<td>2007-09-01 00:00</td>',
            r'<td>\s*'
            r'<a href="/mop_batches/9">99/992'
            r'</a>\s*</td>\s*<td>06</td>\s*<td>22 0883 6932 301</td>',

            # Check that MOP bill before supply start is displayed
            r'<td>\s*'
            r'<a href="/mop_batches/9">99/992'
            r'</a>\s*</td>\s*<td>08</td>\s*<td>22 0883 6932 301</td>',

            # Check that channel type is displayed
            r'<tr>\s*<td>\s*'
            r'<a href="/channels/16">ACTIVE</a>\s*'
            r'<a href="/channels/17">REACTIVE_IMP</a>\s*</td>'],
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

    {
        'name': "Edit a note",
        'path': '/supplies/2/notes/0/edit',
        'method': 'post',
        'data': {
            'is_important': "False",
            'category': "general",
            'body': "Do not hurry the sublime."},
        'status_code': 303},

    # Try importing HH data from FTP server.
    {
        'name': "Update Contract",
        'path': '/dc_contracts/8/edit',
        'method': 'post',
        'data': {
            'party_id': "116",  # DASL
            'name': "HH contract",
            'charge_script': """
def virtual_bill_titles():
    return ['net-gbp', 'problem']

def virtual_bill(supply_source):
    supply_source.dc_bill['net-gbp'] = 0
""",
            'properties': """{
  "enabled": true,
  "protocol": "ftp",
  "file_type": ".df2",
  "hostname": "localhost",
  "port": 2121,
  "username": "chellow",
  "password": "HixaNfUBOf*u",
  "directories": ["."]}
"""},
        'status_code': 303},

    {
        'name': "Check that the update worked",
        'path': '/dc_contracts/8',
        'status_code': 200,
        'regexes': [
            r'&#34;hostname&#34;: &#34;localhost&#34;,']},

    # Do an 'import now'
    {
        'name': "Do an 'import now'",
        'path': '/dc_contracts/8/auto_importer',
        'method': 'post',
        'regexes': [
            r'/dc_contracts/8/auto_importer'],
        'status_code': 303},
    {
        'name': "Check that file from FTP server has imported properly",
        'path': '/dc_contracts/8/auto_importer',
        'tries': {},
        'regexes': [
            r"Finished loading",
            r'<a href="/dc_contracts/8/auto_importer">Refresh page</a>']},
    {
        'path': '/dc_contracts/8',
        'regexes': [
            r"hh_data\.df2"]},

    {
        'name': "System price",
        'path': '/non_core_contracts/6/edit',
        'method': 'post',
        'data': {
            'name': 'system_price',
            'properties': """{
  "enabled": true,
  "url": "http://127.0.0.1:8080/elexonportal/",
  "limit": true}
"""},
        'status_code': 303},

    {
        'name': "Do an 'import now'",
        'path': '/non_core_contracts/6/auto_importer',
        'method': 'post',
        'regexes': [
            r'/non_core_contracts/6/auto_importer'],
        'status_code': 303},

    {
        'name': 'System Price',
        'path': '/non_core_contracts/6/auto_importer',
        'tries': {'max': 40, 'period': 1},
        'regexes': [
            r"Updating rate script starting at 2005-01-01 00:00\."],
        'status_code': 200},

    {
        'name': 'System Price Feb',
        'path': '/non_core_contracts/6/auto_importer',
        'method': 'post',
        'data': {
            'name': 'now'},
        'status_code': 303},
    {
        'name': 'System Price',
        'path': '/non_core_contracts/6/auto_importer',
        'tries': {'max': 40, 'period': 1},
        'regexes': [
            r"Updating rate script starting at 2005-02-01 00:00\."],
        'status_code': 200},
    {
        'name': 'System Price March',
        'path': '/non_core_contracts/6/auto_importer',
        'method': 'post',
        'data': {
            'name': 'now'},
        'status_code': 303},
    {
        'name': 'System Price',
        'path': '/non_core_contracts/6/auto_importer',
        'tries': {'max': 40, 'period': 1},
        'regexes': [
            r"Updating rate script starting at 2005-03-01 00:00\."],
        'status_code': 200},
    {
        'name': 'System Price April',
        'path': '/non_core_contracts/6/auto_importer',
        'method': 'post',
        'data': {
            'name': 'now'},
        'status_code': 303},
    {
        'name': 'System Price',
        'path': '/non_core_contracts/6/auto_importer',
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
            'properties': "{}",
            'mop_contract_id': "11",
            'mop_account': "mc-22 6354 2983 570",
            'dc_contract_id': "8",
            'dc_account': "01",
            'imp_llfc_code': "210",
            'imp_mpan_core': "22 4862 4512 332",
            'imp_sc': "230",
            'imp_supplier_contract_id': "13",
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
            r"0019_FINISHED_watkinsexamplecom_crc_2012_2013_supply_7\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0019_FINISHED_watkinsexamplecom_crc_2012_2013_supply_7.csv',
        'status_code': 200,
        'regexes': [
            r'^7,2012-04-01 00:00,2013-03-31 23:30,22 4862 4512 332']},

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
            'mop_contract_id': "11",
            'mop_account': "mc-22 0195 4836 192",
            'dc_contract_id': "9",
            'dc_account': "dc-22 0195 4836 192",
            'msn': "P96C93722",
            'pc_id': "8",
            'mtc_code': "857",
            'cop_id': "8",
            'ssc_code': "0428",
            'properties': "{}",
            'imp_llfc_code': "980",
            'imp_mpan_core': "22 0195 4836 192",
            'imp_sc': "304",
            'imp_supplier_contract_id': "13",
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
            r"0020_FINISHED_watkinsexamplecom_supply_virtual_bills_9\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0020_FINISHED_watkinsexamplecom_supply_virtual_bills_9.csv',
        'regexes': [
            r'Imp MPAN Core,Exp MPAN Core,Site Code,Site Name,'
            r'Account,From,To,,mop-net-gbp,mop-problem,,'
            r'dc-net-gbp,dc-problem,,imp-supplier-ccl-kwh,'
            r'imp-supplier-ccl-rate,imp-supplier-ccl-gbp,imp-supplier-net-gbp,'
            r'imp-supplier-vat-gbp,imp-supplier-gross-gbp,'
            r'imp-supplier-sum-msp-kwh,imp-supplier-problem',
            r'22 0195 4836 192,,CI004,Lower Treave,SA342376,'
            r'2011-05-01 00:00,2011-05-31 23:30,,10,,,7,,,'
            r',0.00485,,0.0,0.0,0.0,25.819178082191478,'],
        'status_code': 200},

    {
        'name': "Parties",
        'path': '/parties',
        'regexes': [
            r'<a href="/participants/647">SWEB</a>'],
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
            r"0021_FINISHED_watkinsexamplecom_supplies_monthly_duration_for_"
            r"10_1_to_2011_1\.csv"]
        },
    {
        'path': '/downloads/'
        '0021_FINISHED_watkinsexamplecom_supplies_monthly_duration_for_'
        '10_1_to_2011_1.csv',
        'status_code': 200,
        'regexes': [
            r"supply-id,supply-name,source-code,generator-type,month,pc-code,"
            r"msn,site-code,site-name,metering-type,import-mpan-core,"
            r"metered-import-kwh,metered-import-net-gbp,"
            r"metered-import-estimated-kwh,billed-import-kwh,"
            r"billed-import-net-gbp,export-mpan-core,metered-export-kwh,"
            r"metered-export-estimated-kwh,billed-export-kwh,"
            r"billed-export-net-gbp,problem,timestamp",
            r'10,"2","net","","2011-01-31 23:30","03","I02D89150","CI017",'
            r'"Roselands","nhh","22 1065 3921 534","0.0","10.0","0","150.0",'
            r'"98.17","None","0","0","0","0",""']},
    {
        'name': "Try monthly supply duration with a half-hourly.",
        'path': '/reports/177?supply_id=4&months=1&end_year=2010&end_month=05',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"0022_FINISHED_watkinsexamplecom_supplies_monthly_duration_for_"
            r"4_1_to_2010_5\.csv"]},
    {
        'path': '/downloads/'
        '0022_FINISHED_watkinsexamplecom_supplies_monthly_duration_for_'
        '4_1_to_2010_5.csv',
        'status_code': 200,
        'regexes': [
            r"supply-id,supply-name,source-code,generator-type,month,pc-code,"
            r"msn,site-code,site-name,metering-type,import-mpan-core,"
            r"metered-import-kwh,metered-import-net-gbp,"
            r"metered-import-estimated-kwh,billed-import-kwh,"
            r"billed-import-net-gbp,export-mpan-core,metered-export-kwh,"
            r"metered-export-estimated-kwh,billed-export-kwh,"
            r"billed-export-net-gbp,problem,timestamp",
            r'4,"1","net","","2010-05-31 23:30","00","","CI005",'
            r'"Wheal Rodney","hh","22 6158 2968 220","0","189.2268\d*",'
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
            r"/chellowcss"],
        'status_code': 200},
    {
        'path': '/reports/59?start_year=2013&start_month=04&start_day=01&'
        'start_hour=00&start_minute=00&finish_year=2013&finish_month=04&'
        'finish_day=1&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"0023_FINISHED_watkinsexamplecom_sites_duration.csv"]},
    {
        'path': '/downloads/'
        '0023_FINISHED_watkinsexamplecom_sites_duration.csv',
        'status_code': 200,
        'regexes': [
            r'CH017,Parbola,,sub,,2013-04-01 00:00,'
            r'2013-04-01 23:30,0,0,0,0,0,0,hh']},
    {
        'name': "Check CSV Sites HH Data Selector.",
        'path': '/csv_sites_hh_data',

        # Should have link to CSS
        'regexes': [
            r"/chellowcss"],
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
            r"0024_FINISHED_watkinsexamplecom_supplies_hh_data_200807312330_"
            r"supply_22_9205_6799_106\.csv"]},
    {
        'path': '/downloads/'
        '0024_FINISHED_watkinsexamplecom_supplies_hh_data_200807312330_'
        'supply_22_9205_6799_106.csv',
        'status_code': 200,

        # Check the HH data is there
        'regexes': [
            r"NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-06,0\.262"
        ]
    },

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
            'gsp_group_id': "10",
            'mop_contract_id': "11",
            'mop_account': "22 0883 6932 301",
            'dc_contract_id': "8",
            'dc_account': "22 0883 6932 301",
            'msn': "",
            'pc_id': "0",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'properties': "{}",
            'imp_llfc_code': "570",
            'imp_mpan_core': "22 0883 6932 301",
            'imp_sc': "350",
            'imp_supplier_contract_id': "12",
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
            r"0025_FINISHED_watkinsexamplecom_supply_virtual_bills_5\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0025_FINISHED_watkinsexamplecom_supply_virtual_bills_5.csv',
        'regexes': [
            r'Imp MPAN Core,Exp MPAN Core,Site Code,Site Name,'
            r'Account,From,To,,mop-net-gbp,mop-problem,,'
            r'dc-net-gbp,dc-problem,,imp-supplier-net-gbp,'
            r'imp-supplier-tlm,imp-supplier-ccl-kwh,'
            r'imp-supplier-ccl-rate,imp-supplier-ccl-gbp,'
            r'imp-supplier-data-collection-gbp,'
            r'imp-supplier-duos-availability-kva,'
            r'imp-supplier-duos-availability-days,'
            r'imp-supplier-duos-availability-rate,'
            r'imp-supplier-duos-availability-gbp,'
            r'imp-supplier-duos-excess-availability-kva,'
            r'imp-supplier-duos-excess-availability-days,'
            r'imp-supplier-duos-excess-availability-rate,'
            r'imp-supplier-duos-excess-availability-gbp,'
            r'imp-supplier-duos-green-kwh,imp-supplier-duos-green-rate,'
            r'imp-supplier-duos-green-gbp,imp-supplier-duos-amber-kwh,'
            r'imp-supplier-duos-amber-rate,imp-supplier-duos-amber-gbp,'
            r'imp-supplier-duos-red-kwh,imp-supplier-duos-red-rate,'
            r'imp-supplier-duos-red-gbp,imp-supplier-duos-reactive-kvarh,'
            r'imp-supplier-duos-reactive-rate,'
            r'imp-supplier-duos-reactive-gbp,imp-supplier-duos-fixed-days,'
            r'imp-supplier-duos-fixed-rate,imp-supplier-duos-fixed-gbp,'
            r'imp-supplier-settlement-gbp,'
            r'imp-supplier-aahedc-gsp-kwh,imp-supplier-aahedc-rate,'
            r'imp-supplier-aahedc-gbp,imp-supplier-rcrc-kwh,'
            r'imp-supplier-rcrc-rate,imp-supplier-rcrc-gbp,'
            r'imp-supplier-night-msp-kwh,imp-supplier-night-gsp-kwh,'
            r'imp-supplier-night-gbp,imp-supplier-other-msp-kwh,'
            r'imp-supplier-other-gsp-kwh,imp-supplier-other-gbp,'
            r'imp-supplier-summer-pk-msp-kwh,'
            r'imp-supplier-summer-pk-gsp-kwh,imp-supplier-summer-pk-gbp,'
            r'imp-supplier-winter-low-pk-msp-kwh,'
            r'imp-supplier-winter-low-pk-gsp-kwh,'
            r'imp-supplier-winter-low-pk-gbp,'
            r'imp-supplier-winter-off-pk-msp-kwh,'
            r'imp-supplier-winter-off-pk-gsp-kwh,'
            r'imp-supplier-winter-off-pk-gbp,'
            r'imp-supplier-winter-pk-msp-kwh,'
            r'imp-supplier-winter-pk-gsp-kwh,'
            r'imp-supplier-winter-pk-gbp,'
            r'imp-supplier-bsuos-kwh,imp-supplier-bsuos-rate,'
            r'imp-supplier-bsuos-gbp,imp-supplier-triad-actual-1-date,'
            r'imp-supplier-triad-actual-1-msp-kw,'
            r'imp-supplier-triad-actual-1-status,'
            r'imp-supplier-triad-actual-1-laf,'
            r'imp-supplier-triad-actual-1-gsp-kw,'
            r'imp-supplier-triad-actual-2-date,'
            r'imp-supplier-triad-actual-2-msp-kw,'
            r'imp-supplier-triad-actual-2-status,'
            r'imp-supplier-triad-actual-2-laf,'
            r'imp-supplier-triad-actual-2-gsp-kw,'
            r'imp-supplier-triad-actual-3-date,'
            r'imp-supplier-triad-actual-3-msp-kw,'
            r'imp-supplier-triad-actual-3-status,'
            r'imp-supplier-triad-actual-3-laf,'
            r'imp-supplier-triad-actual-3-gsp-kw,'
            r'imp-supplier-triad-actual-gsp-kw,'
            r'imp-supplier-triad-actual-rate,'
            r'imp-supplier-triad-actual-gbp,'
            r'imp-supplier-triad-estimate-1-date,'
            r'imp-supplier-triad-estimate-1-msp-kw,'
            r'imp-supplier-triad-estimate-1-status,'
            r'imp-supplier-triad-estimate-1-laf,'
            r'imp-supplier-triad-estimate-1-gsp-kw,'
            r'imp-supplier-triad-estimate-2-date,'
            r'imp-supplier-triad-estimate-2-msp-kw,'
            r'imp-supplier-triad-estimate-2-status,'
            r'imp-supplier-triad-estimate-2-laf,'
            r'imp-supplier-triad-estimate-2-gsp-kw,'
            r'imp-supplier-triad-estimate-3-date,'
            r'imp-supplier-triad-estimate-3-msp-kw,'
            r'imp-supplier-triad-estimate-3-status,'
            r'imp-supplier-triad-estimate-3-laf,'
            r'imp-supplier-triad-estimate-3-gsp-kw,'
            r'imp-supplier-triad-estimate-gsp-kw,'
            r'imp-supplier-triad-estimate-rate,'
            r'imp-supplier-triad-estimate-months,'
            r'imp-supplier-triad-estimate-gbp,'
            r'imp-supplier-triad-all-estimates-months,'
            r'imp-supplier-triad-all-estimates-gbp,'
            r'imp-supplier-problem',
            r'22 0883 6932 301,,CI005,Wheal Rodney,4341,'
            r'2013-04-01 00:00,2013-04-30 23:30,,10,,,0,,,'
            r'369.604999999999\d*,,,0.00524,,5.89,350,30,'
            r'0.026,272.99999999999994,,,,,0,'
            r'0.00161,0.0,0,0.00287,0.0,0,0.2441,0.0,0.0,0.00382,'
            r'0.0,30,0.0905,2.7150000000000003,88,'
            r'0.0,0.0001897,0.0,0.0,,0.0,0,'
            r'0.0,0.0,0,0.0,0.0,0,0.0,0.0,,,,,,,,'
            r',,0.0,'
            r',0.0,,,,,,,,,,,,,,,,'
            r',,,2012-11-29 17:00,0,X,1.087,0.0,'
            r'2012-12-12 17:00,0,X,1.087,0.0,2013-01-16 17:00,0,'
            r'X,1.087,0.0,0.0,33.551731,1,0.0,,,'],
        'status_code': 200},
    {
        'name': "Try site search",
        'path': '/sites?pattern=',
        'regexes': [
            r'<a href="/sites/8">'
            r'B00LG Bieling</a>'],
        'status_code': 200},
    {
        'name': "Site search with trailing whitespace",
        'path': '/sites?pattern= B00LG',
        'status_code': 302},
    {
        'name': "Try TRIAD report when supply starts after first triad",
        'path': '/reports/41?supply_id=6&year=2007',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"0026_FINISHED_watkinsexamplecom_supplies_triad\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0026_FINISHED_watkinsexamplecom_supplies_triad.csv',
        'regexes': [
            r'CI017,Roselands,1,net,,22 6354 2983 570,'
            r'2007-01-23 17:00,0,X,1.074,0.0,2006-12-20 17:00,0,'
            r'before start of supply,before start of supply,0,'
            r'2007-02-08 17:30,0,X,1.074,0.0,0.0,5.94264,0.0,'
            r',,,,,,,,,,,,,,,,,,$'],
        'status_code': 200},

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
            'gsp_group_id': "4",
            'pc_id': "0",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'properties': "{}",
            'mop_contract_id': "11",
            'mop_account': "14 7206 6139 971/MOP",
            'dc_contract_id': "8",
            'dc_account': "14 7206 6139 971/DC",
            'imp_llfc_code': "365",
            'imp_mpan_core': "14 7206 6139 971",
            'imp_sc': "2300",
            'imp_supplier_contract_id': "10",
            'imp_supplier_account': "sup-14 7206 6139 971",
            'insert_electricity': "insert"},
        'regexes': [
            r"/supplies/17"],
        'status_code': 303},

    {
        'name': "Try a pre 2010-04-01 DNO 14 bill.",
        'path': '/reports/291?supply_id=17&start_year=2009&start_month=06&'
        'start_day=01&start_hour=00&start_minute=00&finish_year=2009&'
        'finish_month=06&finish_day=30&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"0027_FINISHED_watkinsexamplecom_supply_virtual_bills_17\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0027_FINISHED_watkinsexamplecom_supply_virtual_bills_17.csv',
        'regexes': [
            r'Imp MPAN Core,Exp MPAN Core,Site Code,Site Name,'
            r'Account,From,To,,mop-net-gbp,mop-problem,,'
            r'dc-net-gbp,dc-problem,,imp-supplier-net-gbp,'
            r'imp-supplier-tlm,imp-supplier-ccl-kwh,'
            r'imp-supplier-ccl-rate,imp-supplier-ccl-gbp,'
            r'imp-supplier-data-collection-gbp,'
            r'imp-supplier-duos-availability-kva,'
            r'imp-supplier-duos-availability-days,'
            r'imp-supplier-duos-availability-rate,'
            r'imp-supplier-duos-availability-gbp,'
            r'imp-supplier-duos-excess-availability-kva,'
            r'imp-supplier-duos-excess-availability-days,'
            r'imp-supplier-duos-excess-availability-rate,'
            r'imp-supplier-duos-excess-availability-gbp,'
            r'imp-supplier-duos-day-kwh,imp-supplier-duos-day-gbp,'
            r'imp-supplier-duos-night-kwh,imp-supplier-duos-night-gbp,'
            r'imp-supplier-duos-reactive-rate,'
            r'imp-supplier-duos-reactive-gbp,'
            r'imp-supplier-duos-standing-gbp,'
            r'imp-supplier-settlement-gbp,imp-supplier-night-msp-kwh,'
            r'imp-supplier-night-gsp-kwh,imp-supplier-night-gbp,'
            r'imp-supplier-other-msp-kwh,imp-supplier-other-gsp-kwh,'
            r'imp-supplier-other-gbp,imp-supplier-summer-pk-msp-kwh,'
            r'imp-supplier-summer-pk-gsp-kwh,imp-supplier-summer-pk-gbp,'
            r'imp-supplier-winter-low-pk-msp-kwh,'
            r'imp-supplier-winter-low-pk-gsp-kwh,'
            r'imp-supplier-winter-low-pk-gbp,'
            r'imp-supplier-winter-off-pk-msp-kwh,'
            r'imp-supplier-winter-off-pk-gsp-kwh,'
            r'imp-supplier-winter-off-pk-gbp,'
            r'imp-supplier-winter-pk-msp-kwh,'
            r'imp-supplier-winter-pk-gsp-kwh,'
            r'imp-supplier-winter-pk-gbp,'
            r'imp-supplier-bsuos-kwh,imp-supplier-bsuos-rate,'
            r'imp-supplier-bsuos-gbp,imp-supplier-triad-actual-1-date,'
            r'imp-supplier-triad-actual-1-msp-kw,'
            r'imp-supplier-triad-actual-1-status,'
            r'imp-supplier-triad-actual-1-laf,'
            r'imp-supplier-triad-actual-1-gsp-kw,'
            r'imp-supplier-triad-actual-2-date,'
            r'imp-supplier-triad-actual-2-msp-kw,'
            r'imp-supplier-triad-actual-2-status,'
            r'imp-supplier-triad-actual-2-laf,'
            r'imp-supplier-triad-actual-2-gsp-kw,'
            r'imp-supplier-triad-actual-3-date,'
            r'imp-supplier-triad-actual-3-msp-kw,'
            r'imp-supplier-triad-actual-3-status,'
            r'imp-supplier-triad-actual-3-laf,'
            r'imp-supplier-triad-actual-3-gsp-kw,'
            r'imp-supplier-triad-actual-gsp-kw,'
            r'imp-supplier-triad-actual-rate,imp-supplier-triad-actual-gbp,'
            r'imp-supplier-triad-estimate-1-date,'
            r'imp-supplier-triad-estimate-1-msp-kw,'
            r'imp-supplier-triad-estimate-1-status,'
            r'imp-supplier-triad-estimate-1-laf,'
            r'imp-supplier-triad-estimate-1-gsp-kw,'
            r'imp-supplier-triad-estimate-2-date,'
            r'imp-supplier-triad-estimate-2-msp-kw,'
            r'imp-supplier-triad-estimate-2-status,'
            r'imp-supplier-triad-estimate-2-laf,'
            r'imp-supplier-triad-estimate-2-gsp-kw,'
            r'imp-supplier-triad-estimate-3-date,'
            r'imp-supplier-triad-estimate-3-msp-kw,'
            r'imp-supplier-triad-estimate-3-status,'
            r'imp-supplier-triad-estimate-3-laf,'
            r'imp-supplier-triad-estimate-3-gsp-kw,'
            r'imp-supplier-triad-estimate-gsp-kw,'
            r'imp-supplier-triad-estimate-rate,'
            r'imp-supplier-triad-estimate-months,'
            r'imp-supplier-triad-estimate-gbp,'
            r'imp-supplier-triad-all-estimates-months,'
            r'imp-supplier-triad-all-estimates-gbp,imp-supplier-problem',
            r'14 7206 6139 971,,CH023,Treglisson,'
            r'sup-14 7206 6139 971,2009-06-01 00:00,2009-06-30 23:30,,'
            r'10,,,0,,,334.3\d*,,,0.0047,,'
            r'5.89,,,0.0457,105.11,,,,,0,0.0,0,0.0,'
            r'0.0012,0.0,135.30000000000004,88,0,0.0,0.0,0,'
            r'0.0,0.0,0,0.0,0.0,0,0,0.0,0,0,0.0,0,0,'
            r'0.0,0.0,,0.0,,,,,,,,,,,,,,,'
            r',,,,'
            r'2009-01-06 17:00,0,X,1.037,0.0,2008-12-01 17:00,0,'
            r'X,1.037,0.0,2008-12-15 17:00,0,X,1.037,0.0,0.0,'
            r'20.526611,1,0.0,,,,,,,,,,,,,,,,,,,duos-availability-agreed-kva,'
            r'2300,duos-availability-billed-kva,2300'],
        'status_code': 200},
    {
        'name': "Report of DC snags",
        'path': '/reports/233?dc_contract_id=8&days_hidden=1',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"0028_FINISHED_watkinsexamplecom_channel_snags\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0028_FINISHED_watkinsexamplecom_channel_snags.csv',
        'regexes': [
            r'83,22 0883 6932 301,,CI005,Wheal Rodney,Missing,'
            r'True,ACTIVE,2002-01-01 00:00,2003-08-02 23:30,'],
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
            'gsp_group_id': "10"},
        'regexes': [
            r"/supplies/1"],
        'status_code': 303},
    {
        'path': '/reports/29?site_id=7&type=used&months=1&finish_year=2008&'
        'finish_month=07',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"0029_FINISHED_watkinsexamplecom_site_hh_data_200807010000\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0029_FINISHED_watkinsexamplecom_site_hh_data_200807010000.csv',
        'regexes': [
            r"CH017,used,2008-07-01,", ],
        'status_code': 200},
    {
        'path': '/reports/29?site_id=7&type=displaced&months=1&'
        'finish_year=2008&finish_month=07',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"0030_FINISHED_watkinsexamplecom_site_hh_data_200807010000\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0030_FINISHED_watkinsexamplecom_site_hh_data_200807010000.csv',
        'regexes': [
            r"CH017,displaced,2008-07-01,"],
        'status_code': 200},

    {
        'name': "Look at list of supplier contracts.",
        'path': '/supplier_contracts',

        # Are the contracts in alphabetical order?
        'regexes': [
            r'<tbody>\s*'
            r'<tr>\s*'
            r'<td>\s*'
            r'<a\s*'
            r'href="/supplier_contracts/10"\s*'
            r'>Half-hourlies 2007</a>'],
        'status_code': 200},
    {
        'name': "Daily supplier virtual bills page.",
        'path': '/reports/241?supply_id=6&is_import=true&start_year=2013&'
        'start_month=10&start_day=1&finish_year=2013&finish_month=10&'
        'finish_day=31',
        'status_code': 303},
    {
        'name': "Daily supplier virtual bills page.",
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"0031_FINISHED_watkinsexamplecom_daily_"
            r"supplier_virtual_bill\.csv"],
        'status_code': 200},
    {
        'name': "Daily supplier virtual bills page.",
        'path': '/downloads/'
        '0031_FINISHED_watkinsexamplecom_daily_supplier_virtual_bill.csv',
        'status_code': 200,
        'regexes': [
            r'22 6354 2983 570,CI017,Roselands,141 5532,'
            r'2013-10-31 00:00,2013-10-31 23:30,False,153.7805\d*,'
            r',,0.00524,,5.89,2300,1,0.026,59.8,'
            r',,,,,,,,0.00382,0.0,,88,0,'
            r'0.0,0.0,0,0.0,0.0,0,0.0,0.0,0,0,0.0,0,'
            r'0,0.0,0,0,0.0,0.0,,0.0,,,,,,,,,'
            r',,,,,,,,,,2012-11-29 17:00,0,X,'
            r'1.087,0.0,2012-12-12 17:00,0,X,1.087,0.0,'
            r'2013-01-16 17:00,0,X,1.087,0.0,0.0,33.551731,1,'
            r'0.0,,,,duos-amber-gbp,0.0,duos-amber-kwh,0,'
            r'duos-amber-rate,0.00287,duos-fixed-days,1,'
            r'duos-fixed-gbp,0.0905,duos-fixed-rate,0.0905,'
            r'duos-green-gbp,0.0,duos-green-kwh,0,duos-green-rate,'
            r'0.00161,duos-reactive-kvarh,0.0,duos-red-gbp,0.0,'
            r'duos-red-kwh,0,duos-red-rate,0.2441,sbp-rate,,ssp-rate,\s*\Z']},

    {
        'name': "Test register read page.",
        'path': '/csv_register_reads',
        'status_code': 200,
        'regexes': [
            r"end_year"]},
    {
        'name': "Test register read report for a supply.",
        'path': '/reports/219?supply_id=10&months=1&end_year=2011&end_month=1',
        'status_code': 303},
    {
        'name': "Test register read report for a supply.",
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"0032_FINISHED_watkinsexamplecom_register_reads\.csv"],
        'status_code': 200},
    {
        'name': "Test register read report for a supply.",
        'path': '/downloads/'
        '0032_FINISHED_watkinsexamplecom_register_reads.csv',
        'status_code': 200,
        'regexes': [
            r'\.csv".\)',
            r"Duration Start,Duration Finish,Supply Id,Import MPAN Core,"
            r"Export MPAN Core,Batch Reference,Bill Id,Bill Reference,"
            r"Bill Issue Date,Bill Type,Register Read Id,TPR,Coefficient,"
            r"Previous Read Date,Previous Read Value,Previous Read Type,"
            r"Present Read Date,Present Read Value,Present Read Type",
            r'2011-01-01 00:00,2011-01-31 23:30,10,22 1065 3921 534,'
            r',07-002,13,3423760005,2011-02-02 00:00,N,8,00001,'
            r'1,2011-01-04 23:30,24286,E,2011-01-06 23:30,25927,E']},

    {
        'name': "Period where there's a read with no TPR (an MD read)",
        'path': '/reports/219?supply_id=10&months=1&end_year=2007&end_month=1',
        'status_code': 303},
    {
        'name': "Period where there's a read with no TPR (an MD read)",
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"0033_FINISHED_watkinsexamplecom_register_reads\.csv"],
        'status_code': 200},
    {
        'name': "Period where there's a read with no TPR (an MD read)",
        'path': '/downloads/'
        '0033_FINISHED_watkinsexamplecom_register_reads.csv',
        'status_code': 200,
        'regexes': [
            r'2007-01-01 00:00,2007-01-31 23:30,10,22 1065 3921 534,'
            r',06-002,14,SA342376,2007-01-01 00:00,N,12,md,1,'
            r'2007-01-04 00:00,45,E,2007-01-17 00:00,76,E']},

    {
        'name': "View a MOP rate script. Contract 38.",
        'path': '/mop_rate_scripts/27',
        'status_code': 200,
        'regexes': [
            r'<a href="/mop_rate_scripts/27/edit">edit</a>']},

    {
        'name': "View a MOP rate script edit. Contract 37.",
        'path': '/mop_rate_scripts/27/edit',
        'status_code': 200,
        'regexes': [
            r'<input type="submit" value="Update">']},

    {
        'name': "View a MOP rate script confirm delete. Contract 37.",
        'path': '/mop_rate_scripts/27/edit?&delete=Delete',
        'status_code': 200,
        'regexes': [
            r'<form\s*'
            r'method="post"\s*'
            r'action="/mop_rate_scripts/27/edit">']},

    {
        'name': "View eras duration selector.",
        'path': '/csv_eras_duration',
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
            r"0034_FINISHED_watkinsexamplecom_supplies_duration\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0034_FINISHED_watkinsexamplecom_supplies_duration.csv',
        'regexes': [
            r'10,2,'
        ],
        'status_code': 200
    },
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
        'name': "Monthly duration report",
        'path': '/ods_monthly_duration',
        'status_code': 200},

    {
        'name': "Bill type",
        'path': '/bill_types/1',
        'status_code': 200},

    # Supplier contract 64.
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

    # Supplier contract 64.
    {
        'path': '/supplier_bill_imports/8',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"All the bills have been successfully loaded and attached to "
            r"the batch\."]},
    {
        'name': "Look at an DC batch",
        'path': '/dc_batches/8',
        'status_code': 200,
        'regexes': [
            r'<a href="/local_reports/1/output\?batch_id=8">',
            r"<tbody>\s*<tr>"]},

    # Supplier contract 63, batch 7, bill 10
    {
        'name': "Edit register read with a TPR that's not 00001",
        'path': '/reads/1/edit',
        'regexes': [
            r'<option value="36" selected>00040</option>']},

    # Insert a new batch
    {
        'name': "Add and delete an DC contract",
        'path': '/dc_contracts/8/add_batch',
        'method': 'post',
        'data': {
            'reference': "to_delete",
            'description': ""},
        'status_code': 303,
        'regexes': [
            r"/dc_batches/10"]},

    {
        'name': "DC batch confirm delete page. DC contract 34",
        'path': '/dc_batches/10/edit?confirm_delete=Delete',
        'status_code': 200,
        'regexes': [
            r'<form method="post">\s*'
            r'<fieldset>\s*'
            r'<input type="submit" name="delete" value="Delete">\s']},
    {
        'name': "Delete it. DC contract 8",
        'path': '/dc_batches/10/edit',
        'method': 'post',
        'data': {
            'delete': 'Delete'},
        'status_code': 303,
        'regexes': [
            r'/dc_batches\?dc_contract_id=8']},
    {
        'name': "Check it's really gone. DC contract 8",
        'path': '/dc_batches/10',
        'status_code': 404},


    # CRC Special Events
    {
        'name': "CRC Special Events",
        'path': '/reports/215?year=2012',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"0035_FINISHED_watkinsexamplecom_crc_special_events\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0035_FINISHED_watkinsexamplecom_crc_special_events.csv',
        'status_code': 200,
        'regexes': [
            r'22 0883 6932 301,CI005,']},

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
            r"0036_FINISHED_watkinsexamplecom_supply_virtual_bills_10\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0036_FINISHED_watkinsexamplecom_supply_virtual_bills_10.csv',
        'regexes': [
            r'Imp MPAN Core,Exp MPAN Core,Site Code,Site Name,'
            r'Account,From,To,,mop-net-gbp,mop-problem,,'
            r'dc-net-gbp,dc-problem,,imp-supplier-ccl-kwh,'
            r'imp-supplier-ccl-rate,imp-supplier-ccl-gbp,imp-supplier-net-gbp,'
            r'imp-supplier-vat-gbp,imp-supplier-gross-gbp,'
            r'imp-supplier-sum-msp-kwh,imp-supplier-problem',
            r'22 1065 3921 534,,CI017,Roselands,SA342376,'
            r'2010-01-01 00:00,2010-01-03 23:30,,0,,,,,,'
            r',,,0.0,0.0,0.0,0.0,'],
        'status_code': 200},
    {
        'name': "A bill check with multiple covered bills",
        'path': '/reports/111?bill_id=8',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"0037_FINISHED_watkinsexamplecom_bill_check\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0037_FINISHED_watkinsexamplecom_bill_check.csv',
        'regexes': [
            r'06-004,00101,N,244,3810.08,355.03,2011-05-01 00:00,'
            r'2011-06-30 00:00,22 6354 2983 570,,CI017,Roselands,'
            r'2011-05-01 00:00,2011-06-30 00:00,8,0,3810.08,0,3810.08,,,,,'
            r'11.4,0.00485,,,0.0,,,0.0,,,,,,,,,0.0,,,,,,,,,0.0,,,,,0.0,,,,,0.0'
            r',,,,,0.0,,,0.0,,,0.0,,,,,,,0.0,,,,,,,0.0,,,,,,,0.0,,,,,,,0.0,,,,'
            r',,,0.0,,,,,,,0.0,,,,,,,0.0,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,'
            r'0.0,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,0.0,,,,,0.0,,,'
            r'virtual-sbp-rate,,,,virtual-ssp-rate,,,'],
        'status_code': 200},
    {
        'name': "Contract virtual bills",
        'path': '/reports/87?supplier_contract_id=10&start_year=2013&'
        'start_month=12&start_day=01&start_hour=00&start_minute=00&'
        'finish_year=2013&finish_month=12&finish_day=01&finish_hour=23&'
        'finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"0038_FINISHED_watkinsexamplecom_virtual_bills\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0038_FINISHED_watkinsexamplecom_virtual_bills.csv',
        'regexes': [
            r'22 0470 7514 535,CH017,Parbola,010,2013-12-01 00:00,'
            r'2013-12-01 23:30,93.89,,,,,5.89,150,1,'
            r'0.0,0.0,,,,,,,,,0.00147,0.0,,88,0,'
            r'0.0,'
            r'0.0,0,0.0,0.0,0,0,0.0,0,0,0.0,0,0,0.0,'
            r'0,0,0.0,0.0,,0.0,,,,,,,,,'
            r',,,,,,,,,,,,,,,,,,,,,'
            r',,,,,,,,,,,duos-amber-gbp,0.0,'
            r'duos-amber-kwh,0,duos-amber-rate,\{-0.00649\},'
            r'duos-fixed-days,1,'
            r'duos-fixed-gbp,0\.0,duos-fixed-rate,\{0\.0\},duos-green-gbp,'
            r'0.0,duos-green-kwh,0,duos-green-rate,\{-0.00649\}'],
        'status_code': 200},

    {
        'name': "Contract displaced virtual bills",
        'path': '/reports/109?supplier_contract_id=10&months=1&'
        'finish_year=2013&finish_month=01',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"0039_FINISHED_watkinsexamplecom_displaced\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0039_FINISHED_watkinsexamplecom_displaced.csv',
        'regexes': [
            r'CI004,Lower Treave,,2013-01-01 00:00,'
            r'2013-01-31 23:30,chp,,,,,0.0,0.0,,0.0,,0.00509,'
            r',,,0,0.00161,0.0,,,,0.0,0.0,0,0.0,'
            r'0.0,0,,0,0,,,,0,0,0.0,0.0,0,0.0,'
            r'0.0,0,,,,,,,,,,,,,,,,,,,'
            r'2011-12-05 17:00,0,E,1.087,0.0,2012-01-16 17:00,0,'
            r'E,1.087,0.0,2012-02-02 17:30,0,E,1.075,0.0,'
            r'0.0,31.062748,1,0.0,,,,duos-amber-gbp,0.0,'
            r'duos-amber-kwh,0,duos-amber-rate,{0.00251},duos-red-gbp,'
            r'0.0,duos-red-kwh,0,duos-red-rate,{0.20727}'],
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
            'mop_contract_id': "11",
            'mop_account': "mc-22 9205 6799 106",
            'dc_contract_id': "8",
            'dc_account': "01",
            'msn': "",
            'pc_id': "0",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'properties': "{}",
            'imp_llfc_code': "540",
            'imp_mpan_core': "22 9205 6799 106",
            'imp_sc': "450",
            'imp_supplier_contract_id': "10",
            'imp_supplier_account': "11640077",
            'exp_llfc_code': "581",
            'exp_mpan_core': "22 0470 7514 535",
            'exp_sc': "150",
            'exp_supplier_contract_id': "10",
            'exp_supplier_account': ""},
        'status_code': 303},
    {
        'path': '/channel_snags?dc_contract_id=8&days_hidden=5',
        'status_code': 200,
        'regexes': [
            r'<tr>\s*<td>\s*<ul>\s*<li>\s*'
            r'<a href="/channel_snags/100">view</a>\s*'
            r'\[<a href="/channel_snags/100/edit">edit</a>\]\s*'
            r'</li>\s*</ul>\s*</td>\s*<td>\s*</td>\s*<td>\s*'
            r'22 0470 7514 535\s*</td>\s*<td>\s*<ul>\s*'
            r'<li>CH017 Parbola</li>\s*</ul>\s*</td>\s*<td>Missing</td>\s*'
            r'<td>\s*<ul>\s*<li>\s*Export\s*ACTIVE\s*</li>\s*</ul>\s*</td>\s*'
            r'<td>\s*2004-07-07 00:00 to\s*2005-09-14 23:30\s*</td>\s*</tr>']},

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
        'path': '/reports/233?dc_contract_id=8&days_hidden=0',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"0040_FINISHED_watkinsexamplecom_channel_snags\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0040_FINISHED_watkinsexamplecom_channel_snags.csv',
        'status_code': 200,
        'regexes': [
            r'0,107,22 4862 4512 332,,CH023,Treglisson,'
            r'Missing,True,ACTIVE,2010-02-04 20:30,',
            r'0,3,22 9205 6799 106,22 0470 7514 535,CH017,Parbola,'
            r'Missing,False,ACTIVE,2003-08-03 00:00,2004-07-06 23:30,'
            r'[^,]*,[^,]*,True\s*0,100,,22 0470 7514 535,'
            r'CH017,Parbola,Missing,False,ACTIVE,2004-07-07 00:00,'
            r'2005-09-14 23:30,[^,]*,[^,]*,False\s*0,102,,'
            r'22 0470 7514 535,CH017,Parbola,Missing,False,ACTIVE,'
            r'2005-09-15 00:30,2005-12-15 06:30,[^,]*,[^,]*,False\s*'
            r'0,101,,22 0470 7514 535,CH017,Parbola,Missing,'
            r'False,ACTIVE,2005-12-15 10:00,2008-07-06 23:30,[^,]*,'
            r'[^,]*,False\s*0,56,,22 0470 7514 535,CH017,'
            r'Parbola,Missing,False,ACTIVE,2008-07-07 00:00,'
            r'2008-08-06 23:30,[^,]*,[^,]*,True\s*'
            r'0,79,,22 0470 7514 535,CH017,Parbola,Missing,'
            r'False,ACTIVE,2008-08-07 00:00,2008-09-05 23:30,'
            r'[^,]*,[^,]*,False\s*0,68,,22 0470 7514 535,'
            r'CH017,Parbola,Missing,False,ACTIVE,2008-09-06 00:00,'
            r',[^,]*,[^,]*,False\s*']},
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
            r"0041_FINISHED_watkinsexamplecom_supplies_snapshot\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0041_FINISHED_watkinsexamplecom_supplies_snapshot.csv',
        'status_code': 200,
        'regexes': [
            r'2007-09-30 23:30,CI004,Lower Treave,,,9,net,,_L,'
            r'22,HV,nhh,no,05,535,5,0127,3,MOP Contract,'
            r'mc-22 0195 4836 192,Dynamat data,dc-22 0195 4836 192,'
            r'P96C93722,2005-08-06 00:00,2007-08-01 00:00,N,,,'
            r'2005-08-06 00:00,,'
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
            r"0042_FINISHED_watkinsexamplecom_supplies_snapshot\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0042_FINISHED_watkinsexamplecom_supplies_snapshot.csv',
        'status_code': 200,
        'regexes': [
            r'2011-05-31 23:30,CI004,Lower Treave,,,9,net,,_L,'
            r'22,LV,unmetered,no,08,857,6c,0428,2,'
            r'MOP Contract,mc-22 0195 4836 192,Dynamat data,'
            r'dc-22 0195 4836 192,P96C93722,2005-08-06 00:00,unmetered,'
            r',,,2005-08-06 00:00,,false,false,false,false,false,false,'
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
            r"0043_FINISHED_watkinsexamplecom_supplies_snapshot\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0043_FINISHED_watkinsexamplecom_supplies_snapshot.csv',
        'status_code': 200,
        'regexes': [
            r'Other Site Ids,Other Site Names',
            r'2012-05-31 23:30,CI017,Roselands,,,6,net,,_L,22,'
            r'LV,hh,no,00,845,5,,,MOP Contract,'
            r'mc-22 6354 2983 570,HH contract,01,,2007-01-01 00:00,'
            r'hh,,,,2007-01-01 00:00,,true,true,false,false,false,true,'
            r'22 6354 2983 570,2300,570,PC 5-8 & HH LV,'
            r'Half-hourlies 2007,141 5532,,2011-06-30 00:00,,,,'
            r',,,,$']},

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
            r"0044_FINISHED_watkinsexamplecom_supply_virtual_bills_7\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0044_FINISHED_watkinsexamplecom_supply_virtual_bills_7.csv',
        'regexes': [
            r'22 4862 4512 332,,CH023,Treglisson,141 5532,2013-09-29 00:00,'
            r'2013-11-28 23:30,,20,,,0,,,,0.00524,,0.0,0.0,0.0,0,'],
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
        'path': '/dc_contracts/8/hh_imports',
        'method': 'post',
        'files': {'import_file': 'test/hh_clock_change.df2'},
        'status_code': 303,
        'regexes': [
            r"/dc_contracts/8/hh_imports/15"]},
    {
        'path': '/dc_contracts/8/hh_imports/15',
        'tries': {},
        'regexes': [
            r"The import has completed.*successfully."],
        'status_code': 200},
    {
        'path': '/supplies/5/hh_data?months=1&finish_year=2014&'
        'finish_month=03',
        'regexes': [
            r"<tr>\s*<td>\s*2014-03-30 00:30\s*</td>\s*<td>0</td>\s*"
            r"<td>A</td>"],
        'status_code': 200},

    # Create a new batch
    {
        'name': "NHH bill outside supply period.",
        'path': '/supplier_contracts/13/add_batch',
        'method': 'post',
        'data': {
            'reference': "06-078",
            'description': "Way out batch"
        },
        'status_code': 303,
        'regexes': [
            r"/supplier_batches/12"
        ]
    },

    {
        'name': "View empty batch",
        'path': '/supplier_batches/12',
        'status_code': 200
    },

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
        'name': 'Supplier contract 13, batch 12',
        'path': '/supplier_bill_imports/9',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"All the bills have been successfully loaded and attached to "
            r"the batch\."]},
    {
        'path': '/reports/219?supply_id=7&months=1&end_year=2002&end_month=1',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"0045_FINISHED_watkinsexamplecom_register_reads\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0045_FINISHED_watkinsexamplecom_register_reads.csv',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r'2002-01-01 00:00,2002-01-31 23:30,7,22 4862 4512 332,,'
            r'06-078,20,jg87593jfj,2002-02-02 00:00,N,15,00001,'
            r'1,2002-01-04 23:30,2286,E,2002-01-06 23:30,2927,E']},

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
            r'<a\s*'
            r'href="/sites/3"\s*'
            r'title="Wheal Rodney">CI005</a>\s*</td>'],
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
            r"0046_FINISHED_watkinsexamplecom_supplies_snapshot\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0046_FINISHED_watkinsexamplecom_supplies_snapshot.csv',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r'2014-05-31 23:30,CI005,Wheal Rodney,,,5,gen,'
            r'chp,_L,22,LV,hh,no,00,845,5,,,MOP Contract,'
            r'22 0883 6932 301,HH contract,22 0883 6932 301,,'
            r'2002-01-01 00:00,hh,,2007-10-31 23:30,2007-10-31 23:30,'
            r'2002-01-01 00:00,,'
            r'true,true,false,false,false,true,22 0883 6932 301,'
            r'350,570,PC 5-8 & HH LV,Half-hourlies 2013,4341,0,,'
            r',,,,,,,']},
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
        'path': '/non_core_rate_scripts/1/edit',
        'method': 'post',
        'data': {
            # First rate script of non-core contract bank_holidays
            'start_year': "2006",
            'start_month': "01",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00",
            'has_finished': "true",
            'finish_year': "2009",
            'finish_month': "12",
            'finish_day': "30",
            'finish_hour': "23",
            'finish_minute': "30",
            'script': """{
    "bank_holidays": []}"""},
        'status_code': 303},
    {
        'path': '/non_core_rate_scripts/2',
        'regexes': [
            r"2009-12-31 00:00"],
        'status_code': 200},
    {
        'name': "Put it back to how it was",
        'path': '/non_core_rate_scripts/1/edit',
        'method': 'post',
        'data': {
            'start_year': "2006",
            'start_month': "01",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00",
            'has_finished': "true",
            'finish_year': "2009",
            'finish_month': "12",
            'finish_day': "31",
            'finish_hour': "23",
            'finish_minute': "30",
            'script': """{
    "bank_holidays": []}"""},
        'status_code': 303},

    {
        'name': "Try sites monthly duration with a clocked bill",
        'path': '/supplier_bill_imports',
        'method': 'post',
        'data': {
            'supplier_batch_id': "7"},
        'files': {'import_file': 'test/bills-nhh-clocked.csv'},
        'status_code': 303,
        'regexes': [
          r'supplier_bill_imports/10']},

    {
        'name': "Bill check on a clocked bill",
        'path': '/supplier_bill_imports/10',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r'have been successfully loaded']},

    {
        'name': "Bill check on a clocked bill",
        'path': '/reports/111?bill_id=21',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"0047_FINISHED_watkinsexamplecom_bill_check\.csv"]},
    {
        'path': '/downloads/0047_FINISHED_watkinsexamplecom_bill_check.csv',
        'status_code': 200,
        'regexes': [
            r'07-002,3423760010,N,10,9.07,0.21,2012-01-05 00:00,'
            r'2012-01-10 23:30,22 1065 3921 534,,CI017,Roselands,'
            r'2012-01-05 00:00,2012-01-10 23:30,21,30.\d*,9.07,0,9.07,'
            r'10.0,9.999999\d*,,']},
    {
        'name': "Monthly supplies duration with export hh data",
        'path': '/reports/177?supply_id=1&months=1&end_year=2008&end_month=07',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"0048_FINISHED_watkinsexamplecom_supplies_monthly_duration_for_"
            r"1_1_to_2008_7\.csv"]},
    {
        'path': '/downloads/'
        '0048_FINISHED_watkinsexamplecom_supplies_monthly_duration_for_'
        '1_1_to_2008_7.csv',
        'status_code': 200,
        'regexes': [
            r"supply-id,supply-name,source-code,generator-type,month,pc-code,"
            r"msn,site-code,site-name,metering-type,import-mpan-core,"
            r"metered-import-kwh,metered-import-net-gbp,"
            r"metered-import-estimated-kwh,billed-import-kwh,"
            r"billed-import-net-gbp,export-mpan-core,metered-export-kwh,"
            r"metered-export-estimated-kwh,billed-export-kwh,"
            r"billed-export-net-gbp,problem,timestamp",
            r'1,"Hello","sub","","2008-07-31 23:30","00","","CH017","Parbola",'
            r'"hh","None","18.281","0","0","0","0","22 0470 7514 535","0","0",'
            r'"0","0",""']},

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
            r"0049_FINISHED_watkinsexamplecom_hh_data_row_200801010000\.csv"]},
    {
        'path': '/downloads/'
        '0049_FINISHED_watkinsexamplecom_hh_data_row_200801010000.csv',
        'status_code': 200,
        'regexes': [
            r'"CH023","22 4862 4512 332","","2008-01-01 00:00","3.77","A",'
            r'"\d\d\d\d-\d\d-\d\d \d\d:\d\d","","","","","","","","",""']},

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
            r"0050_FINISHED_watkinsexamplecom_hh_data_row_201001010000\.csv"]},
    {
        'path': '/downloads/'
        '0050_FINISHED_watkinsexamplecom_hh_data_row_201001010000.csv',
        'status_code': 200,
        'regexes': [
            r'"Export REACTIVE_EXP Status","Export REACTIVE_EXP Modified"\s'
            r'"CH023","22 4862 4512 332","","2010-02-04 20:00","30.4339","A",'
            r'"\d\d\d\d-\d\d-\d\d \d\d:\d\d","","","","","","","","",""']},

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
            r"finish date 2007-01-01 00:00."],
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

    {
        'name': "HH by HH virtual bill (must straddle two eras)",
        'path': '/reports/387?supply_id=5&start_year=2012&start_month=12&'
        'start_day=31&start_hour=23&start_minute=30&finish_year=2013&'
        'finish_month=1&finish_day=1&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'name': "HH by HH virtual bill (must straddle two eras)",
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r'0051_FINISHED_watkinsexamplecom_supply_virtual_bills_hh_5\.csv'],
        'status_code': 200},
    {
        'name': "HH by HH virtual bill (must straddle two eras)",
        'path': '/downloads/'
        '0051_FINISHED_watkinsexamplecom_supply_virtual_bills_hh_5.csv',
        'status_code': 200,
        'regexes': [
            r'^22 0883 6932 301,']},

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
            r"<td>\s*2010-02-04 20:00\s*</td>\s*<td>60.9</td>\s*"
            r"<td>91.4</td>\s*<td>0.55</td>\s*<td>109.8</td>\s*<td>230</td>\s*"
            r"<td>\s*30\s*</td>\s*</tr>"]},

    # Add in second batch
    {
        'name': "Order of DC batches",
        'path': '/dc_contracts/8/add_batch',
        'method': 'post',
        'data': {
            'reference': "7",
            'description': ""},
        'status_code': 303},
    {
        'path': '/dc_batches?dc_contract_id=8',
        'status_code': 200,
        'regexes': [
            r'<a\s*href="/dc_contracts/8"\s*>HH contract</a>',
            r'<tr>\s*<td>\s*'
            r'<a href="/dc_batches/13">\s*7\s*'
            r'</a>\s*</td>\s*<td></td>\s*</tr>\s*<tr>\s*<td>\s*'
            r'<a href="/dc_batches/8">\s*'
            r'001-7t\s*</a>\s*</td>\s*<td>dc batch</td>\s*</tr>']},

    # Add in second batch
    {
        'name': "Order of MOP batches",
        'path': '/mop_contracts/11/add_batch',
        'method': 'post',
        'data': {
            'reference': "7a",
            'description': ""},
        'status_code': 303},
    {
        'path': '/mop_batches?mop_contract_id=11',
        'status_code': 200,
        'regexes': [
            r'<tr>\s*<td>\s*'
            r'<a href="/mop_batches/9">\s*'
            r'99/992\s*</a>\s*</td>\s*<td>mop batch</td>\s*</tr>\s*<tr>\s*'
            r'<td>\s*'
            r'<a href="/mop_batches/14">\s*7a\s*'
            r'</a>\s*</td>\s*<td></td>\s*</tr>']},

    {
        'name': "MTCs",
        'path': '/mtcs',
        'status_code': 200,
        'regexes': [
            r'<tr>\s*<td>\s*'
            r'<a href="/mtcs/98">\s*001\s*'
            r'</a>\s*</td>\s*<td>\s*'
            r'<a href="/dnos/805">\s*'
            r'12\s*</a>\s*</td>\s*<td>Economy 7, 23.30 - 06.30</td>\s*<td>\s*'
            r'<a href="/meter_types/15">\s*TP\s*'
            r'</a>\s*</td>\s*<td>2</td>\s*</tr>']},

    {
        'path': '/mtcs/98',
        'status_code': 200,
        'regexes': [
            r'<tr>\s*<th>Code</th>\s*<td>001</td>\s*</tr>\s*<tr>\s*'
            r'<th>DNO</th>\s*<td>\s*'
            r'<a href="/dnos/805">\s*'
            r'12\s*</a>\s*</td>\s*</tr>']},

    {
        'path': '/mtcs/0',
        'status_code': 200,
        'regexes': [
            r"<tr>\s*<th>Code</th>\s*<td>500</td>\s*</tr>\s*<tr>\s*"
            r"<th>DNO</th>\s*<td>\s*All\s*</td>\s*</tr>"]},

    {
        'path': '/mtcs/0/edit',
        'method': 'post',
        'data': {
            'description': 'NHH Unrestricted 1-rate Non-Prog Credit Meter',
            'has_related_metering': 'true',
            'has_comms': 'false',
            'is_hh': 'false',
            'meter_type_id': '17',
            'meter_payment_type_id': '0',
            'tpr_count': '1',
            'valid_from_year': '1996',
            'valid_from_month': '04',
            'valid_from_day': '01',
            'valid_from_hour': '00',
            'valid_from_minute': '00'},
        'status_code': 303},

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
            'mop_contract_id': "11",
            'mop_account': "mc-22 1065 3921 534",
            'dc_contract_id': "8",
            'dc_account': "dc-22 1065 3921 534",
            'pc_id': "3",
            'mtc_code': "801",
            'cop_id': "6",
            'ssc_code': "366",
            'properties': "{}",
            'imp_llfc_code': "110",
            'imp_mpan_core': "22 1065 3921 534",
            'imp_sc': "30",
            'imp_supplier_contract_id': "16",
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
            r"0052_FINISHED_watkinsexamplecom_bill_check\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0052_FINISHED_watkinsexamplecom_bill_check.csv',
        'status_code': 200,
        'regexes': [
            r'06-002,23618619,N,0,49119.00,8596.00,2007-06-30 00:00,'
            r'2007-07-31 00:00,22 9974 3438 105,,CI005,Wheal Rodney,'
            r'2007-06-30 00:00,2007-07-31 00:00,6,1209.0322580\d*,'
            r',,,0.00441,,,0.0,49119.0,0,'
            r'49119.0,8596.0,,8596.0,,,0.0,0.0,4.765\d*,,']},
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
            'mop_contract_id': "11",
            'mop_account': "mc-22 1065 3921 534",
            'dc_contract_id': "9",
            'dc_account': "dc-22 1065 3921 534",
            'msn': "I02D89150",
            'pc_id': "3",
            'mtc_code': "801",
            'cop_id': "5",
            'ssc_code': "0393",
            'properties': "{}",
            'imp_llfc_code': "110",
            'imp_mpan_core': "22 1065 3921 534",
            'imp_sc': "30",
            'imp_supplier_contract_id': "16",
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
            r"0053_FINISHED_watkinsexamplecom_bill_check\.csv"]},
    {
        'path': '/downloads/0053_FINISHED_watkinsexamplecom_bill_check.csv',
        'status_code': 200,
        'regexes': [
            r'07-002,3423760005,N,150,98.17,15.01,'
            r'2011-01-05 00:00,2011-01-10 23:30,22 1065 3921 534,,'
            r'CI017,Roselands,2011-01-05 00:00,2011-01-10 23:30,13,'
            r'692.9175824\d*,98.17,0,98.17,150.0,14239.0\d*,,']},

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
            'tpr_id': "642",
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
            r"0054_FINISHED_watkinsexamplecom_bill_check\.csv"]},
    {
        'path': '/downloads/0054_FINISHED_watkinsexamplecom_bill_check.csv',
        'status_code': 200,
        'regexes': [
            r'07-002,3423760010,N,10,9.07,0.21,2012-01-05 00:00,'
            r'2012-01-10 23:30,22 1065 3921 534,,CI017,Roselands,'
            r'2012-01-05 00:00,2012-01-10 23:30,21,0,9.07,0,9.07,'
            r'10.0,0,,']},

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
            'tpr_id': "0",
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
            r"0055_FINISHED_watkinsexamplecom_crc_2009_2010_supply_10\.csv"]},
    {
        'path': '/downloads/'
        '0055_FINISHED_watkinsexamplecom_crc_2009_2010_supply_10.csv',
        'status_code': 200,
        'regexes': [
            r'10,2009-04-01 00:00,2010-03-31 23:30,22 1065 3921 534,CI017,'
            r'Roselands,2009-04-01 00:00,'
            r'2010-03-31 23:30,.*?,0,0,277.0,0,0,0,365.0,'
            r'0,277.0,365.0,Actual,0,0,2164.9638989169675,0,'
            r'0,0,2164.9638989169675']},

    {
        'name': "BAU scenario. Remove contents of rate script.",
        'path': '/supplier_rate_scripts/26/edit',
        'method': 'post',
        'data': {
            'start_year': '2000',
            'start_month': '01',
            'start_day': '03',
            'start_hour': '00',
            'start_minute': '00',
            'script': '{}'},
        'status_code': 303},

    {
        'name': "Run a BAU scenario. Add scenario",
        'path': '/supplier_contracts/add',
        'method': 'post',
        'data': {
            'participant_id': "70",  # COOP
            'name': "scenario_bau",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'charge_script': "",
            'properties': """
{
  "local_rates": [
    {
      "contract_id": 10,
      "start_date": 2015-06-01T00:00:00Z,
      "finish_date": 2015-06-30T23:30:00Z,
      "script": {
        "*": {
          "night": 0.0062656,
          "other": 0.0062656,
          "summer-pk": 0.0062656,
          "winter-low-pk": 0.0501474,
          "winter-off-pk": 0.0062656,
          "winter-pk": 0.0193918}}}],

  "scenario_start": 2015-06-01T00:00:00Z,
  "scenario_duration": 1}""", },
        'regexes': [
            r"/supplier_contracts/17"],
        'status_code': 303},
    {
        'name': "Scenario runner",
        'path': '/ods_scenario_runner',
        'regexes': [
            r'<a href="/reports/247\?scenario_id=17">\s*'
            r'Run\s*'
            r'</a>'],
        'status_code': 200},

    {
        'name': "Run scenario for a site where there are no site groups",
        'path': '/reports/247?site_id=1&scenario_id=17&compression=False',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 70, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"0056_FINISHED_watkinsexamplecom_scenario_bau_20150601_0000_for_"
            r"1_months_site_CI004\.ods"]},
    {
        'path': '/downloads/'
        '0056_FINISHED_watkinsexamplecom_scenario_bau_20150601_0000_for_'
        '1_months_site_CI004.ods',
        'status_code': 200,

        'regexes': [
            r'CI005',
            r'<table:table-cell office:string-value="exp-supplier-problem" '
            r'office:value-type="string"/>\s*'
            r'</table:table-row>']},

    {
        'name': "BAU scenario. Reinstate contents of rate script.",
        'path': '/supplier_rate_scripts/26/edit',
        'method': 'post',
        'data': {
            'start_year': '2000',
            'start_month': '01',
            'start_day': '03',
            'start_hour': '00',
            'start_minute': '00',
            'script': """{
                "gsp_gbp_per_kwh": {
                  "night": 0.0062656,
                  "other": 0.0062656,
                  "summer-pk": 0.0062656,
                  "winter-low-pk": 0.0501474,
                  "winter-off-pk": 0.0062656,
                  "winter-pk": 0.0193918}}"""},
        'status_code': 303},

    {
        'name': "Run scenario for a site where there are site groups",
        'path': '/reports/247?site_id=3&scenario_id=17&compression=False',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"0057_FINISHED_watkinsexamplecom_scenario_bau_20150601_0000_for_"
            r"1_months_site_CI005\.ods"]},
    {
        'path': '/downloads/'
        '0057_FINISHED_watkinsexamplecom_scenario_bau_20150601_0000_for_'
        '1_months_site_CI005.ods',
        'status_code': 200,
        'regexes': [
            r"CI005"]},

    {
        'name': "Check BSUoS automatic import page",
        'path': '/non_core_contracts/2/auto_importer',
        'status_code': 200,
        'regexes': [
            r"Is Locked\?"]},
    {
        'name': "Check RCRC automatic import page",
        'path': '/non_core_contracts/5/auto_importer',
        'status_code': 200,
        'regexes': [
            r"Is Locked\?"]},
    {
        'name': "Check TLM automatic import page",
        'path': '/non_core_contracts/7/auto_importer',
        'status_code': 200,
        'regexes': [
            r"Is Locked\?"]},

    # Add a scenario
    {
        'name': "Run an increased BSUoS scenario",
        'path': '/supplier_contracts/add',
        'method': 'post',
        'data': {
            'participant_id': "70",  # COOP
            'name': "scenario_bsuos",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'charge_script': "",
            'properties': """
{
  "scenario_start": 2011-01-01T00:00:00Z,
  "scenario_duration": 1,

  "local_rates": [
    {
      "contract_id": 20,
      "start_date": 2015-06-01T00:00:00Z,
      "finish_date": 2015-06-30T23:30:00Z,
      "script": {
        "gsp_gbp_per_kwh": {
          "night": 0.0062656,
        "other": 0.0062656,
        "summer-pk": 0.0062656,
        "winter-low-pk": 0.0501474,
        "winter-off-pk": 0.0062656,
        "winter-pk": 0.0193918}}}],

  "industry_rates": [
    {
      "contract_name": "aahedc",
      "start_date": 2011-01-01T00:00:00Z,
      "finish_date": 2011-01-31T23:30:00Z,
      "script": {
          "aahedc_gbp_per_gsp_kwh": 0.10016297}}]}"""},
        'regexes': [
            r"/supplier_contracts/18"],
        'status_code': 303},

    {
        'name': "Run scenario for a site",
        'path': '/reports/247?site_id=3&scenario_id=18&compression=False',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"0058_FINISHED_watkinsexamplecom_scenario_bsuos_20110101_0000_"
            r"for_1_months_site_CI005\.ods"]},
    {
        'path': '/downloads/'
        '0058_FINISHED_watkinsexamplecom_scenario_bsuos_20110101_0000_for_'
        '1_months_site_CI005.ods',
        'status_code': 200,
        'regexes': [
            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:string-value="22 6158 2968 220" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Half-hourlies 2013" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="22 3479 7618 470" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Half-hourlies 2007" '
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
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:date-value="2011-01-31T23:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="9"/>\s*'
            r'<table:table-cell office:value="189.2268\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="112.080\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="5"/>\s*'
            r'<table:table-cell office:value="189.2268\d*" '
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
            r'<table:table-cell office:value="179.2268\d*" '
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
            r'<table:table-cell table:number-columns-repeated="8"/>\s*'
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
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
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
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
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
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
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
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0003" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
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
            r'<table:table-cell office:value="19.6478\d*" '
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
            r'<table:table-cell table:number-columns-repeated="19"/>\s*'
            r'<table:table-cell office:value="112.080\d*" '
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
            r'<table:table-cell table:number-columns-repeated="8"/>\s*'
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
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
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
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
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
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
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
            'participant_id': "70",  # COOP
            'name': "scenario_used",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'charge_script': "",
            'properties': r"""
{
    "scenario_start": 2005-09-01T00:00:00Z,
    "scenario_duration": 2,
    "forecast_from": 2006-01-01T00:00:00Z,

    "hh_data": {
      "CI005": {
        "used": "
          2005-09-01 00:00, 0.5",
        "generated": "
            2005-09-01 00:00, 2
            2005-09-15 00:00, 2
            2005-10-01 00:00, 2
            2006-09-01 00:00, 0"}}}"""},
        'regexes': [
            r"/supplier_contracts/19"],
        'status_code': 303},

    {
        'name': "Run scenario for a site",
        'path': '/reports/247?site_id=3&scenario_id=19&compression=False',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r'0059_FINISHED_watkinsexamplecom_scenario_used_20050901_0000_for_'
            r'2_months_site_CI005\.ods']},
    {
        'path': '/downloads/'
        '0059_FINISHED_watkinsexamplecom_scenario_used_20050901_0000_for_'
        '2_months_site_CI005.ods',
        'status_code': 200,
        'regexes': [
            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:string-value="CI005" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Wheal Rodney" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="CI004" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:date-value="2005-09-30T23:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:string-value="hh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="gen, net" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="chp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="1.5" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="4.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell office:value="2.5" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="263.80\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="116.966601073\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="4"/>\s*'
            r'<table:table-cell office:value="0.02414945\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="263.83014945\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="3"/>\s*'
            r'</table:table-row>\s*'
            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:string-value="CI005" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Wheal Rodney" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="CI004" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:date-value="2005-10-31T23:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:string-value="hh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="gen, net" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="chp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="3506.1935483872066" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="2.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="4"/>\s*'
            r'<table:table-cell office:value="3506.193548387\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="268.969999999\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="116.226801431\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="4"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="268.96999999\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="3"/>\s*'
            r'</table:table-row>']},

    {
        'name': "Try to detach an era from its physical site",
        'path': '/eras/8/edit',
        'method': 'post',
        'data': {
            'site_id': "1",
            'detach': "Detach"},
        'status_code': 400,
        'regexes': [
            r'<li>\s*'
            r'You can&#39;t detach an era from the site where it is '
            r'physically located.\s*'
            r'</li>']},
    {
        'name': "Look at a DNO",
        'path': '/dnos/160',
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
        'path': '/supplier_contracts/18/edit',
        'method': 'post',
        'data': {
            'party_id': "106",  # COOP
            'name': "scenario_bsuos",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'charge_script': "",
            'properties': """
{
    "bsuos" : {
        "start_date": 5010-01-01T00:00:00Z,
        "multiplier": 1,
        "constant": 0.1},

    "ccl": {
        "start_date": 2014-10-01T00:00:00Z,
        "multiplier": 1,
        "constant": 0},

    "aahedc": {
        "start_date": 2011-01-01T00:00:00Z,
        "multiplier": 1,
        "constant": 0.1},

    "scenario_start": 5011-01-01T00:00:00Z,
    "scenario_duration": 1,
    "resolution": "hh",

    "kw_changes": ""}
"""},
        'regexes': [
            r"/supplier_contracts/18"],
        'status_code': 303},

    # Run scenario for a site
    {
        'path': '/reports/247?site_id=3&scenario_id=18&compression=False',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"0060_FINISHED_watkinsexamplecom_scenario_bsuos_50110101_0000_"
            r"for_1_months_site_CI005\.ods"]},
    {
        'path': '/downloads/'
        '0060_FINISHED_watkinsexamplecom_scenario_bsuos_50110101_0000_'
        'for_1_months_site_CI005.ods',
        'status_code': 200,
        'regexes': [
            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:string-value="22 6158 2968 220" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Half-hourlies 2013" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="22 3479 7618 470" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Half-hourlies 2007" '
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
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:date-value="5011-01-31T23:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="9"/>\s*'
            r'<table:table-cell '
            r'office:value="248.895\d*" office:value-type="float"/>\s*'
            r'<table:table-cell office:value="106.7829\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="5"/>\s*'
            r'<table:table-cell office:value="248.895\d*" '
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
            r'<table:table-cell office:value="238.895\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.00847" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="5.89" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="130" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="31" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0282" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="113.64\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="8"/>\s*'
            r'<table:table-cell office:value="0.00072" '
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
            r'office:date-value="2017-12-11T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.038" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2018-02-05T17:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.038" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2018-02-26T18:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.038" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="67.731541" '
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
            r'<table:table-cell office:value="0.01343" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.01407" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.06719" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="31" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="1.0116" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="31.3596\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0002749" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="19"/>\s*'
            r'<table:table-cell office:value="106.7829\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.00847" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="5.89" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="20" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="31" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell table:number-columns-repeated="8"/>\s*'
            r'<table:table-cell office:value="0.00096" '
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
            r'office:date-value="2017-12-11T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.038" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2018-02-05T17:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.038" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell '
            r'office:date-value="2018-02-26T18:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.038" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="7.700456" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="1" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'</table:table-row>']},

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
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"0061_FINISHED_watkinsexamplecom_Market_Participant_233_"
            r"general_import\.csv"]},
    {
        'path': '/downloads/'
        '0061_FINISHED_watkinsexamplecom_Market_Participant_233_general_'
        'import.csv',
        'status_code': 200,
        'regexes':  [
            r'insert,participant,JOLT,Jolt Energy Ltd.']},

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
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"0062_FINISHED_watkinsexamplecom_Market_Role_234_general_"
            r"import\.csv"]},
    {
        'path': '/downloads/'
        '0062_FINISHED_watkinsexamplecom_Market_Role_234_general_import.csv',
        'status_code': 200,
        'regexes':  [
            r'insert,market_role,7,Fusion Balancer',
            r'update,market_role,S,Settlement System Controller']},

    {
        'name': "MDD Converter. Market role",
        'path': "/general_imports",
        'method': "post",
        'files': {'import_file': "test/gi_insert_market_role.csv"},
        'status_code': 303,
        'regexes': [
            r"/general_imports/22"]},
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
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"0063_FINISHED_watkinsexamplecom_Market_Participant_Role_232_"
            r"general_import\.csv"]},
    {
        'path': '/downloads/'
        '0063_FINISHED_watkinsexamplecom_Market_Participant_Role_232_general_'
        'import.csv',
        'status_code': 200,
        'regexes':  [
            r'insert,party,M,JOLT,Jolt Metering Services Ltd,'
            r'2015-08-19 00:00,,']},

    {
        'name': "MDD Converter. Party",
        'path': "/general_imports",
        'method': "post",
        'files': {'import_file': "test/gi_party.csv"},
        'status_code': 303,
        'regexes': [
            r"/general_imports/23"]},
    {
        'name': "MDD Converter. Party",
        'path': "/general_imports/23",
        'tries': {'max': 10, 'period': 1},
        'status_code': 200,
        'regexes': [r"The file has been imported successfully\."]},

    {
        'name': "MDD Converter. Check imported party looks okay",
        'path': "/participants/752",
        'status_code': 200,
        'regexes': [
            r'<tr>\s*<td>\s*'
            r'<a href="/parties/1183">Jolt Metering Services Ltd</a>\s*'
            r'</td>\s*<td>\s*'
            r'<a href="/market_roles/21">Meter Operator</a>\s*'
            r'</td>\s*<td>\s*</td>\s*</tr>']},

    {
        'name': "MDD Converter. Convert LLFC.",
        'path': "/reports/163",
        'method': "post",
        'files': {"file": "test/Line_Loss_Factor_Class_225.csv"},
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"0064_FINISHED_watkinsexamplecom_Line_Loss_Factor_Class_225_"
            r"general_import.csv"]},
    {
        'path': '/downloads/'
        '0064_FINISHED_watkinsexamplecom_Line_Loss_Factor_Class_225_general_'
        'import.csv',
        'status_code': 200,
        'regexes':  [
            r'insert,llfc,19,889,"PROLOGIS, BEDDINGTON - IMPORT",LV,'
            r'False,True,2012-04-01 00:00,',
            r'update,llfc,14,633,2015-04-01 00:00,Spare LV 2,LV,False,True,'
            r'2015-05-13 23:30']},

    {
        'name': "GI Insert LLFC",
        'path': "/general_imports",
        'method': "post",
        'files': {'import_file': "test/gi_insert_llfc.csv"},
        'status_code': 303,
        'regexes': [
            r"/general_imports/24"]},
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
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"0065_FINISHED_watkinsexamplecom_MTC_Meter_Type_234_general_"
            r"import\.csv"]},
    {
        'path': '/downloads/'
        '0065_FINISHED_watkinsexamplecom_MTC_Meter_Type_234_general_'
        'import.csv',
        'status_code': 200,
        'regexes':  [
            r'insert,meter_type,6A,COP6\(a\)  20 days memory,'
            r'1996-04-02 00:00,']},
    {
        'name': "MDD Converter. MTC Meter Type",
        'path': "/general_imports",
        'method': "post",
        'files': {'import_file': "test/gi_mtc_meter_type.csv"},
        'status_code': 303,
        'regexes': [
            r"/general_imports/25"]},
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
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"0066_FINISHED_watkinsexamplecom_Meter_Timeswitch_Class_233_"
            r"general_import\.csv"]},
    {
        'path': '/downloads/'
        '0066_FINISHED_watkinsexamplecom_Meter_Timeswitch_Class_233_general_'
        'import.csv',
        'status_code': 200,
        'regexes':  [
            r'update,mtc,,506,Unmetered Reserved - Site Specific,'
            r'True,False,False,UM,CR,0,1996-04-01 00:00,'
            r'2010-04-01 23:30']},

    {
        'name': "MDD Converter. Meter Timeswitch Class",
        'path': "/general_imports",
        'method': "post",
        'files': {'import_file': "test/gi_meter_timeswitch_class.csv"},
        'status_code': 303,
        'regexes': [
            r"/general_imports/26"]},
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
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"0067_FINISHED_watkinsexamplecom_MTC_in_PES_Area_233_general_"
            r"import\.csv"]},
    {
        'path': '/downloads/'
        '0067_FINISHED_watkinsexamplecom_MTC_in_PES_Area_233_general_'
        'import.csv',
        'status_code': 200,
        'regexes':  [
            r'update,mtc,19,074,Local Authority Heating,False,'
            r'False,False,LN,CR,1,1996-04-01 00:00,']},
    {
        'name': "MDD Converter. MTC in PES Area",
        'path': "/general_imports",
        'method': "post",
        'files': {'import_file': "test/gi_insert_mtc_in_pes_area.csv"},
        'status_code': 303,
        'regexes': [
            r"/general_imports/27"]},
    {
        'name': "MDD Converter. Meter Timeswitch Class",
        'path': "/general_imports/27",
        'tries': {'max': 10, 'period': 1},
        'status_code': 200,
        'regexes': [r"The file has been imported successfully\."]},

    {
        'name': "CRC Selector",
        'path': "/csv_crc",
        'status_code': 200},

    {
        'name': "Dumb NHH supply with DUoS pass-through: "
        "Update Non half-hourlies 2010",
        'path': "/supplier_contracts/16/edit",
        'method': 'post',
        'data': {
            'party_id': '106',
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
        bill[rate_name] = rate_set
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
            r"0068_FINISHED_watkinsexamplecom_supply_virtual_bills_16\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0068_FINISHED_watkinsexamplecom_supply_virtual_bills_16.csv',
        'regexes': [
            r'Imp MPAN Core,Exp MPAN Core,Site Code,Site Name,'],
        'status_code': 200},

    {
        'name': "Leap day forecast. Create scenario",
        'path': '/supplier_contracts/add',
        'method': 'post',
        'data': {
            'participant_id': "70",  # COOP
            'name': "scenario_leap_day",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'charge_script': "",
            'properties': """
{
  "forecast_from": 2009-04-01T00:00:00Z,
  "scenario_start": 2016-02-01T00:00:00Z,
  "scenario_duration": 1}
""", },
        'regexes': [
            r"/supplier_contracts/20"],
        'status_code': 303},

    {
        'name': "Leap day forecast. Run scenario for a site",
        'path': '/reports/247?site_id=5&scenario_id=20&compression=False',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"0069_FINISHED_watkinsexamplecom_scenario_leap_day_20160201_0000_"
            r"for_1_months_site_CH023\.ods"]},
    {
        'path': '/downloads/'
        '0069_FINISHED_watkinsexamplecom_scenario_leap_day_20160201_0000_'
        'for_1_months_site_CH023.ods',
        'status_code': 200,
        'regexes': [

            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:string-value="22 4862 4512 332" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Non half-hourlies 2007" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
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
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="18825.5\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="6"/>\s*'
            r'<table:table-cell office:value="18825.5\d*" '
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
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="18825.559999999998" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.00554" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="104.293602\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="77"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="19"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="18825.5\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="15"/>\s*'
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
            r"0070_FINISHED_watkinsexamplecom_supplies_hh_data_200808012330_"
            r"filter\.csv"]},
    {
        'path': '/downloads/'
        '0070_FINISHED_watkinsexamplecom_supplies_hh_data_200808012330_'
        'filter.csv',
        'status_code': 200,

        # Check the HH data is there
        'regexes': [
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-06,0\.262',
            r"\A\('Connection', 'close'\)\s*"
            r"\('Content-Disposition', 'attachment; "
            r'filename="0070_FINISHED_watkinsexamplecom_supplies_hh_data_'
            r'200808012330_filter.csv"'
            r"'\)\s*"
            r"\('Content-Type', 'text/csv; charset=utf-8'\)\s*"
            r"\('Date', '[^']*'\)\s*"
            r"\('Server', '[^']*'\)\s*"
            r"\('Transfer-Encoding', 'chunked'\)\s*"
            r'Import MPAN Core,Export MPAN Core,Import Related\?,Channel Type,'
            r'Date,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,'
            r'19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,'
            r'40,41,42,43,44,45,46,47\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-01,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-02,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-03,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-04,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-05,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-06,0.262,,0.252,0.246,'
            r'0.249,,0.25,0.249,0.244,0.239,'
            r'0.255,0.255,0.286,0.289,0.356,0.489,0.576,0.585,0.496,0.411,'
            r'0.457,0.463,0.436,0.447,0.436,0.431,0.439,0.396,0.455,0.453,'
            r'0.377,0.314,0.341,0.338,0.418,0.45,0.446,0.442,0.464,0.366,'
            r'0.314,0.386,0.395,0.444,0.346,0.288,0.263,0.255\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-07,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-08,0.299,,,,,,,,,,'
            r',,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,0.933\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-09,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-10,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-11,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-12,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-13,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-14,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-15,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-16,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-17,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-18,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-19,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-20,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-21,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-22,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-23,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-24,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-25,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-26,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-27,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-28,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-29,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-30,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-07-31,*\s*'
            r'NA,22 0470 7514 535,TRUE,ACTIVE,2008-08-01,*\s*'
            r'22 1065 3921 534,NA,TRUE,ACTIVE,2008-07-01,']},

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

    {
        'name': "Supplies TRIAD selector",
        'path': '/csv_supplies_triad',
        'status_code': 200,
        'regexes': [
            r"<!DOCTYPE html>"]},

    {
        'name': "Sites TRIAD selector",
        'path': '/csv_sites_triad',
        'status_code': 200,
        'regexes': [
            r"<!DOCTYPE html>"]},

    {
        'name': "View a MOP bill",
        'path': '/mop_bills/16',
        'status_code': 200,
        'regexes': [
            r'<!DOCTYPE html>',
            r'/mop_bills/16/edit']},

    {
        'name': "Edit a MOP bill",
        'path': '/mop_bills/16/edit',
        'status_code': 200,
        'regexes': [
            r'<!DOCTYPE html>']},

    {
        'name': "CRC for HH supply with HH data",
        'path': '/reports/207?supply_id=2&year=2005',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"0071_FINISHED_watkinsexamplecom_crc_2005_2006_supply_2\.csv"]},
    {
        'path': '/downloads/'
        '0071_FINISHED_watkinsexamplecom_crc_2005_2006_supply_2.csv',
        'status_code': 200,
        'regexes': [
            r'2,2005-04-01 00:00,2006-03-31 23:30,22 9813 2107 763']},

    {
        'name': "CRC for HH supply that straddles eras with missing data",
        'path': '/reports/207?supply_id=7&year=2008',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"0072_FINISHED_watkinsexamplecom_crc_2008_2009_supply_7\.csv"]},
    {
        'path': '/downloads/'
        '0072_FINISHED_watkinsexamplecom_crc_2008_2009_supply_7.csv',
        'status_code': 200,
        'regexes': [
            r'7,2008-04-01 00:00,2009-03-31 23:30,22 4862 4512 332,CH023,'
            r'Treglisson,2008-04-01 00:00,2009-03-31 23:30,,0,127.0,0,0,0,'
            r'365.0,0,0,127.0,365.0,Estimated,0,612952.9400000019,0,0,0,'
            r'1148683.4623622093,1761636.4023622111,']},

    {
        'name': "Contract level MOP virtual bills",
        'path': '/reports/231?mop_contract_id=11&start_year=2015&'
        'start_month=04&start_day=01&start_hour=00&start_minute=00&'
        'finish_year=2015&finish_month=04&finish_day=01&finish_hour=23&'
        'finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'status_code': 200,
        'regexes': [
            r'0073_FINISHED_watkinsexamplecom_mop_virtual_bills\.csv']},
    {
        'path': '/downloads/'
        '0073_FINISHED_watkinsexamplecom_mop_virtual_bills.csv',
        'status_code': 200,
        'regexes': [
            r'Import MPAN Core,Export MPAN Core,Start Date,Finish Date,'
            r'net-gbp,problem',

            r',22 0470 7514 535,2015-04-01 00:00,2015-04-01 23:30,0,']},

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
            r"0074_FINISHED_watkinsexamplecom_supply_virtual_bills_5\.csv"],
        'status_code': 200},
    {
        'name': "Check supplies snapshot at beginning of supply",
        'path': '/downloads/'
        '0074_FINISHED_watkinsexamplecom_supply_virtual_bills_5.csv',
        'regexes': [
            r'22 0883 6932 301,,CI005,Wheal Rodney,4341,'
            r'2014-06-04 00:00,2014-06-04 23:30,,0,,,0,,,'
            r'116.13605\d*,1.008563,,,,5.89,350,1,0.0269,'
            r'9.415000000000001,,,,,0,0.00147,0.0,0,0.00344,0.0,48.9,'
            r'0.25405,12.423045,0.0,0.00399,0.0,1,0.0878,'
            r'0.0878,88,52.5186,0.00021361,0.011218498146,'
            r'52.96831677\d*,,-0.02240461668\d*,0,0.0,0.0,0,'
            r'0.0,0.0,48.9,52.5186,0.32906054015999997,,,,,'
            r',,,,,52.96831\d*,,0.00233272\d*,,,,,,,,,,,,,,,,,,,,,,,,,,'
            r',,,,,,,,,,,,,,,,,,,,,,,,,,,,,'],
        'status_code': 200},
    {
        'name': "Bank holiday day change without restart. Edit the rate "
        "script",
        'path': '/non_core_rate_scripts/5/edit',
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
            r"0075_FINISHED_watkinsexamplecom_supply_virtual_bills_5\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0075_FINISHED_watkinsexamplecom_supply_virtual_bills_5.csv',
        'regexes': [
            r'22 0883 6932 301,,CI005,Wheal Rodney,4341,'
            r'2014-06-04 00:00,2014-06-04 23:30,,0,,,0,,,'
            r'116.1360521\d*,1.008563,,,,5.89,350,1,0.0269,'
            r'9.415000000000001,,,,,0,0.00147,0.0,0,0.00344,0.0,48.9,'
            r'0.25405,12.423045,0.0,0.00399,0.0,1,0.0878,'
            r'0.0878,88,52.5186,0.00021361,0.011218498146,'
            r'52.968316771\d*,,-0.02240461668\d*,0,0.0,0.0,'
            r'48.9,52.5186,0.32906054015999997,,,,,,,,,'
            r',,,,52.96831677\d*,,0.00233272\d*,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,'
            r',,,,,,,,,,,,,,,,,,,,,,,,,'],
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
            r"0076_FINISHED_watkinsexamplecom_crc_2011_2012_supply_10\.csv"],
        'status_code': 200},
    {
        'name': "CRC report for mismatched TPRs",
        'path': '/downloads/'
        '0076_FINISHED_watkinsexamplecom_crc_2011_2012_supply_10.csv',
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
            'gross': '0.00',
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
            'tpr_id': "0",
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
            'tpr_id': "0",
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
            'tpr_id': "0",
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
            r"0077_FINISHED_watkinsexamplecom_crc_2010_2011_supply_10\.csv"],
        'status_code': 200},
    {
        'name': "CRC meter change reads",
        'path': '/downloads/'
        '0077_FINISHED_watkinsexamplecom_crc_2010_2011_supply_10.csv',
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
            'net': "45.70",
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
            r"0078_FINISHED_watkinsexamplecom_supplies_duration\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0078_FINISHED_watkinsexamplecom_supplies_duration.csv',
        'regexes': [
            r'10,2,net,,CI017,Roselands,,2012-01-05 00:00,'
            r'2012-01-10 23:30,03,801,6a,0366,{},MOP Contract,'
            r'mc-22 1065 3921 534,HH contract,dc-22 1065 3921 534,1,nhh,'
            r'2005-09-06 00:00,,110,'
            r'22 1065 3921 534,30,Non half-hourlies 2010,756.0,756.0,'
            r'813.79\d*,5.25,2012-01-05 00:00,None,288,,,,,0,0,0,0,,None,'
        ],
        'status_code': 200},
    {
        'name': "Reads covered by bill without. Run bill check.",
        'path': '/reports/111?bill_id=21',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"0079_FINISHED_watkinsexamplecom_bill_check\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0079_FINISHED_watkinsexamplecom_bill_check.csv',
        'regexes': [
            r'07-002,3423760010,N,10,9.07,0.21,2012-01-05 00:00,'
            r'2012-01-10 23:30,22 1065 3921 534,,CI017,Roselands,'
            r'2012-01-05 00:00,2012-01-10 23:30,21,756.0,9.07,0,9.07,10.0,'
            r'252.0\d*,,'],
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
            r"0080_FINISHED_watkinsexamplecom_supplies_duration\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0080_FINISHED_watkinsexamplecom_supplies_duration.csv',
        'regexes': [
            r'2005-09-06 00:00,2011-01-19 23:30,10,2,net,,CI017,Roselands,,'
            r'2007-02-01 00:00,'
            r'2007-02-28 23:30,03,801,5,0393,{},MOP Contract,'
            r'mc-22 1065 3921 534,Dynamat data,dc-22 1065 3921 534,0,nhh,'
            r'2005-09-06 00:00,,'
            r'110,22 1065 3921 534,30,Non half-hourlies 2010,166.0794\d*,'
            r'166.0794\d*,177.13161\d*,0.2471\d*,2007-02-01 00:00,None,'
            r'1344,,,,,0,0,0,0,,None,'
        ],
        'status_code': 200
    },

    {
        'name': "Supplies duration normal reads with prev, pres the same.",
        'path': '/reads/11/edit',
        'method': 'post',
        'data': {
            'mpan': "2210653921534",
            'coefficient': "1",
            'msn': "I02D89150",
            'units': "kWh",
            'tpr_id': "0",
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
            r"0081_FINISHED_watkinsexamplecom_supplies_duration\.csv"],
        'status_code': 200},
    {
        'name': "Supplies duration normal reads with prev, pres the same.",
        'path': '/downloads/'
        '0081_FINISHED_watkinsexamplecom_supplies_duration.csv',
        'regexes': [
            r'2005-09-06 00:00,2011-01-19 23:30,10,2,net,,CI017,Roselands,,'
            r'2009-04-01 00:00,'
            r'2009-04-10 23:30,03,801,5,0393,\{\},MOP Contract,'
            r'mc-22 1065 3921 534,Dynamat data,dc-22 1065 3921 534,1,nhh,'
            r'2005-09-06 00:00,,'
            r'110,22 1065 3921 534,30,Non half-hourlies 2010,59.314\d*,'
            r'59.3140\d*,63.406\d*,0.24714\d*,2009-04-01 00:00,'
            r'None,480,,,,,0,0,0,0,,None,'
        ],
        'status_code': 200
    },

    {
        'name': "Eras starting after report period.",
        'path': '/reports/247?site_id=3&months=1&finish_year=2003&'
        'finish_month=08&compression=False',
        'status_code': 303},
    {
        'name': "Eras starting after report period.",
        'path': '/downloads',
        'tries': {'max': 20},
        'regexes': [
            r'0082_FINISHED_watkinsexamplecom_monthly_duration_20030801_0000_'
            r'for_1_months_site_CI005\.ods'],
        'status_code': 200},
    {
        'name': "Eras starting after report period.",
        'path': '/downloads/'
        '0082_FINISHED_watkinsexamplecom_monthly_duration_20030801_0000_'
        'for_1_months_site_CI005.ods',
        'regexes': [
            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="Half-hourlies 2013" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:string-value="hh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="displaced" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="4"/>\s*'
            r'<table:table-cell office:string-value="CI005" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Wheal Rodney" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:date-value="2003-08-31T23:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="15"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell table:number-columns-repeated="7"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.00441" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="10"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0023" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="18"/>\s*'
            r'<table:table-cell office:date-value="2017-12-11T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="before start of MPAN" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:date-value="2018-02-05T17:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="before start of MPAN" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:date-value="2018-02-26T18:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="before start of MPAN" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="23.77056" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="1" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="13"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.00016456" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="9"/>\s*'
            r'</table:table-row>'],
        'status_code': 200},

    {
        'name': "Displaced bills for a contract",
        'path': '/reports/109?supplier_contract_id=12&months=1&'
        'finish_year=2005&finish_month=11',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"0083_FINISHED_watkinsexamplecom_displaced\.csv"]},
    {
        'path': '/downloads/0083_FINISHED_watkinsexamplecom_displaced.csv',
        'status_code': 200,
        'regexes': [
            r'CI005,Wheal Rodney,CI004,2005-11-01 00:00,'
            r'2005-11-30 23:30,']},

    # Scenario runner with default scenario
    {
        'name': "Scenario runner with default scenario",
        'path': '/reports/247?site_id=5&months=1&finish_year=2015&'
        'finish_month=2&compression=False',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"0084_FINISHED_watkinsexamplecom_monthly_"
            r"duration_20150201_0000_for_1_months_site_CH023\.ods"]
        },

    {
        'path': '/downloads/'
        '0084_FINISHED_watkinsexamplecom_monthly_'
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
            'tpr_id': "0",
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
            'tpr_id': "0",
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
            'tpr_id': "0",
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
            r"0085_FINISHED_watkinsexamplecom_crc_2010_2011_supply_10\.csv"],
        'status_code': 200},
    {
        'name': "CRC meter change reads",
        'path': '/downloads/'
        '0085_FINISHED_watkinsexamplecom_crc_2010_2011_supply_10.csv',
        'status_code': 200,
        'regexes': [
            r'73142.39335486847']},

    {
        'name': "Monthly Duration - billed amounts",
        'path': '/reports/247?supply_id=10&months=1&finish_year=2010&'
        'finish_month=01&compression=False',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"0086_FINISHED_watkinsexamplecom_monthly_"
            r"duration_20100101_0000_for_1_months_supply_10\.ods"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0086_FINISHED_watkinsexamplecom_monthly_'
        'duration_20100101_0000_for_1_months_supply_10.ods',
        'status_code': 200,
        'regexes': [
            r'<table:table-row>\s*'
            r'<table:table-cell office:string-value="creation-date" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-mpan-core" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-contract" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="exp-mpan-core" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="exp-supplier-contract" '
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
            r'<table:table-cell office:string-value="imp-supplier-00001-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00001-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00001-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00039-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00039-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00039-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00080-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00080-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00080-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00148-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00148-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00148-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00221-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00221-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00221-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'</table:table-row>',

            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:string-value="22 1065 3921 534" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Non half-hourlies 2010" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
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
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
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
            r'<table:table-cell table:number-columns-repeated="15"/>\s*'
            r'</table:table-row>']},

    # Supplier contract 66
    {
        'name': "3rd party in monthly duration report. "
        "Make 3rd-party-reverse.",
        'path': '/supplies/16/edit',
        'method': 'post',
        'data': {
            'name': "3",
            'source_id': "6",
            'generator_type_id': "1",
            'gsp_group_id': "10"},
        'status_code': 303},
    {
        'name': "3rd party in monthly duration report.",
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
            'net': "2.00",
            'vat': "0.50",
            'gross': "2.50",
            'account': "taa2",
            'bill_type_id': "1",
            'breakdown': "{}"},
        'regexes': [
            r"/supplier_bills/23"],
        'status_code': 303},
    {
        'name': "3rd party in monthly duration report.",
        'path': '/supplier_bills/23/add_read',
        'method': 'post',
        'data': {
            'mpan': "03 801 111 22 9789 0534 938",
            'coefficient': "1",
            'msn': "",
            'units': "kWh",
            'tpr_id': "0",
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
        'name': "3rd party in monthly duration report.",
        'path': '/supplier_bills/23',
        'regexes': [
            r"/reads/17"],
        'status_code': 200},
    {
        'name': "3rd party in monthly duration report.",
        'path': '/reports/247?supply_id=16&months=1&finish_year=2014&'
        'finish_month=12&compression=False',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r'0087_FINISHED_watkinsexamplecom_monthly_'
            r'duration_20141201_0000_for_1_months_supply_16\.ods'],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0087_FINISHED_watkinsexamplecom_monthly_'
        'duration_20141201_0000_for_1_months_supply_16.ods',
        'status_code': 200,
        'regexes': [
            r'<table:table table:name="Era Level">\s*'
            r'<table:table-column/>\s*'
            r'<table:table-row>\s*'
            r'<table:table-cell office:string-value="creation-date" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-mpan-core" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-contract" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="exp-mpan-core" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="exp-supplier-contract" '
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
            r'<table:table-cell table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00001-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00001-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00001-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00258-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00258-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00258-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00259-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00259-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00259-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-01218-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-01218-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-01218-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-01219-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-01219-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-01219-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'</table:table-row>\s*'
            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:string-value="22 9789 0534 938" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Non half-hourlies 2010" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
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
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="5"/>\s*'
            r'<table:table-cell office:value="100.06724949562901" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="-100.06724949562901" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="4"/>\s*'
            r'<table:table-cell office:value="10" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="10.006724949562901" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="-0.006724949562901372" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="10.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="2.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="18"/>\s*'
            r'</table:table-row>\s*'
            r'</table:table>']},

    {
        'name': "Dumb NHH supply with DUoS pass-through: "
        "Update Non half-hourlies 2010",
        'path': "/supplier_contracts/16/edit",
        'method': 'post',
        'data': {
            'party_id': '106',
            'name': 'Non half-hourlies 2010',
            'charge_script': """import chellow.duos

def virtual_bill_titles():
    return ['net-gbp', 'sum-msp-kwh', 'problem']

def virtual_bill(supply_source):
    sum_msp_kwh = sum(h['msp-kwh'] for h in supply_source.hh_data)
    bill = supply_source.supplier_bill
    chellow.duos.duos_vb(supply_source)
    for rate_name, rate_set in supply_source.supplier_rate_sets.items():
        bill[rate_name] = rate_set
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
            r"0088_FINISHED_watkinsexamplecom_supply_virtual_bills_16\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0088_FINISHED_watkinsexamplecom_supply_virtual_bills_16.csv',
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
            'gross': '0.00',
            'bill_type_id': '2',
            'breakdown': '{}'},
        'status_code': 303},


    {
        'name': "Monthly duration report for a gen-net supply",
        'path': '/supplies/5/edit',
        'method': 'post',
        'data': {
            'name': "Hello",
            'source_id': "3",
            'generator_type_id': "1",
            'gsp_group_id': "10"},
        'status_code': 303},
    {
        'name': "Monthly duration report for a gen-net supply",
        'path': '/reports/247?supply_id=5&months=1&finish_year=2015&'
        'finish_month=05&compression=False',
        'status_code': 303},
    {
        'name': "Monthly duration report for a gen-net supply",
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r'0089_FINISHED_watkinsexamplecom_monthly_'
            r'duration_20150501_0000_for_1_months_supply_5\.ods'],
        'status_code': 200},
    {
        'name': "Monthly duration report for a gen-net supply",
        'path': '/downloads/'
        '0089_FINISHED_watkinsexamplecom_monthly_'
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
            'tpr_id': "0",
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
            r"0090_FINISHED_watkinsexamplecom_supplies_duration\.csv"],
        'status_code': 200},
    {
        'name': "Supplies duration normal reads with prev, pres the same.",
        'path': '/downloads/'
        '0090_FINISHED_watkinsexamplecom_supplies_duration.csv',
        'regexes': [
            r'2005-09-06 00:00,2011-01-19 23:30,10,2,net,,CI017,Roselands,,'
            r'2009-04-01 00:00,2009-04-10 23:30,03,801,5,0393,{},MOP Contract,'
            r'mc-22 1065 3921 534,Dynamat data,dc-22 1065 3921 534,1,nhh,'
            r'2005-09-06 00:00,,'
            r'110,22 1065 3921 534,30,Non half-hourlies 2010,59.31\d*,'
            r'59.314079422382534,63.40\d*,0.2471\d*,2009-04-01 00:00,None,'
            r'480,,,,,0,0,0,0,,None,'
        ],
        'status_code': 200
    },

    {
        'name': "Monthly Duration report - displaced kWh",
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
        'name': "Monthly Duration report - displaced kWh",
        'path': '/reports/247?site_id=1&months=1&finish_year=2015&'
        'finish_month=05&compression=False',
        'status_code': 303},
    {
        'name': "Monthly Duration report - displaced kWh",
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'regexes': [
            r'0091_FINISHED_watkinsexamplecom_monthly_'
            r'duration_20150501_0000_for_1_months_site_CI004\.ods'],
        'status_code': 200},
    {
        'name': "Monthly Duration report - displaced kWh",
        'path': '/downloads/'
        '0091_FINISHED_watkinsexamplecom_monthly_'
        'duration_20150501_0000_for_1_months_site_CI004.ods',
        'status_code': 200,
        'regexes': [
            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="Half-hourlies 2007" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:string-value="hh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="displaced" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="4"/>\s*'
            r'<table:table-cell office:string-value="CI004" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Lower Treave" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:date-value="2015-05-31T23:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="6"/>\s*'
            r'<table:table-cell office:value="-45.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="7"/>\s*'
            r'<table:table-cell office:value="-0.51779018\d*" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell table:number-columns-repeated="7"/>\s*'
            r'<table:table-cell office:value="-0.517790188\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.00554" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="18"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="-45.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="-48.285\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="-0.30253\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="-48.6984\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="-0.052805692\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="18"/>\s*'
            r'<table:table-cell office:date-value="2014-12-04T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="E" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.085" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:date-value="2015-01-19T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="E" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.085" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:date-value="2015-02-02T17:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="E" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.085" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="43.979049" '
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
            r'<table:table-cell office:value="0.00129" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="-45.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.00361" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="-0.1624\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.20511" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="28"/>\s*'
            r'</table:table-row>\s*',

            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:string-value="22 7907 4116 080" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Half-hourlies 2007" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="hh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="gen" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="chp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="2" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="00" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="CI004" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Lower Treave" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:date-value="2015-05-31T23:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell office:value="45.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="5"/>\s*'
            r'<table:table-cell office:value="10" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="6"/>\s*'
            r'<table:table-cell office:value="10" '
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
            r'<table:table-cell table:number-columns-repeated="122"/>\s*'
            r'<table:table-cell office:value="93.9298901\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.00554" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="5.89" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="600" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="31" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell table:number-columns-repeated="8"/>\s*'
            r'<table:table-cell office:value="0.0016" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="88" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="45.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="48.285\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.3025\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="48.6984\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0.052805692\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="18"/>\s*'
            r'<table:table-cell office:date-value="2014-12-04T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.085" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:date-value="2015-01-19T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.085" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:date-value="2015-02-02T17:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.085" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="43.979049" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="1" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'</table:table-row>\s*']},

    {
        'name': "Monthly duration supply starts after period",
        'path': '/reports/247?supply_id=7&months=1&finish_year=2003&'
        'finish_month=08&compression=False',
        'status_code': 303},
    {
        'name': "Monthly duration supply starts after period",
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'regexes': [
            r'0092_FINISHED_watkinsexamplecom_monthly_'
            r'duration_20030801_0000_for_1_months_supply_7\.ods'],
        'status_code': 200},
    {
        'name': "Monthly duration supply starts after period",
        'path': '/downloads/'
        '0092_FINISHED_watkinsexamplecom_monthly_'
        'duration_20030801_0000_for_1_months_supply_7.ods',
        'status_code': 200,
        'regexes': [
            r'22 4862 4512 332']},

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
            'mop_contract_id': "11",
            'mop_account': "mc-22 7907 4116 080",
            'dc_contract_id': "9",
            'dc_account': "01",
            'msn': "",
            'pc_id': "0",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'properties': "{}",
            'exp_llfc_code': "581",
            'exp_mpan_core': "22 7907 4116 080",
            'exp_sc': "600",
            'exp_supplier_contract_id': "10",
            'exp_supplier_account': ""
        },
        'status_code': 303
    },

    {
        'name': "Montly duration report, billed: "
        "add batch to Dynamat contract",
        'path': '/dc_contracts/9/add_batch',
        'method': 'post',
        'data': {
            'reference': "Zathustra",
            'description': "Thus spoke."},
        'status_code': 303,
        'regexes': [
            r"/dc_batches/15"]},
    {
        'name': "Monthly duration report, billed: add bill to batch",
        'path': '/dc_batches/14/add_bill',
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
            r"/dc_bills/24"]},
    {
        'name': "Monthly duration report, billed",
        'path': '/reports/247?site_id=1&months=1&finish_year=2015&'
        'finish_month=08&compression=False',
        'status_code': 303},
    {
        'name': "Monthly duration report, billed",
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'regexes': [
            r'0093_FINISHED_watkinsexamplecom_monthly_'
            r'duration_20150801_0000_for_1_months_site_CI004\.ods'],
        'status_code': 200},
    {
        'name': "Monthly duration report, billed",
        'path': '/downloads/'
        '0093_FINISHED_watkinsexamplecom_monthly_'
        'duration_20150801_0000_for_1_months_site_CI004.ods',
        'status_code': 200,
        'regexes': [
            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:string-value="22 7907 4116 080" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Half-hourlies 2007" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="hh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="gen" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="chp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="2" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="00" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="CI004" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Lower Treave" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:date-value="2015-08-31T23:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="9"/>\s*'
            r'<table:table-cell office:value="17" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="6"/>\s*'
            r'<table:table-cell office:value="17" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="11.2" '
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
            r'<table:table-cell table:number-columns-repeated="122"/>\s*'
            r'<table:table-cell office:value="93.89" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.00554" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="5.89" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="600" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="31" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell table:number-columns-repeated="8"/>\s*'
            r'<table:table-cell office:value="0.0016" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="88" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="18"/>\s*'
            r'<table:table-cell office:date-value="2014-12-04T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.085" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:date-value="2015-01-19T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.085" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:date-value="2015-02-02T17:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.085" '
            r'office:value-type="float"/>\s*'
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
            'mop_contract_id': "11",
            'mop_account': "22 0883 6932 301",
            'dc_contract_id': "8",
            'dc_account': "22 0883 6932 301",
            'msn': "",
            'pc_id': "0",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'properties': "{}",
            'imp_llfc_code': "510",
            'imp_mpan_core': "22 0883 6932 301",
            'imp_sc': "350",
            'imp_supplier_contract_id': "12",
            'imp_supplier_account': "4341",
            'exp_llfc_code': "521",
            'exp_mpan_core': "22 6158 2968 220",
            'exp_sc': "20",
            'exp_supplier_contract_id': "12",
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
            'mop_contract_id': "11",
            'mop_account': "22 0883 6932 301",
            'dc_contract_id': "8",
            'dc_account': "22 0883 6932 301",
            'msn': "",
            'pc_id': "0",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'properties': "{}",
            'imp_llfc_code': "570",
            'imp_mpan_core': "22 0883 6932 301",
            'imp_sc': "350",
            'imp_supplier_contract_id': "12",
            'imp_supplier_account': "413",
            'exp_llfc_code': "581",
            'exp_mpan_core': "22 7824 9120 097",
            'exp_sc': "150",
            'exp_supplier_contract_id': "12",
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
            r"0094_FINISHED_watkinsexamplecom_supply_virtual_bills_5\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0094_FINISHED_watkinsexamplecom_supply_virtual_bills_5.csv',
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
            r"0095_FINISHED_watkinsexamplecom_supply_virtual_bills_10\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0095_FINISHED_watkinsexamplecom_supply_virtual_bills_10.csv',
        'regexes': [
            r'3409.15883838'],
        'status_code': 200},

    {
        'name': "Test displaced virtual bill with generation",
        'path': '/reports/247?site_id=3&months=1&finish_year=2005&'
        'finish_month=11&compression=False',
        'status_code': 303},
    {
        'name': "Test displaced virtual bill with generation",
        'path': '/downloads',
        'tries': {'max': 20},
        'regexes': [
            r'0096_FINISHED_watkinsexamplecom_monthly_duration_20051101_0000_'
            r'for_1_months_site_CI005\.ods'],
        'status_code': 200},
    {
        'name': "Test displaced virtual bill with generation",
        'path': '/downloads/'
        '0096_FINISHED_watkinsexamplecom_monthly_duration_20051101_0000_for_1_'
        r'months_site_CI005.ods',
        'regexes': [
            r'"CI005"'],
        'status_code': 200},

    {
        'name': "GSP Groups",
        'path': '/gsp_groups',
        'status_code': 200},

    {
        'name': 'Wildcard user. Add config.',
        'path': '/non_core_contracts/3/edit',
        'method': 'post',
        'data': {
            'name': "configuration",
            'properties': """
{
    "ips": {"*.*.*.*": "watkins@example.com"},
    "site_links": [
        {"name": "Google Maps", "href": "https://maps.google.com/maps?q="}],
    "batch_reports": [1],
    "elexonportal_scripting_key": "xxx",
    "ecoes": {
        "user_name": "a",
        "password": "a",
        "prefix": "http://localhost:8080/ecoes/"},
    "background_colour": "aquamarine"}
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
        'path': '/non_core_contracts/1/edit',
        'method': 'post',
        'data': {
            'properties': """
{
  "enabled": true,
  "url": "http://127.0.0.1:8080/nationalgrid/england-and-wales.ics"}
"""},
        'status_code': 303},
    {
        'name': "Do an 'import now'.",
        'path': '/non_core_contracts/1/auto_importer',
        'method': 'post',
        'data': {
            'now': 'Now'},
        'status_code': 303},
    {
        'name': "Check that an import has happened.",
        'path': '/non_core_contracts/1/auto_importer',
        'tries': {'max': 20},
        'regexes': [
            r'<ul>\s*<li>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} - '
            r'Finished checking bank holidays.</li>',
            r'Updated rate script starting at',
            r'<a\s*'
            r'href="/non_core_contracts/1/auto_importer"\s*'
            r'>Refresh page</a>'],
        'status_code': 200},
    {
        'name': "Set up RCRC downloader",
        'path': '/non_core_contracts/5/edit',
        'method': 'post',
        'data': {
            'properties': """
{
            "enabled": true,
            "url": "http://127.0.0.1:8080/elexonportal/"}
"""},
        'status_code': 303},
    {
        'name': "Do an 'import now' on RCRC.",
        'path': '/non_core_contracts/5/auto_importer',
        'method': 'post',
        'data': {
            'now': 'Now'},
        'status_code': 303},
    {
        'name': "Check that an RCRC import has happened.",
        'path': '/non_core_contracts/5/auto_importer',
        'tries': {},
        'regexes': [
            r"Added a new rate script starting at 2016-01-01 00:00\."],
        'status_code': 200},
    {
        'name': "Is the rate script correct?",
        'path': '/non_core_rate_scripts/50',
        'regexes': [
            r"&#34;01 00:00 Z&#34;: "
            r"0\.092536082309507475102132933090071710251,"],
        'status_code': 200},
    {
        'name': "Do an 'import now' on RCRC.",
        'path': '/non_core_contracts/5/auto_importer',
        'method': 'post',
        'data': {
            'now': 'Now'},
        'status_code': 303},
    {
        'name': "Check that an RCRC import has happened.",
        'path': '/non_core_contracts/5/auto_importer',
        'tries': {},
        'regexes': [
            r"Added a new rate script starting at 2016-02-01 00:00\."],
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
        'name': "Supplier contract 11, batch 4",
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
            r'Channel Import\s*ACTIVE',
            r'<form method="post" action="/channels/40/edit">']},

    {
        'name': "Look at a LLFC",
        'path': '/llfcs/6128',
        'status_code': 200},

    {
        'name': "Look at edit LLFC",
        'path': '/llfcs/6128/edit',
        'status_code': 200,
        'regexes': [
            r'<a\s*'
            r'href="/llfcs/6128"\s*'
            r'>128 2010-03-17 00:00</a>']},

    {
        'name': "A DNO's LLFCs",
        'path': '/llfcs?dno_id=160',
        'status_code': 200,
        'regexes': [
            r'<a href="/dnos">DNOs</a>']},

    {
        'name': "Comparison against ECOES",
        'path': '/reports/ecoes_comparison',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"0000_FINISHED_adminexamplecom_ecoes_comparison\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0000_FINISHED_adminexamplecom_ecoes_comparison.csv',
        'status_code': 200,
        'regexes': [
            r'MPAN Core,MPAN Core No Spaces,ECOES PC,Chellow PC,ECOES MTC,'
            r'Chellow MTC,ECOES LLFC,Chellow LLFC,ECOES SSC,Chellow SSC,'
            r'ECOES Supplier,Chellow Supplier,ECOES DC,Chellow DC,ECOES MOP,'
            r'Chellow MOP,ECOES GSP Group,Chellow GSP Group,ECOES MSN,'
            r'Chellow MSN,ECOES Meter Type,Chellow Meter Type,Problem',
            r'14 7206 6139 971,1472066139971,,00,,845,,365,,,,BIZZ,,DASL,,'
            r'LENG,,_E,,88jiuf ff,,H,"In Chellow, but not in ECOES."']},

    {
        'name': "View a CoP",
        'path': '/cops/5',
        'status_code': 200},

    {
        'name': "View an DC bill",
        'path': '/dc_bills/15',
        'status_code': 200},

    {
        'name': "Edit view of an DC bill",
        'path': '/dc_bills/15/edit',
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
            r"0001_FINISHED_adminexamplecom_supplies_snapshot\.csv"],
        'status_code': 200},
    {
        'name': "Check supplies snapshot at beginning of supply",
        'path': '/downloads/'
        '0001_FINISHED_adminexamplecom_supplies_snapshot.csv',
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
            'gsp_group_id': "10"},
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
            r'height="16.0px" fill="blue">\s*'
            r'<title>2\.0 kW @ 2005-09-15 00:00</title>\s*'
            r'</rect>']},

    {
        'name': "Site generation graph stradling groups",
        'path': '/sites/3/gen_graph?months=2&finish_year=2005&finish_month=10',
        'status_code': 200,
        'regexes': [
            r'<text x="672px" y="214.0px">\s*'
            r'September\s*'
            r'</text>\s*'
            r'<text x="2112px" y="214.0px">\s*'
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
        'name': "Ignore channel snag",
        'path': '/channel_snags/100',
        'status_code': 200,
        'regexes': [
            r'<td>\s*'
            r'Ignored\s*'
            r'</td>']},

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
            'vat': '-112.29',
            'gross': '0.00',
            'bill_type_id': '2',
            'breakdown': '{}'},
        'status_code': 303},
    {
        'name': "Bill check with exception",
        'path': "/supplier_contracts/16/edit",
        'method': 'post',
        'data': {
            'party_id': '106',
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
        bill[rate_name] = rate_set
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
            r"0002_FINISHED_adminexamplecom_bill_check\.csv"],
        'status_code': 200},
    {
        'name': "Bill check with exception",
        'path': '/downloads/'
        '0002_FINISHED_adminexamplecom_bill_check.csv',
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
            r"0003_FINISHED_adminexamplecom_supply_virtual_bills_10\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0003_FINISHED_adminexamplecom_supply_virtual_bills_10.csv',
        'regexes': [
            r'Theory laden\.'],
        'status_code': 200},
    {
        'name': "Bill check with exception. Put back to how it was.",
        'path': "/supplier_contracts/16/edit",
        'method': 'post',
        'data': {
            'party_id': '106',
            'name': 'Non half-hourlies 2010',
            'charge_script': """def virtual_bill_titles():
    return ['net-gbp', 'sum-msp-kwh', 'problem']

def virtual_bill(supply_source):
    sum_msp_kwh = sum(h['msp-kwh'] for h in supply_source.hh_data)
    bill = supply_source.supplier_bill
    for rate_name, rate_set in supply_source.supplier_rate_sets.items():
        bill[rate_name] = rate_set
    bill['net-gbp'] += sum_msp_kwh * 0.1
    bill['sum-msp-kwh'] += sum_msp_kwh
""",
            'properties': '{}'},
        'status_code': 303},

    {
        'name': "Reverse proxy authentication",
        'path': '/non_core_contracts/3/edit',
        'method': 'post',
        'data': {
            'name': "configuration",
            'properties': """
{
    "site_links": [
        {"name": "Google Maps", "href": "https://maps.google.com/maps?q="}],
    "batch_reports": [1],
    "elexonportal_scripting_key": "xxx",
    "ecoes": {
        "user_name": "a",
        "password": "a",
        "prefix": "http://localhost:8080/ecoes/"},
    "background_colour": "aquamarine",
    "ad_authentication": {
        "on": true,
        "default_user": "admin@example.com"}}
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
        'path': '/non_core_contracts/3/edit',
        'method': 'post',
        'headers': {
            'X-Isrw-Proxy-Logon-User': 'admin@example.com'},
        'data': {
            'name': "configuration",
            'properties': """
{
  "site_links": [
      {"name": "Google Maps", "href": "https://maps.google.com/maps?q="}],
  "batch_reports": [1],
  "elexonportal_scripting_key": "xxx",
  "ecoes": {
    "user_name": "a",
    "password": "a",
    "prefix": "http://localhost:8080/ecoes/"},
  "background_colour": "aquamarine"}
""", },
        'status_code': 303},

    {
        'name': "View site snag edit",
        'path': '/site_snags/41/edit',
        'auth': ('admin@example.com', 'admin'),
        'regexes': [
            r'<form'],
        'status_code': 200},
    {
        'name': "Attempt to delete an DC contract that has batches",
        'path': '/dc_contracts/9/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'regexes': [
            r'Can&#39;t delete a contract that has batches\.'],
        'status_code': 400},
    {
        'name': "View add DC rate script",
        'path': '/dc_contracts/9/add_rate_script',
        'status_code': 200},
    {
        'name': "View add mop bill.",
        'path': '/mop_batches/9/add_bill',
        'status_code': 200},

    {
        'name': "Bill that cancel, bill check.",
        'path': '/supplier_bills/14/edit',
        'method': 'post',
        'data': {
            'reference': 'SA342376',
            'account': '21767837',
            'issue_year': '2007',
            'issue_month': '01',
            'issue_day': '01',
            'issue_hour': '00',
            'issue_minute': '00',
            'start_year': '2007',
            'start_month': '02',
            'start_day': '28',
            'start_hour': '00',
            'start_minute': '00',
            'finish_year': '2007',
            'finish_month': '03',
            'finish_day': '01',
            'finish_hour': '00',
            'finish_minute': '00',
            'kwh': '0',
            'net': '3163479.00',
            'vat': '553609.00',
            'gross': '0.00',
            'bill_type_id': '2',
            'breakdown': '{}'},
        'status_code': 303},

    {
        'name': "Test the supplier batch checking",
        'path': '/reports/111?bill_id=14',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"0004_FINISHED_adminexamplecom_bill_check\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/0004_FINISHED_adminexamplecom_bill_check.csv',
        'status_code': 200},

    {
        'name': "Bill that cancel, bill check with primary bill.",
        'path': '/supplier_bills/12/edit',
        'method': 'post',
        'data': {
            'reference': '3423760004',
            'account': 'SA342376000',
            'issue_year': '2007',
            'issue_month': '01',
            'issue_day': '01',
            'issue_hour': '00',
            'issue_minute': '00',
            'start_year': '2007',
            'start_month': '02',
            'start_day': '28',
            'start_hour': '00',
            'start_minute': '00',
            'finish_year': '2007',
            'finish_month': '03',
            'finish_day': '01',
            'finish_hour': '00',
            'finish_minute': '00',
            'kwh': '150',
            'net': '98.17',
            'vat': '15.01',
            'gross': '0.00',
            'bill_type_id': '2',
            'breakdown': '{}'},
        'status_code': 303},
    {
        'name': "Test the supplier batch checking",
        'path': '/reports/111?bill_id=14',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"0005_FINISHED_adminexamplecom_bill_check\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0005_FINISHED_adminexamplecom_bill_check.csv',
        'regexes': [
            r'batch,bill-reference,bill-type,bill-kwh,bill-net-gbp,'
            r'bill-vat-gbp,bill-start-date,bill-finish-date,imp-mpan-core,'
            r'exp-mpan-core,site-code,site-name,covered-from,covered-to,'
            r'covered-bills,metered-kwh,covered-ccl-kwh,virtual-ccl-kwh,'
            r'covered-ccl-rate,virtual-ccl-rate,covered-ccl-gbp,'
            r'virtual-ccl-gbp,difference-ccl-gbp,covered-net-gbp,'
            r'virtual-net-gbp,difference-net-gbp,covered-vat-gbp,'
            r'virtual-vat-gbp,difference-vat-gbp,covered-gross-gbp,'
            r'virtual-gross-gbp,difference-gross-gbp,covered-sum-msp-kwh,'
            r'virtual-sum-msp-kwh,covered-problem,virtual-problem\s*\Z'
        ],
        'status_code': 200
    },

    {
        'name': "Update a MOP batch",
        'path': '/mop_batches/9/edit',
        'method': 'post',
        'data': {
            'reference': "99/992",
            'description': "mop batch"},
        'status_code': 303,
        'regexes': [
            r'/mop_batches/9']},
    {
        'name': "Mop bill imports for a batch",
        'path': '/mop_bill_imports?mop_batch_id=9',
        'status_code': 200},
    {
        'name': "Monthly duration Report: gen-net",
        'path': '/reports/247?supply_id=5&months=1&finish_year=2014&'
        'finish_month=06&compression=False',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 40, 'period': 1},
        'regexes': [
            r'0006_FINISHED_adminexamplecom_monthly_'
            r'duration_20140601_0000_for_1_months_supply_5\.ods'],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0006_FINISHED_adminexamplecom_monthly_duration_'
        '20140601_0000_for_1_months_supply_5.ods',
        'regexes': [
            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:string-value="22 0883 6932 301" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Half-hourlies 2013" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="22 7824 9120 097" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Half-hourlies 2013" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="hh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="gen-net" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="chp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Hello" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="00" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="CI005" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Wheal Rodney" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:date-value="2014-06-30T23:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="48.9" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="48.9" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell office:value="48.9" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="401.717\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="93.89" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="5"/>\s*'
            r'<table:table-cell office:value="401.717\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell table:number-columns-repeated="19"/>\s*'
            r'</table:table-row>'],
        'status_code': 200},

    {
        'name': "Non-core contract without module (configuration)",
        'path': '/non_core_contracts/3',
        'status_code': 200},

    {
        'name': "NHH bill with triad: Update Non half-hourlies 2010:",
        'path': "/supplier_contracts/16/edit",
        'method': 'post',
        'data': {
            'party_id': '106',
            'name': 'Non half-hourlies 2010',
            'charge_script': """import chellow.duos
import chellow.triad
from chellow.computer import is_tpr
from chellow.models import Tpr, MeasurementRequirement

def virtual_bill_titles():
    return ['net-gbp', 'problem']

def virtual_bill(ss):
    bill = ss.supplier_bill
    chellow.duos.duos_vb(ss)
    chellow.triad.hh(ss)
    chellow.ro.hh(ss)
    tpr_codes = [
        t[0] for t in ss.sess.query(Tpr.code).join(MeasurementRequirement).
        filter(MeasurementRequirement.ssc == ss.ssc)]
    for hh in ss.hh_data:
        for tpr_code in tpr_codes:
            if is_tpr(ss.sess, ss.caches, tpr_code, hh['start-date']):
                rate = 0.1
                ss.supplier_rate_sets[tpr_code + '-rate'].add(rate)
                bill[tpr_code + '-kwh'] += hh['msp-kwh']
                bill[tpr_code + '-gbp'] += hh['msp-kwh'] * rate

    for rate_name, rate_set in ss.supplier_rate_sets.items():
        bill[rate_name] = rate_set
    bill['net-gbp'] = sum(v for k, v in bill.items() if k.endswith('-gbp'))
""",
            'properties': '{}'},
        'status_code': 303},
    {
        'name': "Test the supplier batch checking",
        'path': '/reports/111?bill_id=23',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 40, 'period': 1},
        'regexes': [
            r'0007_FINISHED_adminexamplecom_bill_check.csv'],
        'status_code': 200},
    {
        'path': '/downloads/0007_FINISHED_adminexamplecom_bill_check.csv',
        'regexes': [
            r'07-002,3Pb,F,10,2.00,0.50,2014-12-01 00:00,2014-12-31 23:30,'
            r'22 9789 0534 938,,CI017,Roselands,2014-12-01 00:00,'
            r'2014-12-31 23:30,23,100.06724\d*,2.0,0,2.0,,'],
        'status_code': 200},

    {
        'name': "Monthly duration report for site with only generation",
        'path': '/eras/4/edit',
        'method': 'post',
        'data': {
            'site_code': "CI004",
            'attach': "Attach"},
        'status_code': 303},
    {
        'name': "Monthly duration report for site with only generation",
        'path': '/eras/4/edit',
        'method': 'post',
        'data': {
            'era_id': '4',
            'site_id': '1',
            'locate': "Locate"},
        'status_code': 303},
    {
        'name': "Monthly duration report for site with only generation",
        'path': '/reports/247?site_id=1&months=1&finish_year=2015&'
        'finish_month=05&compression=False',
        'status_code': 303},
    {
        'name': "Monthly duration report for site with only generation",
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'regexes': [
            r'0008_FINISHED_adminexamplecom_monthly_'
            r'duration_20150501_0000_for_1_months_site_CI004\.ods'],
        'status_code': 200},
    {
        'name': "Monthly duration report for site with only generation",
        'path': '/downloads/'
        '0008_FINISHED_adminexamplecom_monthly_'
        'duration_20150501_0000_for_1_months_site_CI004.ods',
        'status_code': 200,
        'regexes': [
            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:string-value="CI004" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Lower Treave" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="CI005" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:date-value="2015-05-31T23:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:string-value="hh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="gen, net" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="chp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="25.819178082191478" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="45.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="-45.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="-19.180821917808522" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="752.9111\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="198.4626" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="4"/>\s*'
            r'<table:table-cell office:value="-0.372128492\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="752.538971\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="3"/>\s*'
            r'</table:table-row>']},

    {
        'name': "Monthly duration report for site with no supplies",
        'path': '/reports/247?site_id=8&months=1&finish_year=2015&'
        'finish_month=05&compression=False',
        'status_code': 303},
    {
        'name': "Monthly duration report for site with no supplies",
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'regexes': [
            r'0009_FINISHED_adminexamplecom_monthly_'
            r'duration_20150501_0000_for_1_months_site_MOBY\.ods'],
        'status_code': 200},
    {
        'name': "Monthly duration report for site with no supplies",
        'path': '/downloads/'
        '0009_FINISHED_adminexamplecom_monthly_'
        'duration_20150501_0000_for_1_months_site_MOBY.ods',
        'status_code': 200,
        'regexes': [
            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:string-value="MOBY" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Ishmael" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:date-value="2015-05-31T23:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="20"/>\s*'
            r'</table:table-row>']},

    {
        'name': "Site level HH data, row per hh",
        'path': '/reports/csv_site_hh_data?site_id=7&start_year=2016&'
        'start_month=09&start_day=1&start_hour=0&start_minute=0&'
        'finish_year=2016&finish_month=09&finish_day=30&finish_hour=23&'
        'finish_minute=30',
        'status_code': 303},
    {
        'name': "Site level HH data, row per hh",
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'regexes': [
            r'0010_FINISHED_adminexamplecom_site_hh_data\.csv'],
        'status_code': 200},
    {
        'name': "Site level HH data, row per hh",
        'path': '/downloads/0010_FINISHED_adminexamplecom_site_hh_data.csv',
        'status_code': 200,
        'regexes': [
            r'CH017,Parbola,,3rd-party,,2016-09-01 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-01 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-02 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-03 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-04 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-05 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-06 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-07 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-08 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-09 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-10 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-11 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-12 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-13 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-14 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-15 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-16 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-17 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-18 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-19 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-20 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-21 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-22 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-23 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-24 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-25 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-26 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-27 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-28 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-29 23:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 00:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 00:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 01:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 01:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 02:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 02:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 03:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 03:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 04:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 04:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 05:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 05:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 06:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 06:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 07:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 07:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 08:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 08:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 09:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 09:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 10:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 10:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 11:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 11:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 12:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 12:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 13:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 13:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 14:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 14:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 15:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 15:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 16:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 16:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 17:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 17:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 18:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 18:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 19:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 19:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 20:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 20:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 21:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 21:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 22:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 22:30,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 23:00,0,0,0,0,0,0,hh\s*'
            r'CH017,Parbola,,3rd-party,,2016-09-30 23:30,0,0,0,0,0,0,hh\s*'
            r'\Z']},

    {
        'name': "SSE EDI bill with multiple rates for an element",
        'path': '/supplier_contracts/16/add_batch',
        'method': 'post',
        'data': {
            'reference': "07-009",
            'description': "Multiple rate batch"},
        'status_code': 303,
        'regexes': [
            r"/supplier_batches/16"]},
    {
        'name': "SSE EDI bill with multiple rates for an element",
        'path': '/supplier_bill_imports',
        'method': 'post',
        'data': {
            'supplier_batch_id': '16'},
        'files': {'import_file': 'test/bills3.sse.edi'},
        'status_code': 303,
        'regexes': [
            r"/supplier_bill_imports/12"]},
    {
        'name': "SSE EDI bill with multiple rates for an element",
        'path': '/supplier_bill_imports/12',
        'tries': {},
        'regexes': [
            r'\(&#39;fit-rate&#39;, &#39;0.00205, 0.00206&#39;\)'],
        'status_code': 200},

    {
        'name': "Check months before and after forecast for NHH",
        'path': '/local_reports/1',
        'method': 'post',
        'data': {
            'name': 'Minority Report',
            'script': """from chellow.models import Session
from chellow.computer import datum_range
from datetime import datetime as Datetime
import pytz


sess = None
try:
    caches = {}
    sess = Session()
    t = Datetime(2010, 10, 1, tzinfo=pytz.utc)
    datum1 = datum_range(sess, caches, 0, t, t)
    datum2 = datum_range(sess, caches, 1, t, t)
    if datum1 == datum2:
        raise Exception("datums match!")
    response = 'Henriki'
finally:
    if sess is not None:
        sess.close()
""",
            'template': ''},
        'status_code': 303},
    {
        'name': "Run a local report",
        'path': '/local_reports/1/output',
        'status_code': 200,
        'regexes': [
            r'Henriki']},

    {
        'name': "Engie XLS Bills",
        'path': '/eras/8/edit',
        'method': 'post',
        'data': {
            'start_year': "2006",
            'start_month': "07",
            'start_day': "20",
            'start_hour': "00",
            'start_minute': "00",
            'is_ended': "false",
            'mop_contract_id': "11",
            'mop_account': "mc-22 9813 2107 763",
            'dc_contract_id': "8",
            'dc_account': "01",
            'msn': "",
            'pc_id': "0",
            'mtc_code': "845",
            'cop_id': "5",
            'ssc_code': "",
            'properties': "{}",
            'imp_llfc_code': "570",
            'imp_mpan_core': "22 9813 2107 763",
            'imp_sc': "430",
            'imp_supplier_contract_id': '10',
            'imp_supplier_account': '22 9813 2107 763',
            'exp_llfc_code': '581',
            'exp_mpan_core': '22 3475 1614 211',
            'exp_sc': "900",
            'exp_supplier_contract_id': '10',
            'exp_supplier_account': '4341'},
        'status_code': 303},
    {
        'name': "Engie XLS Bills",
        'path': '/supplier_contracts/10/add_batch',
        'method': 'post',
        'data': {
            'reference': "009",
            'description': "Engie XLS batch"},
        'status_code': 303,
        'regexes': [
            r"/supplier_batches/17"]},

    {
        'name': "Engie XLS Bills",
        'path': '/supplier_bill_imports',
        'method': 'post',
        'data': {
            'supplier_batch_id': '17'},
        'files': {'import_file': 'test/bills.engie.xls'},
        'status_code': 303,
        'regexes': [
            r"/supplier_bill_imports/13"]},

    {
        'name': "Engie XLS Bills",
        'path': '/supplier_bill_imports/13',
        'tries': {},
        'regexes': [
            r'<tr>\s*'
            r'<td>99708221.0_2_bsuos</td>\s*'
            r'<td>22 9813 2107 763</td>\s*'
            r'<td>N</td>\s*'
            r'<td></td>\s*'
            r'<td>2016-09-13 23:00</td>\s*'
            r'<td>2016-07-31 23:00</td>\s*'
            r'<td>2016-08-31 22:30</td>\s*'
            r'<td>0</td>\s*'
            r'<td>770.69</td>\s*'
            r'<td>0.00</td>\s*'
            r'<td>770.69</td>\s*'
            r'<td>\[\(&#39;bsuos-gbp&#39;, Decimal\(&#39;770.69&#39;\)\), ',

            r'<tr>\s*'
            r'<td>99708221.0_8_bsuos</td>\s*'
            r'<td>22 9813 2107 763</td>\s*'
            r'<td>N</td>\s*'
            r'<td></td>\s*'
            r'<td>2016-09-13 23:00</td>\s*'
            r'<td>2016-07-31 23:00</td>\s*'
            r'<td>2016-08-31 22:30</td>\s*'
            r'<td>0</td>\s*'
            r'<td>611.00</td>\s*'
            r'<td>0.00</td>\s*'
            r'<td>611.00</td>\s*'
            r'<td>\[\(&#39;bsuos-gbp&#39;, Decimal\(&#39;611.0&#39;\)\), '
            r'\(&#39;bsuos-nbp-kwh&#39;, Decimal\(&#39;23971.88&#39;\)\), '
            r'\(&#39;bsuos-rate&#39;, \[Decimal\(&#39;0.0911&#39;\)\]\), ',

            r'<tr>\s*'
            r'<td>99708221.0_9_aahedc</td>\s*'
            r'<td>22 9813 2107 763</td>\s*'
            r'<td>N</td>\s*'
            r'<td></td>\s*'
            r'<td>2016-09-13 23:00</td>\s*'
            r'<td>2016-07-31 23:00</td>\s*'
            r'<td>2016-08-31 22:30</td>\s*'
            r'<td>0</td>\s*'
            r'<td>0.89</td>\s*'
            r'<td>0.00</td>\s*'
            r'<td>0.89</td>\s*'
            r'<td>\[\(&#39;aahedc-gbp&#39;, Decimal\(&#39;0.89&#39;\)\), '
            r'\(&#39;aahedc-gsp-kwh&#39;, Decimal\(&#39;55866.88&#39;\)\), '
            r'\(&#39;aahedc-rate&#39;, '
            r'\[Decimal\(&#39;0.0088658712&#39;\)\]\), ',

            r"All the bills have been successfully loaded and attached to "
            r"the batch\."],
        'status_code': 200},

    {
        'name': "Engie XLS Bills",
        'path': '/supplier_batches/17',
        'regexes': [
            r'<td>2016-09-13 23:00</td>\s*'
            r'<td>2016-07-31 23:00</td>\s*'
            r'<td>2016-08-31 22:30</td>\s*'
            r'<td>0</td>\s*'
            r'<td>571.25</td>\s*'
            r'<td>0.00</td>\s*'
            r'<td>571.25</td>\s*'
        ],
        'status_code': 200},

    {
        'name': "Engie XLS Bills",
        'path': '/supplier_bill_imports',
        'method': 'post',
        'data': {
            'supplier_batch_id': '17'},
        'files': {'import_file': 'test/bills_fail.engie.xls'},
        'status_code': 303,
        'regexes': [
            r"/supplier_bill_imports/14"]},

    {
        'name': "Engie XLS Bills",
        'path': '/supplier_bill_imports/14',
        'tries': {},
        'regexes': [
            r'Can&#39;t find a bill finish date in row 4\.'],
        'status_code': 200},

    {
        'name': "Contract level MOP virtual bills, straddling eras",
        'path': '/reports/231?mop_contract_id=11&start_year=2008&'
        'start_month=09&start_day=05&start_hour=00&start_minute=00&'
        'finish_year=2008&finish_month=09&finish_day=06&finish_hour=23&'
        'finish_minute=30',
        'status_code': 303},
    {
        'name': "Contract level MOP virtual bills, straddling eras",
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'status_code': 200,
        'regexes': [
            r'0011_FINISHED_adminexamplecom_mop_virtual_bills\.csv']},
    {
        'name': "Contract level MOP virtual bills, straddling eras",
        'path': '/downloads/'
        '0011_FINISHED_adminexamplecom_mop_virtual_bills.csv',
        'status_code': 200,
        'regexes': [
            r',22 0470 7514 535,2008-09-05 00:00,2008-09-05 23:30,0,\s*'
            r',22 0470 7514 535,2008-09-06 00:00,2008-09-06 23:30,0,']},

    {
        'name': "Check TPRs in virtual bill",
        'path': '/reports/291?supply_id=16&start_year=2014&'
        'start_month=12&start_day=01&start_hour=00&start_minute=00&'
        'finish_year=2014&finish_month=12&finish_day=31&finish_hour=23&'
        'finish_minute=30',
        'status_code': 303},
    {
        'name': "Check TPRs in virtual bill",
        'path': '/downloads',
        'tries': {'max': 30},
        'status_code': 200,
        'regexes': [
            r'0012_FINISHED_adminexamplecom_supply_virtual_bills_16\.csv']},
    {
        'name': "Check TPRs in virtual bill",
        'path': '/downloads/'
        '0012_FINISHED_adminexamplecom_supply_virtual_bills_16.csv',
        'status_code': 200,
        'regexes': [
            r'Imp MPAN Core,Exp MPAN Core,Site Code,Site Name,Account,From,To'
            r',,mop-net-gbp,mop-problem,,dc-net-gbp,dc-problem,,'
            r'imp-supplier-net-gbp,imp-supplier-problem,'
            r'imp-supplier-00001-kwh,imp-supplier-00001-rate,'
            r'imp-supplier-00001-gbp,imp-supplier-00258-kwh,'
            r'imp-supplier-00258-rate,imp-supplier-00258-gbp,'
            r'imp-supplier-00259-kwh,imp-supplier-00259-rate,'
            r'imp-supplier-00259-gbp,imp-supplier-01218-kwh,'
            r'imp-supplier-01218-rate,imp-supplier-01218-gbp,'
            r'imp-supplier-01219-kwh,imp-supplier-01219-rate,'
            r'imp-supplier-01219-gbp\s*'
            r'22 9789 0534 938,,CI017,Roselands,taa2,2014-12-01 00:00,'
            r'2014-12-31 23:30,,10,,,0,,,14.68352837928714\d*,,'
            r'100.06724949562901,0.1,10.006724949562878,,,,,,,,,,,,,'
            r'duos-amber-gbp,1.0220578345662372,duos-amber-kwh,'
            r'40.34969737726923,duos-amber-rate,0.02533,'
            r'duos-availability-days,31,duos-availability-gbp,0.0,'
            r'duos-availability-kva,0,duos-availability-rate,0.0,'
            r'duos-excess-availability-days,31,duos-excess-availability-gbp,'
            r'0.0,duos-excess-availability-kva,0.13449899125756556,'
            r'duos-excess-availability-rate,0.0,duos-fixed-days,31,'
            r'duos-fixed-gbp,2.1420999999999992,duos-fixed-rate,'
            r'0.0691,duos-green-gbp,1.3559300605245412,duos-green-kwh,'
            r'53.53059852050996,duos-green-rate,0.02533,'
            r'duos-reactive-kvarh,0,duos-red-gbp,0.1567155346334899,'
            r'duos-red-kwh,6.186953597848016,duos-red-rate,0.02533']},

    {
        'name': "Virtual bill with 2 hh data items.",
        'path': '/reports/291?supply_id=5&start_year=2014&start_month=03&'
        'start_day=01&start_hour=00&start_minute=00&finish_year=2014&'
        'finish_month=06&finish_day=30&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'name': "Virtual bill with 2 hh data items.",
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'regexes': [
            r"0013_FINISHED_adminexamplecom_supply_virtual_bills_5\.csv"],
        'status_code': 200},
    {
        'name': "Virtual bill with 2 hh data items.",
        'path': '/downloads/'
        '0013_FINISHED_adminexamplecom_supply_virtual_bills_5.csv',
        'regexes': [
            r'22 0883 6932 301,22 7824 9120 097,CI005,Wheal Rodney,413,'
            r'2014-03-01 00:00,2014-06-30 23:30,,40,,,0,,,'
            r'1256.2935521\d*,,'
            r',,,5.89,350,122,0.026 \| 0.0269,1138.8649999999982,,'
            r',,,0.0,0.00147 \| 0.00161,0.0,0,0.00287 | 0.00344,0.0,48.9,'
            r'0.2441 \| 0.25405,12.423045,0.0,0.00382 \| 0.00399,0.0,122,'
            r'0.0878 \| 0.0905,10.795299999999976,88,52.5186,'
            r'0.0001897 \| 0.00021361,0.011218498146,52.9683167718\d*,,'
            r'-0.0224046166\d*,0.0,0.0,0.0,0,0.0,0.0,48.9,52.5186,'
            r'0.32906054015999997,,,,0,0.0,0.0,,,,53.23951\d*,,'
            r'0.0023446683\d*,2013-11-25 17:00,0,X,1.087,0.0,'
            r'2013-12-06 17:00,0,X,1.087,0.0,2014-01-30 17:00,0,X,1.087,0.0,'
            r'0.0,33.551731,0.0,2012-11-29 17:00 \| 2013-11-25 17:00,'
            r'0,X,1.087,0.0,2012-12-12 17:00 \| 2013-12-06 17:00,0,X,'
            r'1.074 \| 1.087,0.0,2013-01-16 17:00 \| 2014-01-30 17:00,'
            r'0,X,1.087,0.0,0.0,33.551731 \| 38.699518,1,0.0,12,0.0,,,,,,,,,'
            r',,,,,,,,,93.89,,,,,5.89,150,122,0.0,0.0,,,,,0,'
            r'-0.00667 \| -0.00649,0.0,0,-0.00667 \| -0.00649,0.0,0.0,'
            r'0.00147 \| 0.00151,0.0,122,0.0,0.0,88,0.0,0.0001897 \| '
            r'0.00021361,'
            r'0.0,0.0,,0.0,0,0.0,0.0,0,0.0,0.0,0,0.0,0.0,,,,0,0.0,0.0,,,,0.0,,'
            r'0.0,2013-11-25 17:00,0,before start of supply,'
            r'before start of supply,0,2013-12-06 17:00,0,'
            r'before start of supply,before start of supply,0,'
            r'2014-01-30 17:00,0,X,1.087,0.0,0.0,33.551731,0.0,'
            r'2013-01-16 17:00 \| 2013-11-25 17:00,0,X,1.087,0.0,'
            r'2013-12-06 17:00,0,X,1.074,0.0,2014-01-30 17:00,0,X,1.087,0.0,'
            r'0.0,33.551731 \| 38.699518,1,0.0,12,0.0,,duos-amber-rate,'
            r'-0.00667 \| -0.00649,duos-red-kwh,0'],
        'status_code': 200},

    {
        'name': "Delete all bills from a batch",
        'path': '/supplier_batches/17/edit',
        'method': 'post',
        'data': {
            'delete_bills': 'delete bills'},
        'status_code': 303,
        'regexes': [
            r'/supplier_batches/17']},

    {
        'name': "Show insert gas contract",
        'path': '/g_contracts/add',
        'status_code': 200,
        'regexes': [
            r'<form action="/g_contracts/add" method="post">']},

    {
        'name': "Insert gas contract",
        'path': '/g_contracts/add',
        'method': 'post',
        'data': {
            'name': "Total",
            'start_year': '2015',
            'start_month': '07',
            'start_day': '03',
            'start_hour': '00',
            'start_minute': '00',
            'properties': '{}',
            'charge_script': """
"""},
        'status_code': 303,
        'regexes': [
            r'/g_contracts/1']},

    {
        'name': "View gas contracts",
        'path': '/g_contracts',
        'status_code': 200,
        'regexes': [
            r'Total',
            r'\[<a href="/g_contracts/add">add</a>\]']},

    {
        'name': "View gas contract",
        'path': '/g_contracts/1',
        'status_code': 200,
        'regexes': [
            r'<td>Total</td>',
            r'<h3 id="properties">Properties</h3>\s*'
            r'<pre>\{\}</pre>']},

    {
        'name': "View gas contract rate script",
        'path': '/g_rate_scripts/1',
        'status_code': 200},

    {
        'name': "View edit gas contract",
        'path': '/g_contracts/1/edit',
        'status_code': 200,
        'regexes': [
            r'Total']},

    {
        'name': "Edit gas contract",
        'path': '/g_contracts/1/edit',
        'method': 'post',
        'data': {
            'name': "Total",
            'start_year': '2015',
            'start_month': '07',
            'start_day': '03',
            'start_hour': '00',
            'start_minute': '00',
            'properties': '{}',
            'charge_script': """
import chellow.g_ccl
from chellow.g_engine import g_rates


def virtual_bill_titles():
    return [
        'units_consumed', 'correction_factor', 'unit_code', 'unit_factor',
        'calorific_value', 'kwh', 'gas_rate', 'gas_gbp', 'ccl_rate',
        'standing_rate', 'standing_gbp', 'net_gbp', 'vat_gbp', 'gross_gbp',
        'problem']


def virtual_bill(ds):
    bill = ds.bill
    chellow.g_ccl.vb(ds)
    for hh in ds.hh_data:
        bill['units_consumed'] += hh['units_consumed']
        ds.rate_sets['correction_factor'].add(hh['correction_factor'])
        ds.rate_sets['unit_code'].add(hh['unit_code'])
        ds.rate_sets['unit_factor'].add(hh['unit_factor'])
        ds.rate_sets['calorific_value'].add(hh['calorific_value'])
        kwh = hh['kwh']
        bill['kwh'] += kwh
        gas_rate = float(
            g_rates(ds.sess, ds.caches, db_id, hh['start_date'])['gas_rate'])
        ds.rate_sets['gas_rate'].add(gas_rate)
        bill['gas_gbp'] += gas_rate * kwh
        if hh['utc_is_month_end']:
            standing_rate = float(
                g_rates(
                    ds.sess, ds.caches, db_id,
                    hh['start_date'])['standing_rate'])
            ds.rate_sets['standing_rate'].add(standing_rate)
            bill['standing_gbp'] += standing_rate
        if hh['utc_decimal_hour'] == 0:
            pass

    for k, rset in ds.rate_sets.items():
        bill[k] = rset

    bill['net_gbp'] = sum(v for k, v in bill.items() if k.endswith('gbp'))
    bill['vat_gbp'] = 0
    bill['gross_gbp'] = bill['net_gbp'] + bill['vat_gbp']
"""},
        'status_code': 303,
        'regexes': [
            r'/g_contracts/1']},
    {
        'name': "Edit gas contract: check correct",
        'path': '/g_contracts/1',
        'status_code': 200,
        'regexes': [
            r'<h3 id="properties">Properties</h3>\s*'
            r'<pre>\{\}</pre>']},

    {
        'name': "View add rate script to gas contract",
        'path': '/g_contracts/1/add_rate_script',
        'status_code': 200,
        'regexes': [
            r'<form\s*'
            r'action="/g_contracts/1/add_rate_script"\s*'
            r'method="post">']},

    {
        'name': "Add rate script to gas contract",
        'path': '/g_contracts/1/add_rate_script',
        'method': 'post',
        'data': {
            'start_year': '2015',
            'start_month': '09',
            'start_day': '01',
            'start_hour': '00',
            'start_minute': '00'},
        'status_code': 303,
        'regexes': [
            r'/g_rate_scripts/2']},

    {
        'name': "Edit view of gas rate script",
        'path': '/g_rate_scripts/2/edit',
        'status_code': 200,
        'regexes': [
            r'<form\s*'
            r'action="/g_rate_scripts/2/edit"\s*'
            r'method="post">']},

    {
        'name': "Edit the added rate script",
        'path': '/g_rate_scripts/2/edit',
        'method': 'post',
        'data': {
            'start_year': '2015',
            'start_month': '09',
            'start_day': '01',
            'start_hour': '00',
            'start_minute': '00',
            'script': '{"gas_rate": 0.019548, "standing_rate": 67.80}'},
        'status_code': 303,
        'regexes': [
            r'/g_rate_scripts/2']},

    {
        'name': "Edit gas rate script: error in Zish",
        'path': '/g_rate_scripts/2/edit',
        'method': 'post',
        'data': {
            'start_year': '2015',
            'start_month': '09',
            'start_day': '01',
            'start_hour': '00',
            'start_minute': '00',
            'script': '{"gas_rate": 0.019548, "standing_rate: 67.80}'},
        'status_code': 400,
        'regexes': [
            r'Update Rate Script']},

    {
        'name': "View add a batch to a gas contract",
        'path': '/g_contracts/1/add_batch',
        'status_code': 200,
        'regexes': [
            r'<form\s*'
            r'action="/g_contracts/1/add_batch" method="post">']},

    {
        'name': "Add a batch to a gas contract",
        'path': '/g_contracts/1/add_batch',
        'method': 'post',
        'data': {
            'reference': 'TB1',
            'description': 'Total Batch 1'},
        'status_code': 303,
        'regexes': [
            r'/g_batches/1']},


    {
        'name': "View edit site - with gas contracts",
        'path': '/sites/7/edit',
        'status_code': 200,
        'regexes': [
            r'<select name="g_contract_id">\s*'
            r'<option value="1">Total</option>\s*'
            r'</select>']},

    {
        'name': "Insert a gas supply",
        'path': '/sites/7/edit',
        'method': 'post',
        'data': {
            'name': 'Main Gas',
            'start_year': '2015',
            'start_month': '09',
            'start_day': '01',
            'start_hour': '00',
            'start_minute': '00',
            'msn': 'hwo8tt',
            'is_corrected': 'false',
            'g_unit_id': '5',
            'g_exit_zone_id': '6',
            'mprn': '7502786737',
            'g_contract_id': '1',
            'account': 'ghoIIl',
            'insert_gas': 'Insert Gas'},
        'status_code': 303,
        'regexes': [
            r'/g_supplies/1']},

    {
        'name': "View a gas supply",
        'path': '/g_supplies/1',
        'status_code': 200,
        'regexes': [
            r'Main Gas']},

    {
        'name': "Edit view of a gas supply",
        'path': '/g_supplies/1/edit',
        'status_code': 200,
        'regexes': [
            r'Main Gas',
            r'<form method="post" action="/g_supplies/1/edit">\s*'
            r'<fieldset>\s*'
            r'<legend>Insert a new era</legend>\s*',
            r'<select name="g_exit_zone_id">\s*'
            r'<option value="1">EA1</option>']},
    {
        'name': "Edit gas supply",
        'path': '/g_supplies/1/edit',
        'method': 'post',
        'data': {
            'mprn': '750278673',
            'name': 'Main Gas Supply',
            'g_exit_zone_id': '6',
            'update': 'Update'},
        'status_code': 303,
        'regexes': [
            r'/g_supplies/1']},

    {
        'name': "Failed edit of gas supply",
        'path': '/g_supplies/1/edit',
        'method': 'post',
        'data': {
            'mprn': '',
            'name': 'Main Gas Supply',
            'g_exit_zone_id': '6',
            'update': 'Update'},
        'status_code': 400,
        'regexes': [
            r'The MPRN can&#39;t be blank\.']},

    {
        'name': "Check supply has been updated properly",
        'path': '/g_supplies/1',
        'status_code': 200,
        'regexes': [
            r'Main Gas Supply']},

    {
        'name': "Insert duplicate gas supply",
        'path': '/sites/7/edit',
        'method': 'post',
        'data': {
            'name': 'Main Gas',
            'start_year': '2015',
            'start_month': '09',
            'start_day': '01',
            'start_hour': '00',
            'start_minute': '00',
            'msn': 'hwo8tt',
            'is_corrected': 'false',
            'g_unit_id': '5',
            'mprn': '750278673',
            'g_exit_zone_id': '6',
            'g_contract_id': '1',
            'account': 'ghoIIl',
            'insert_gas': 'Insert Gas'},
        'status_code': 400,
        'regexes': [
            r'There&#39;s already a gas supply with that MPRN\.']},

    {
        'name': "Edit view of gas era",
        'path': '/g_eras/1/edit',
        'status_code': 200,
        'regexes': [
            r'hwo8tt']},

    {
        'name': "Edit gas era",
        'path': '/g_eras/1/edit',
        'method': 'post',
        'data': {
            'start_year': '2015',
            'start_month': '09',
            'start_day': '01',
            'start_hour': '00',
            'start_minute': '00',
            'msn': 'hwo8th',
            'is_corrected': 'false',
            'g_unit_id': '5',
            'g_contract_id': 1,
            'account': 'ghoIIl'},
        'status_code': 303,
        'regexes': [
            r'/g_supplies/1']},

    {
        'name': "Check era has been updated properly",
        'path': '/g_supplies/1',
        'status_code': 200,
        'regexes': [
            r'hwo8th']},

    {
        'name': "Show import gas bills",
        'path': '/g_bill_imports?g_batch_id=1',
        'status_code': 200,
        'regexes': [
            r'Total']},

    {
        'name': "Test gas CSV bill import",
        'path': '/g_bill_imports',
        'method': 'post',
        'data': {
            'g_batch_id': "1", },
        'files': {'import_file': 'test/gas/gas_bills.csv'},
        'status_code': 303,
        'regexes': [
            r"/g_bill_imports/0"]},

    {
        'name': "View bill import",
        'path': '/g_bill_imports/0',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"successfully",
            r'39\.300811</td>\s*</tr>\s*</tbody>']},

    {
        'name': "Gas bill shown correctly in batch",
        'path': '/g_batches/1',
        'status_code': 200,
        'regexes': [
            r"<th>0 MSN</th>\s*"
            r"<th>0 Unit</th>\s*"
            r"<th>0 Is Corrected\?</th>\s*"
            r"<th>0 Correction Factor</th>\s*"
            r"<th>0 Calorific Value</th>\s*"
            r"<th>0 Prev Date</th>\s*"
            r"<th>0 Prev Value</th>\s*"
            r"<th>0 Prev Type</th>\s*"
            r"<th>0 Pres Date</th>\s*"
            r"<th>0 Pres Value</th>\s*"
            r"<th>0 Pres Type</th>\s*"
            r"</tr>",
            r"2015-09-01 00:00",
            r'<td>hwo8tt</td>\s*'
            r'<td>HCUF</td>\s*'
            r'<td>\s*'
            r'No\s*'
            r'</td>\s*'
            r'<td>None</td>']},

    {
        'name': "View gas bill",
        'path': '/g_bills/1',
        'status_code': 200,
        'regexes': [
            r'<tr>\s*'
            r'<td>ccl</td>']},

    {
        'name': "View edit gas bill",
        'path': '/g_bills/1/edit',
        'regexes': [
            r'<form action="/g_bills/1/edit">\s*'
            r'<fieldset>\s*'
            r'<legend>Delete This Bill</legend>'],
        'status_code': 200},

    {
        'name': "Edit gas bill",
        'path': '/g_bills/1/edit',
        'method': 'post',
        'data': {
            'bill_type_id': '2',
            'reference': '88999000127',
            'account': 'ghoIIl',
            'issue_year': '2015',
            'issue_month': '10',
            'issue_day': '04',
            'issue_hour': '23',
            'issue_minute': '00',
            'start_year': '2015',
            'start_month': '09',
            'start_day': '01',
            'start_hour': '00',
            'start_minute': '00',
            'finish_year': '2015',
            'finish_month': '09',
            'finish_day': '30',
            'finish_hour': '23',
            'finish_minute': '30',
            'kwh': '4500901',
            'net_gbp': '75.78',
            'vat_gbp': '45.00',
            'gross_gbp': '120.78',
            'raw_lines': 'Despard-Smith,College Rooms,None,Riley Hall,OX4 J99,'
                'ghoIIl,2015-10-05 00:00:00,None,8899900012,None,750278673,'
                'None,None,None,None,None,None,2015-09-01 00:00:00,'
                '2015-09-30 00:00:00,None,None,None,None,None,None,None,None,'
                'None,0,0,0,45,45,78.9,120.78\nPaying Customer Name,'
                'Account Name,Cust Ref,Address Lines All,Post Code,'
                'Account Code,Print Date,Cancel Date,Bill Number,Meter Ser No,'
                'MPR,Previous Billed Reading,Previous Read Date,'
                'Prev Read Type,Billed Reading,Read Date,Read Type,'
                'Charge Start Date,Charge End Date,Units Consumed (Accm),'
                'Correctn Factor,Calorific Value,Consumption Kwh,Price Pkwh,'
                'Units Consumed,Unit of Measure,Gas Charge,CCL Charge,'
                'VAT at 5%,VAT at 15.0%,Vat at 17.50%,VAT at 20%,Total VAT,'
                'Standing Charge,Total Charges',
            'breakdown': '{"vat_20pc": 45, "gas_gbp": 8936.13,'
                ' "vat_17_5pc": 0, "gas_rate": 0.019448, "vat_15pc": 0, '
                '"vat_5pc": 0, "standing_gbp": 78.9, "ccl_gbp": 275.32}'},
        'status_code': 303},
    {
        'name': "Delete gas bill",
        'path': '/g_bills/1/edit',
        'method': 'post',
        'data': {
            'delete': 'delete'},
        'status_code': 303},

    {
        'name': "Insert bills with negative register reads",
        'path': '/supplier_bill_imports',
        'method': 'post',
        'data': {
            'supplier_batch_id': '7'},
        'files': {'import_file': 'test/bills-nhh-negative.csv'},
        'status_code': 303,
        'regexes': [
            r"/supplier_bill_imports/15"]},
    {
        'name': "Insert bills with negative register reads",
        'path': '/supplier_bill_imports/15',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"Negative register reads aren&#39;t allowed"]},

    {
        'name': "Delete an electricity register read",
        'path': '/reads/15/edit',
        'method': 'post',
        'data': {
            'delete': 'Delete'},
        'regexes': [
            r'/supplier_bills/20']},

    {
        'name': "Delete bills of gas batch",
        'path': '/g_batches/1/edit',
        'method': 'post',
        'data': {
            'delete_bills': 'Delete Bills'},
        'status_code': 303},

    {
        'name': "Delete gas batch",
        'path': '/g_batches/1/edit',
        'method': 'post',
        'data': {
            'delete': 'delete'},
        'status_code': 303,
        'regexes': [
            r"/g_batches\?g_contract_id=1"]},

    {
        'name': "Add a new batch to a gas contract",
        'path': '/g_contracts/1/add_batch',
        'method': 'post',
        'data': {
            'reference': 'TB2',
            'description': 'Total Batch 2'},
        'status_code': 303,
        'regexes': [
            r'/g_batches/2']},

    {
        'name': "Import CSV gas bills that will fail",
        'path': '/g_bill_imports',
        'method': 'post',
        'data': {
            'g_batch_id': "2"},
        'files': {'import_file': 'test/gas/gas_bills_fail.csv'},
        'status_code': 303,
        'regexes': [
            r"/g_bill_imports/1"]},

    {
        'name': "View failed gas bill import",
        'path': '/g_bill_imports/1',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r'Net GBP']},

    {
        'name': "Check that the imported bill has been rolled back.",
        'path': '/g_supplies/1',
        'status_code': 200,
        'regexes': [
            r'<table class="DataTable widthAuto noMarginBottom">\s*'
            r'<caption>Gas Bills</caption>\s*'
            r'<thead>\s*'
            r'<tr>\s*'
            r'<th>View</th>\s*'
            r'<th>From</th>\s*'
            r'<th>To</th>\s*'
            r'<th>Batch</th>\s*'
            r'<th>Reference</th>\s*'
            r'<th>kWh</th>\s*'
            r'<th>Net</th>\s*'
            r'<th>VAT</th>\s*'
            r'<th>Type</th>\s*'
            r'<th colspan="2">Previous</th>\s*'
            r'<th colspan="2">Present</th>\s*'
            r'</tr>\s*'
            r'</thead>\s*'
            r'<tbody>\s*'
            r'</tbody>\s*'
            r'</table>']},

    {
        'name': "Gas: Import CSV bills",
        'path': '/g_bill_imports',
        'method': 'post',
        'data': {
            'g_batch_id': "2"},
        'files': {'import_file': 'test/gas/gas_bills.csv'},
        'status_code': 303,
        'regexes': [
            r"/g_bill_imports/2"]},

    {
        'name': "Gas: View bill import",
        'path': '/g_bill_imports/2',
        'tries': {},
        'status_code': 200,
        'regexes': [r'successfully']},
    {
        'name': "Edit the added rate script",
        'path': '/g_rate_scripts/1/edit',
        'method': 'post',
        'data': {
            'start_year': '2015',
            'start_month': '07',
            'start_day': '03',
            'start_hour': '00',
            'start_minute': '00',
            'has_finished': 'true',
            'finish_year': '2015',
            'finish_month': '08',
            'finish_day': '31',
            'finish_hour': '23',
            'finish_minute': '30',
            'script': '{"gas_rate": 0.019548, "standing_rate": 67.80}'},
        'status_code': 303},
    {
        'name': "Gas bill check",
        'path': '/reports/429?g_bill_id=3',
        'status_code': 303},
    {
        'name': "Gas bill check",
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"0014_FINISHED_adminexamplecom_g_bill_check\.csv"],
        'status_code': 200},
    {
        'name': "Gas bill check",
        'path': '/downloads/0014_FINISHED_adminexamplecom_g_bill_check.csv',
        'status_code': 200,
        'regexes': [
            r'batch,bill_reference,bill_type,bill_start_date,'
            r'bill_finish_date,mprn,supply_name,site_code,site_name,'
            r'covered_start,covered_finish,covered_bill_ids,'
            r'covered_units_consumed,virtual_units_consumed,'
            r'covered_correction_factor,virtual_correction_factor,'
            r'covered_unit_code,virtual_unit_code,covered_unit_factor,'
            r'virtual_unit_factor,covered_calorific_value,'
            r'virtual_calorific_value,covered_kwh,virtual_kwh,'
            r'covered_gas_rate,virtual_gas_rate,covered_gas_gbp,'
            r'virtual_gas_gbp,difference_gas_gbp,covered_ccl_rate,'
            r'virtual_ccl_rate,covered_standing_rate,'
            r'virtual_standing_rate,covered_standing_gbp,virtual_standing_gbp,'
            r'difference_standing_gbp,covered_net_gbp,virtual_net_gbp,'
            r'difference_net_gbp,covered_vat_gbp,virtual_vat_gbp,'
            r'difference_vat_gbp,covered_gross_gbp,virtual_gross_gbp,'
            r'difference_gross_gbp\s*',
            r'TB2,8899900012,N,2015-09-01 00:00,2015-09-30 00:00,750278673,'
            r'Main Gas Supply,CH017,Parbola,2015-09-01 00:00,2015-09-30 00:00,'
            r'3,,7829.999999999759,,1.02264,HCUF,M3,2.8317,1.0,39.300811,,'
            r'4500901,87934.521286\d*,0.019448,0.019548,8936.13,'
            r'1718.9440220988\d*,7217.185977901\d*,,0.00525288,,,,,,6972.33,'
            r'1718.9440220988\d*,5253.385977901\d*,1003.89,0,1003.89,7976.22,'
            r'1718.9440220988\d*,6257.275977901\d*,,']},

    {
        'name': "Delete gas supply. Insert the gas supply",
        'path': '/sites/7/edit',
        'method': 'post',
        'data': {
            'name': 'Another Gas',
            'start_year': '2015',
            'start_month': '09',
            'start_day': '01',
            'start_hour': '00',
            'start_minute': '00',
            'mprn': '98472777',
            'g_exit_zone_id': '6',
            'msn': '7ghwsklh',
            'is_corrected': 'false',
            'g_unit_id': '5',
            'g_contract_id': '1',
            'account': 'ghuel',
            'insert_gas': 'Insert Gas'},
        'status_code': 303,
        'regexes': [
            r'/g_supplies/3']},

    {
        'name': "Delete gas supply. Check the search contains it.",
        'path': '/g_supplies?search_pattern=',
        'regexes': [
            r"Another Gas"],
        'status_code': 200},

    {
        'name': "Global search. Find a gas supply by MPRN",
        'path': '/supplies?search_pattern=750278673',
        'status_code': 307},

    {
        'name': "Delete gas supply.",
        'path': '/g_supplies/3/edit',
        'method': 'post',
        'data': {
            'delete': 'Delete'},
        'status_code': 303},


    {
        'name': "Gas: Insert era",
        'path': '/g_supplies/1/edit',
        'method': 'post',
        'data': {
            'start_year': '2016',
            'start_month': '01',
            'start_day': '10',
            'start_hour': '00',
            'start_minute': '00',
            'insert_g_era': 'Insert'},
        'status_code': 303,
        'regexes': [
            r"/g_supplies/1"]},

    {
        'name': "General import of gas supply",
        'path': '/general_imports',
        'method': 'post',
        'files': {'import_file': 'test/gas/g_supplies.csv'},
        'status_code': 303,
        'regexes': [
            r"/general_imports/30"]},
    {
        'name': "General import of gas supply",
        'path': '/general_imports/30',
        'tries': {'max': 10, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"The file has been imported successfully\."]},

    {
        'name': "Add a batch to a gas contract",
        'path': '/g_contracts/1/add_batch',
        'method': 'post',
        'data': {
            'reference': 'EB1',
            'description': 'Engie Batch 1'},
        'status_code': 303,
        'regexes': [
            r'/g_batches/3']},

    {
        'name': "Does site page show the gas supply?",
        'path': '/sites/7',
        'status_code': 200,
        'regexes': [
            r'750278673']},

    {
        'name': "Attach a gas era to a site",
        'path': '/g_eras/3/edit',
        'method': 'post',
        'data': {
            'site_code': 'CH023',
            'attach': 'Attach'},
        'status_code': 303},

    {
        'name': "Detach a gas era from a site",
        'path': '/g_eras/3/edit',
        'method': 'post',
        'data': {
            'site_id': '5',
            'detach': 'Detach'},
        'status_code': 303},

    {
        'name': "View gas batch edit page",
        'path': '/g_batches/3/edit',
        'status_code': 200,
        'regexes': [
            r'<form action="/g_batches/3/edit">\s*'
            r'<fieldset>\s*'
            r'<input type="submit" name="confirm_delete" value="Delete">']},


    {
        'name': "Add mop rate script",
        'path': '/mop_contracts/11/add_rate_script',
        'method': 'post',
        'data': {
            'start_year': "2017",
            'start_month': "03",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00"},
        'status_code': 303,
        'regexes': [
            r"/mop_rate_scripts/52"]},

    {
        'name': "Delete mop rate script",
        'path': '/mop_rate_scripts/52/edit',
        'method': 'post',
        'data': {
            'delete': "Delete"},
        'status_code': 303,
        'regexes': [
            r"/mop_contracts/11"]},
    {
        'name': "Cause an error in auto importer.",
        'path': '/dc_contracts/8/edit',
        'method': 'post',
        'data': {
            'party_id': "116",  # DASL
            'name': "HH contract",
            'charge_script': """
def virtual_bill_titles():
    return ['net-gbp', 'problem']

def virtual_bill(supply_source):
    supply_source.dc_bill['net-gbp'] = 0
""",
            'properties': """
{
    "enabled": true,
    "protocol": "ftp",
    "file_type": ".df2",
    "hostname": "localhost",
    "port": 2121,
    "username": "chellow",
    "password": "HixaNfUBOf*u",
    "directories": ["error"]}
"""},
        'status_code': 303},

    {
        'name': "Cause an error in ftp auto importer. Import now",
        'path': '/dc_contracts/8/auto_importer',
        'method': 'post',
        'regexes': [
            r'/dc_contracts/8/auto_importer'],
        'status_code': 303},

    {
        'name': "Cause an error in ftp auto importer, check for global error",
        'path': '/',
        'tries': {},
        'regexes': [
            r'class="global"']},

    {
        'name': "Cause an error in sftp auto importer.",
        'path': '/dc_contracts/8/edit',
        'method': 'post',
        'data': {
            'party_id': "116",  # DASL
            'name': "HH contract",
            'charge_script': """
def virtual_bill_titles():
    return ['net-gbp', 'problem']

def virtual_bill(supply_source):
    supply_source.dc_bill['net-gbp'] = 0
""",
            'properties': """
{
    "enabled": true,
    "protocol": "sftp",
    "file_type": ".df2",
    "hostname": "localhost",
    "port": 2120,
    "username": "chellow",
    "password": "HixaNfUBOf*u",
    "directories": ["error"]}
"""},
        'status_code': 303},

    {
        'name': "Cause an error in sftp auto importer. Import now",
        'path': '/dc_contracts/8/auto_importer',
        'method': 'post',
        'regexes': [
            r'/dc_contracts/8/auto_importer'],
        'status_code': 303},

    {
        'name': "Cause an error in sftp auto importer, check for global error",
        'path': '/',
        'tries': {},
        'regexes': [
            r'class="global"']},

    {

        'name': "Test the supplier batch checking",
        'path': '/reports/111?bill_id=7',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"0015_FINISHED_adminexamplecom_bill_check\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/0015_FINISHED_adminexamplecom_bill_check.csv',
        'regexes': [
            r'06-004,00080,N,0,4463.08,781.03,2007-02-02 00:00,'
            r'2007-02-28 23:30,,22 0470 7514 535,CH017,Parbola,'
            r'2007-02-02 00:00,2007-02-28 23:30,7,0,4463.08,0,4463.08,,,,,,'
            r'0.00441,,,0.0,,,0.0,,,,,,,,,0.0,'
            r',0,,,,,,,0.0,,,,,0.0,,,,,0.0,,,,,0.0,,,0.0,,,0.0,,,,,,,0.0'
            r',,,,,,,0.0,,,,,,,0.0,,,,,'
            r',,0.0,,,,,,,0.0,,,,,,,0.0,,,,,,,0.0,,,,,,,,,,,,,,,,,,,,,,,,,,,,'
            r',,,,,,,,,0.0,,,,,,,,,,,,,,,,,,,,,,'],
        'status_code': 200},

    {
        'name': "Look at a DNO party",
        'path': '/parties/81',
        'status_code': 200},

    {
        'name': "Insert a 99 supply",
        'path': '/sites/5/edit',
        'method': 'post',
        'data': {
            'source_id': '4',
            'generator_type_id': '1',
            'name': 'CHP 2',
            'start_year': "2017",
            'start_month': "04",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00",
            'msn': "8hkk522h",
            'gsp_group_id': '10',
            'pc_id': '0',
            'mtc_code': '845',
            'cop_id': '5',
            'ssc_code': '',
            'properties': '{}',
            'mop_contract_id': '11',
            'mop_account': "m 99 4881 3898 138",
            'dc_contract_id': '8',
            'dc_account': "dc-14 7206 6139 971",
            'imp_llfc_code': "510",
            'imp_mpan_core': "99 4881 3898 138",
            'imp_sc': "23",
            'imp_supplier_contract_id': '10',
            'imp_supplier_account': "sup 99 4881 3898 138",
            'insert_electricity': "insert"},
        'regexes': [
            r"/supplies/18"],
        'status_code': 303},
    {
        'name': "Test supplies duration with 99 MPAN",
        'path': '/reports/149?start_year=2017&start_month=04&start_day=01&'
        'start_hour=0&start_minute=0&finish_year=2017&finish_month=04&'
        'finish_day=30&finish_hour=23&finish_minute=30&supply_id=18',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"0016_FINISHED_adminexamplecom_supplies_duration\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0016_FINISHED_adminexamplecom_supplies_duration.csv',
        'regexes': [
            r'18,'],
        'status_code': 200},

    {
        'name': "DNO rate parser",
        'path': '/reports/dno_rate_parser',
        'method': 'post',
        'files': {'dno_file': 'test/dno_20_rates_2017.xlsx'},
        'data': {
            'gsp_group_id': '7',
            'llfc_tab': '1',
            'laf_tab': '7'},
        'status_code': 303,
        'regexes': [
            r"/downloads"]},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"0017_FINISHED_adminexamplecom_dno_rates.zish"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0017_FINISHED_adminexamplecom_dno_rates.zish',
        'regexes': [
            r'"super_red": \[\s*'
            r'\{\s*'
            r'"finish-day": "last",\s*'
            r'"finish-month": 2,\s*'
            r'"finish_hour": 19.5,\s*'
            r'"start-day": 1,\s*'
            r'"start-month": 11,\s*'
            r'"start_hour": 16.5,\s*'
            r'"weekend": false\s*'
            r'\}\s*'
            r'\]',

            r'"005": \{\s*'
            r'"amber-gbp-per-kwh": -0.00480,\s*'
            r'"description": "HV Generation Intermittent",\s*'
            r'"excess-gbp-per-kva-per-day": 0.00000,\s*'
            r'"gbp-per-kva-per-day": 0.00000,\s*'
            r'"gbp-per-kvarh": 0.00151,\s*'
            r'"gbp-per-mpan-per-day": 1.25890,\s*'
            r'"green-gbp-per-kwh": -0.00480,\s*'
            r'"red-gbp-per-kwh": -0.00480\s*'
            r'\}',

            r'"605,606": \{',
            r'"455": \{\s*'
            r'"amber-gbp-per-kwh": 0.00335,\s*'
            r'"description": "LV Sub HH Metered",\s*'
            r'"excess-gbp-per-kva-per-day": 0.04260,\s*'
            r'"gbp-per-kva-per-day": 0.04260,\s*'
            r'"gbp-per-kvarh": 0.00250,\s*',
            r'"gbp-per-mpan-per-day": 0.04170,\s*'
            r'"green-gbp-per-kwh": 0.00079,\s*'
            r'"red-gbp-per-kwh": 0.08838\s*'
            r'\}',

            r'"700": \{'],


        'status_code': 200},
    {
        'name': "DNO rate parser",
        'path': '/reports/dno_rate_parser',
        'method': 'post',
        'files': {'dno_file': 'test/dno_24_L_rates_2017.xlsx'},
        'data': {
            'gsp_group_id': '2',
            'llfc_tab': '1',
            'laf_tab': '7'},
        'status_code': 303,
        'regexes': [
            r"/downloads"]},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"0018_FINISHED_adminexamplecom_dno_rates.zish"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0018_FINISHED_adminexamplecom_dno_rates.zish',
        'regexes': [
            r'"601,603": \{',

            r'"night": 1.07000,\s*',
            r'"other": 1.07300,\s*'],
        'status_code': 200},

    {
        'name': "CRC report for unmetered supply.",
        'path': '/reports/207?supply_id=9&year=2016',
        'status_code': 303,
        'regexes': [
            r"/downloads"]},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'status_code': 200,
        'regexes': [
            r'0019_FINISHED_adminexamplecom_crc_2016_2017_supply_9\.csv']},
    {
        'path': '/downloads/'
        '0019_FINISHED_adminexamplecom_crc_2016_2017_supply_9.csv',
        'status_code': 200,
        'regexes': [
            r'Chellow Supply Id,Report Start,Report Finish,MPAN Core,Site Id,'
            r'Site Name,From,To,'
            r'NHH Breakdown,Actual HH Normal Days,Actual AMR Normal Days,'
            r'Actual NHH Normal Days,Actual Unmetered Normal Days,'
            r'Max HH Normal Days,Max AMR Normal Days,Max NHH Normal Days,'
            r'Max Unmetered Normal Days,Total Actual Normal Days,'
            r'Total Max Normal Days,Data Type,HH kWh,AMR kWh,NHH kWh,'
            r'Unmetered kwh,HH Filled kWh,AMR Filled kWh,Total kWh,Note',

            r'9,2016-04-01 00:00,2017-03-31 23:30,22 0195 4836 192,CI004,'
            r'Lower Treave,2016-04-01 00:00,'
            r'2017-03-31 23:30,,0,0,0,365.0,0,0,0,365.0,365.0,365.0,Actual,0,'
            r'0,0,304.0,0,0,304.0,']},

    {
        'name': "CRC report where era ends in the period",
        'path': '/reports/207?supply_id=5&year=2012',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'regexes': [
            r"0020_FINISHED_adminexamplecom_crc_2012_2013_supply_5\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0020_FINISHED_adminexamplecom_crc_2012_2013_supply_5.csv',
        'status_code': 200,
        'regexes': [
            r'^5,2012-04-01 00:00,2013-03-31 23:30,22 0883 6932 301,CI005,'
            r'Wheal Rodney,2012-04-01 00:00,2013-03-31 23:30,,0.0,0,0,0,365.0,'
            r'0,0,0,0.0,365.0,Estimated,0,0,0,0,0,0,0,']},

    {
        'name': "Import data by month for era without channels",
        'path': '/supplies/16/months?is_import=true&year=2017&years=1',
        'regexes': [
            r'Import\s*'
            r'data by month'],
        'status_code': 200},

    {
        'name': "Create a teleswitch supplier contract",
        'path': '/supplier_contracts/add',
        'method': 'post',
        'data': {
            'participant_id': "28",  # BIZZ
            'name': "teleswitch",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'charge_script': "",
            'properties': '{}'},
        'regexes': [
            r"/supplier_contracts/21"]},
    {
        'name': "Update the associated rate script.",
        'path': '/supplier_rate_scripts/53/edit',
        'method': 'post',
        'data': {
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'has_finished': "false",
            'script': """{
  "tprs": {}}
"""},
        'status_code': 303},
    {
        'path': '/reports/291?supply_id=10&start_year=2016&start_month=03&'
        'start_day=01&start_hour=00&start_minute=0&finish_year=2016&'
        'finish_month=03&finish_day=31&finish_hour=23&finish_minute=30',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20},
        'regexes': [
            r"0021_FINISHED_adminexamplecom_supply_virtual_bills_10\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0021_FINISHED_adminexamplecom_supply_virtual_bills_10.csv',
        'regexes': [
            r"Can't find the TPR"]},

    {
        'name': "Bill check on bill without era.",
        'path': '/reports/111?bill_id=17',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"0022_FINISHED_adminexamplecom_bill_check\.csv"],
        'status_code': 200},
    {
        'path': '/downloads/'
        '0022_FINISHED_adminexamplecom_bill_check.csv',
        'regexes': [
            r'99/992,08,N,0,6.40,1.05,2000-10-01 00:00,2000-10-31 23:30,,,,,'
            r'2000-10-01 00:00,2000-10-31 23:30,17,0,6.4,0,6.4,,'],
        'status_code': 200},

    {
        'name': "Two month scenario with LLFC map",
        'path': '/supplier_contracts/18/edit',
        'method': 'post',
        'data': {
            'party_id': "106",  # COOP
            'name': "scenario_bsuos",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'charge_script': "",
            'properties': """
{
  "rates": {
    "bsuos" : {
      "start_date": 2011-01-01T00:00:00Z,
      "multiplier": 1,
      "constant": 0.1}},

  "scenario_start": 2011-01-01T00:00:00Z,
  "scenario_duration": 2,
  "resolution": "month",

  "era_maps": {
    2011-01-01T00:00:00Z: {
      "llfcs": {
        "22": {
          "570": "540"}}}},


  "kw_changes": ""}
"""},
        'regexes': [
            r"/supplier_contracts/18"],
        'status_code': 303},

    {
        'name': "Run scenario for a site",
        'path': '/reports/247?site_id=3&scenario_id=18&compression=False',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"0023_FINISHED_adminexamplecom_scenario_bsuos_20110101_0000_"
            r"for_2_months_site_CI005\.ods"]},
    {
        'path': '/downloads/'
        '0023_FINISHED_adminexamplecom_scenario_bsuos_20110101_0000_for_2_'
        'months_site_CI005.ods',
        'status_code': 200,
        'regexes': [
            r'<table:table table:name="Era Level">\s*'
            r'<table:table-column/>\s*'
            r'<table:table-row>\s*'
            r'<table:table-cell office:string-value="creation-date" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-mpan-core" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-contract" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="exp-mpan-core" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="exp-supplier-contract" '
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
            r'<table:table-cell '
            r'office:string-value="dc-net-gbp" office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="dc-problem" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-net-gbp" '
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
            r'<table:table-cell '
            r'office:string-value="imp-supplier-night-gbp" '
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
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-green-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-green-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-green-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-amber-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-amber-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-amber-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-red-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-red-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-red-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-reactive-kvarh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-fixed-days" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-fixed-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-duos-fixed-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-aahedc-gsp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-aahedc-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-aahedc-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-rcrc-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-rcrc-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-rcrc-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-vat-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-gross-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell '
            r'office:string-value="imp-supplier-sum-msp-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00001-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00001-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00001-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00258-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00258-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00258-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00259-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00259-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-00259-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-01218-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-01218-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-01218-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-01219-kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-01219-rate" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="imp-supplier-01219-gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell '
            r'office:string-value="exp-supplier-net-gbp" '
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
            r'office:string-value="exp-supplier-duos-excess-availability-gbp" '
            r'office:value-type="string"/>\s*'
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
            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell '
            r'office:string-value="Half-hourlies 2007" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:string-value="hh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="displaced" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="4"/>\s*'
            r'<table:table-cell office:string-value="CI005" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Wheal '
            r'Rodney" office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:date-value="2011-01-31T23:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" '
            r'table:number-columns-repeated="15"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell table:number-columns-repeated="7"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0047" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="18"/>\s*'
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
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell/>\s*'
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
            r'<table:table-cell office:date-value="2010-01-07T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="E" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.078" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:date-value="2010-01-25T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="E" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.078" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:date-value="2009-12-15T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="E" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.078" '
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
            r'<table:table-cell office:value="0.0013" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.00147" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.16146" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="28"/>\s*'
            r'</table:table-row>\s*'
            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:string-value="22 '
            r'0883 6932 301" office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Half-hourlies '
            r'2007" office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:string-value="hh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="gen-net" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="chp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Hello" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="00" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="CI005" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Wheal '
            r'Rodney" office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:date-value="2011-01-31T23:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="9"/>\s*'
            r'<table:table-cell office:value="356.1556\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="6"/>\s*'
            r'<table:table-cell office:value="356.1556\d*" '
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
            r'<table:table-cell office:value="346.1556\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0047" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="5.89" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="350" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="31" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0231" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="250.635\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="8"/>\s*'
            r'<table:table-cell office:value="0.00265" '
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
            r'<table:table-cell office:date-value="2010-01-07T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.07" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:date-value="2010-01-25T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.07" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:date-value="2009-12-15T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.078" '
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
            r'<table:table-cell office:value="0.00091" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.00084" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.14307" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="31" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0526" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="1.630\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="24"/>\s*'
            r'</table:table-row>\s*'
            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:string-value="Half-hourlies '
            r'2007" office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:string-value="hh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="displaced" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="4"/>\s*'
            r'<table:table-cell office:string-value="CI005" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Wheal '
            r'Rodney" office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:date-value="2011-02-28T23:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" '
            r'table:number-columns-repeated="15"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell table:number-columns-repeated="7"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0047" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="18"/>\s*'
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
            r'<table:table-cell/>\s*'
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
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="18"/>\s*'
            r'<table:table-cell office:date-value="2010-01-07T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="E" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.078" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:date-value="2010-01-25T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="E" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.078" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:date-value="2009-12-15T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="E" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.078" '
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
            r'<table:table-cell office:value="0.0013" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.00147" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.16146" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="28"/>\s*'
            r'</table:table-row>\s*'
            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:string-value="22 '
            r'0883 6932 301" office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Half-hourlies '
            r'2007" office:value-type="string"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:string-value="hh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="gen-net" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="chp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Hello" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="00" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="CI005" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Wheal '
            r'Rodney" office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:date-value="2011-02-28T23:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="9"/>\s*'
            r'<table:table-cell office:value="331.7428\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float" table:number-columns-repeated="6"/>\s*'
            r'<table:table-cell office:value="331.7428\d*" '
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
            r'<table:table-cell office:value="321.7428\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="0.0047" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="5.89" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="350" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="28" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0231" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="226.38\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="8"/>\s*'
            r'<table:table-cell office:value="0.00265" '
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
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="18"/>\s*'
            r'<table:table-cell office:date-value="2010-01-07T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.07" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:date-value="2010-01-25T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.07" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:date-value="2009-12-15T17:00:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="X" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.078" '
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
            r'<table:table-cell office:value="0.00091" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.00084" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.14307" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="28" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.0526" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="1.472\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell table:number-columns-repeated="24"/>\s*'
            r'</table:table-row>\s*']},

    {
        'name': "Download CSV of  LLFCs",
        'path': '/reports/csv_llfcs',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"0024_FINISHED_adminexamplecom_llfcs.csv"]},
    {
        'path': '/downloads/0024_FINISHED_adminexamplecom_llfcs.csv',
        'status_code': 200,
        'regexes': [
            r'0,28,009,LV HH Metered,LV,False,True,2009-04-16 00:00,'
            r'2014-08-20 00:00']},

    {
        'name': "CSV of supplier batch",
        'path': '/supplier_batches/4/csv',
        'status_code': 200},

    {
        'name': "Update an DC bill",
        'path': '/dc_bills/15/edit',
        'method': 'post',
        'data': {
            'reference': "00031",
            'account': "22 0883 6932 301",
            'issue_year': '2007',
            'issue_month': '09',
            'issue_day': '01',
            'issue_hour': '00',
            'issue_minute': '00',
            'start_year': '2007',
            'start_month': '10',
            'start_day': '01',
            'start_hour': '00',
            'start_minute': '00',
            'finish_year': '2007',
            'finish_month': '10',
            'finish_day': '31',
            'finish_hour': '23',
            'finish_minute': '30',
            'kwh': '0',
            'net': '0.00',
            'vat': '0.00',
            'gross': '0.00',
            'bill_type_id': '2',
            'breakdown': '{}'},
        'status_code': 303},

    {
        'name': "Test DC HTTPS auto importer: Add ACTIVE channel",
        'path': '/eras/20/add_channel',
        'method': 'post',
        'data': {
            'imp_related': "true",
            'channel_type': "ACTIVE"},
        'status_code': 303},
    {
        'name': "Test DC HTTPS auto importer: set up contract",
        'path': '/dc_contracts/9/edit',
        'method': 'post',
        'data': {
            'party_id': "1121",  # UKDC
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
            'properties': """
{
  "enabled": true,
  "protocol": "https",
  "download_days": 8,
  "url_template":
  "http://localhost:8080/hh_api?from={{chunk_start.strftime('%d/%m/%Y')}}&to={{chunk_finish.strftime('%d/%m/%Y')}}",
  "url_values": {
    "22 7907 4116 080": {
      "api_key": "768234ht"}}}
"""},
        'status_code': 303},

    {
        'name': "Test DC HTTPS auto importer: import now",
        'path': '/dc_contracts/9/auto_importer',
        'method': 'post',
        'regexes': [
            r'/dc_contracts/9/auto_importer'],
        'status_code': 303},

    {
        'name': "Test DC HTTPS auto importer: check that it completed",
        'path': '/dc_contracts/9/auto_importer',
        'tries': {},
        'regexes': [
            r"Finished loading"]},

    {
        'name': "Add NHH DC contract",
        'path': '/dc_contracts/add',
        'method': 'post',
        'data': {
            'party_id': "781",  # NHH LBSL
            'name': "NHH DC contract",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'has_finished': "false"},
        'status_code': 303,
        'regexes': [
            r"/dc_contracts/22"]},
    {
        'name': "View NHH DC contract",
        'path': '/dc_contracts/22',
        'status_code': 200},

    {
        'name': "NHH DC contract error on updating",
        'path': '/dc_contracts/22/edit',
        'method': 'post',
        'status_code': 400,
        'regexes': [
            r'Lowri Beck']},

    {
        'name': "Malformed scenario properties",
        'path': '/supplier_contracts/17/edit',
        'method': 'post',
        'data': {
            'party_id': "106",  # COOP
            'name': "scenario_bau",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'charge_script': "",
            'properties': """
{
  "local_rates": {},
  "scenario_start": 2015-06-01T00:00:00Z,
  "scenario_duration": 1}""", },
        'regexes': [
            r"/supplier_contracts/17"],
        'status_code': 303},

    {
        'name': "Malformed scenario properties",
        'path': '/reports/247?site_id=1&scenario_id=17&compression=False',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"0025_FINISHED_adminexamplecom_scenario_bau_20150601_0000_for_1_"
            r"months_site_CI004\.ods"]},
    {
        'path': '/downloads/'
        '0025_FINISHED_adminexamplecom_scenario_bau_20150601_0000_for_1_'
        'months_site_CI004.ods',
        'status_code': 200,

        'regexes': [
            r"The 'local_rates' must be a list."]},

    {
        'name': "Gas CV auto-importer",
        'path': '/non_core_contracts/4/edit',
        'method': 'post',
        'data': {
            'name': 'g_cv',
            'properties': """{
  "enabled": true,
  "url": "http://127.0.0.1:8080/nationalgrid/cv.csv"}
"""},
        'status_code': 303},

    {
        'name': "Do an 'import now'",
        'path': '/non_core_contracts/4/auto_importer',
        'method': 'post',
        'regexes': [
            r'/non_core_contracts/4/auto_importer'],
        'status_code': 303},

    {
        'name': "Gas CV",
        'path': '/non_core_contracts/4/auto_importer',
        'tries': {'max': 40, 'period': 1},
        'regexes': [
            r"Added new rate script\."],
        'status_code': 200},

    {
        'name': "Gas supplies snapshot",
        'path': '/reports/g_supplies_snapshot?g_supply_id=1&date_year=2018&'
        'date_month=03&date_day=01&date_hour=00&date_minute=00',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"0026_FINISHED_adminexamplecom_g_supplies_snapshot\.csv"]},
    {
        'path': '/downloads/'
        '0026_FINISHED_adminexamplecom_g_supplies_snapshot.csv',
        'status_code': 200,
        'regexes': [
            r'2018-03-01 00:00,CH017,Parbola,,,750278673,EM2,hwo8th,no,M3,'
            r'Total,ghoIIl,2015-09-01 00:00,']},

    {
        'name': "Gas monthly duration",
        'path': '/reports/g_monthly_duration?g_supply_id=1&months=1&'
        'finish_year=2018&finish_month=03&finish_day=01&finish_hour=00&'
        'finish_minute=00&compression=False',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r'0027_FINISHED_adminexamplecom_g_monthly_duration_20180301_'
            r'0000_for_1_months_g_supply_1\.ods']},
    {
        'path': '/downloads/'
        '0027_FINISHED_adminexamplecom_g_monthly_duration_20180301_0000_for_1_'
        'months_g_supply_1.ods',
        'status_code': 200,
        'regexes': [
            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:string-value="750278673" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Main Gas Supply" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="EM2" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="hwo8th" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:boolean-value="false" '
            r'office:value-type="boolean"/>\s*'
            r'<table:table-cell office:string-value="M3" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Total" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="CH017" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Parbola" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:date-value="2018-03-31T23:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="90263.78443636319" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="1832.2764581620822" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="8085.385149201755" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="1.02264" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="M3" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="1.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="39.3" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="90263.78443636319" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.019548" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="1764.4764581620823" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0.00198" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="67.8" '
            r'office:value-type="float" table:number-columns-repeated="2"/>\s*'
            r'<table:table-cell office:value="1832.2764581620822" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="1832.2764581620822" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'</table:table-row>']},

    {
        'name': "Gas virtual bill by HH",
        'path': '/reports/g_virtual_bills_hh?g_supply_id=1&start_year=2018&'
        'start_month=02&start_day=01&start_hour=00&start_minute=00&'
        'finish_year=2018&finish_month=02&finish_day=01&finish_hour=00&'
        'finish_minute=30&compression=False',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r'0028_FINISHED_adminexamplecom_'
            r'g_supply_virtual_bills_hh_1\.csv']},
    {
        'path': '/downloads/'
        '0028_FINISHED_adminexamplecom_g_supply_virtual_bills_hh_1.csv',
        'status_code': 200,
        'regexes': [
            r'MPRN,Site Code,Site Name,Account,HH Start,,,units_consumed,'
            r'correction_factor,unit_code,unit_factor,calorific_value,kwh,'
            r'gas_rate,gas_gbp,ccl_rate,standing_rate,standing_gbp,net_gbp,'
            r'vat_gbp,gross_gbp,problem\s*'
            r'750278673,CH017,Parbola,ghoIIl,2018-02-01 00:00,,,'
            r'5.433726578764746,1.02264,M3,1.0,39.3,60.66114545454545,'
            r'0.019548,1.1858040713454543,,,,1.1858040713454543,0,'
            r'1.1858040713454543,']},

    {
        'name': "Gas monthly duration covering bills",
        'path': '/reports/g_monthly_duration?g_supply_id=1&months=1&'
        'finish_year=2015&finish_month=09&finish_day=30&finish_hour=23&'
        'finish_minute=30&compression=False',
        'status_code': 303},
    {
        'path': '/downloads',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r'0029_FINISHED_adminexamplecom_g_monthly_duration_20150901_'
            r'0000_for_1_months_g_supply_1\.ods']},
    {
        'path': '/downloads/'
        '0029_FINISHED_adminexamplecom_g_monthly_duration_20150901_0000_for_'
        '1_months_g_supply_1.ods',
        'status_code': 200,
        'regexes': [
            r'<table:table table:name="Site Level">\s*'
            r'<table:table-column/>\s*'
            r'<table:table-row>\s*'
            r'<table:table-cell office:string-value="creation_date" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="site_id" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="site_name" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="associated_site_ids" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="month" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="gbp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="billed_kwh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="billed_gbp" '
            r'office:value-type="string"/>\s*'
            r'</table:table-row>\s*'
            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:string-value="CH017" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Parbola" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:date-value="2015-09-30T23:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:value="87352.04945454483" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="1775.3578627374982" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="4500901.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="6972.33" '
            r'office:value-type="float"/>\s*'
            r'</table:table-row>\s*'
            r'</table:table>']},

    {
        'name': "Edit gas bill",
        'path': '/g_bills/3/edit',
        'method': 'post',
        'data': {
            'bill_type_id': '3',
            'reference': '8899900012',
            'account': 'college_rooms',
            'issue_year': '2015',
            'issue_month': '11',
            'issue_day': '01',
            'issue_hour': '00',
            'issue_minute': '00',
            'start_year': '2015',
            'start_month': '09',
            'start_day': '01',
            'start_hour': '00',
            'start_minute': '00',
            'finish_year': '2015',
            'finish_month': '09',
            'finish_day': '30',
            'finish_hour': '00',
            'finish_minute': '00',
            'kwh': '4500901',
            'net_gbp': '6972.33',
            'vat_gbp': '1003.89',
            'gross_gbp': '7976.22',
            'raw_lines': 'reference,mprn,bill_type,account,issue_date,'
                'start_date,finish_date,kwh,net_gbp,vat_gbp,gross_gbp,'
                'breakdown,msn,unit,is_corrected,correction_factor,'
                'calorific_value,prev_date,prev_value,prev_type,pres_date,'
                'prev_value,pres_type\n'
                '8899900012,750278673,N,college_rooms,2015-11-01 00:00,'
                '2015-09-01 00:00,2015-09-30 00:00,4500901,6972.33,1003.89,'
                '7976.22,{"gas_rate": 0.019448, "gas_gbp": 8936.13,'
                '"ccl_gbp": 275.32, "vat_0500pc": 0.3, "vat_1500pc": 49.12, '
                '"vat_1750pc": 55.7, "vat_2000pc": 801},hwo8tt,HCUF,FALSE,,'
                '39.300811,2015-09-01 00:00,567822,A,2015-10-01 00:00,'
                '575652,A',
            'breakdown': '{"ccl_gbp": 275.32, "gas_gbp": 8936.13, '
                '"gas_rate": 0.019448, "vat_0500pc": 0.3, "vat_1500pc": 49.12,'
                '"vat_1750pc": 55.7, "vat_2000pc": 801}'},
        'status_code': 303},

    {
        'name': "Gas bill check",
        'path': '/reports/429?g_bill_id=3',
        'status_code': 303},
    {
        'name': "Gas bill check",
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"0030_FINISHED_adminexamplecom_g_bill_check\.csv"],
        'status_code': 200},
    {
        'name': "Gas bill check",
        'path': '/downloads/0030_FINISHED_adminexamplecom_g_bill_check.csv',
        'status_code': 200,
        'regexes': [
            r'batch,bill_reference,bill_type,bill_start_date,'
            r'bill_finish_date,mprn,supply_name,site_code,'
            r'site_name,covered_start,covered_finish,covered_bill_ids,'
            r'covered_units_consumed,virtual_units_consumed,'
            r'covered_correction_factor,virtual_correction_factor,'
            r'covered_unit_code,virtual_unit_code,covered_unit_factor,'
            r'virtual_unit_factor,covered_calorific_value,'
            r'virtual_calorific_value,covered_kwh,virtual_kwh,'
            r'covered_gas_rate,virtual_gas_rate,covered_gas_gbp,'
            r'virtual_gas_gbp,difference_gas_gbp,covered_ccl_rate,'
            r'virtual_ccl_rate,covered_standing_rate,virtual_standing_rate,'
            r'covered_standing_gbp,virtual_standing_gbp,'
            r'difference_standing_gbp,covered_net_gbp,virtual_net_gbp,'
            r'difference_net_gbp,covered_vat_gbp,virtual_vat_gbp,'
            r'difference_vat_gbp,covered_gross_gbp,virtual_gross_gbp,'
            r'difference_gross_gbp,covered_problem,virtual_problem\s*'
            r'TB2,8899900012,W,2015-09-01 00:00,2015-09-30 00:00,750278673,'
            r'Main Gas Supply,CH017,Parbola,2015-09-01 00:00,'
            r'2015-09-30 00:00,3,,0,,1.02264,HCUF,M3,2.8317,1,39.300811,0,'
            r'4500901,0.0,0.019448,0.019548,8936.13,0.0,8936.13,,'
            r'0.00525288,,,,,,6972.33,0.0,6972.33,1003.89,0,1003.89,7976.22,'
            r'0.0,7976.22,,']},

    {
        'name': "Manually add a gas bill",
        'path': '/g_batches/2/add_bill',
        'method': 'post',
        'data': {
            'bill_type_id': "2",
            'mprn': "87614362",
            'reference': "kkhy779",
            'account': "1",
            'issue_year': "2017",
            'issue_month': "02",
            'issue_day': "03",
            'issue_hour': "00",
            'issue_minute': "00",
            'start_year': "2017",
            'start_month': "03",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00",
            'finish_year': "2017",
            'finish_month': "03",
            'finish_day': "31",
            'finish_hour': "23",
            'finish_minute': "30",
            'kwh': "0.00",
            'net': "0.00",
            'vat': "0.00",
            'gross': "0.00",
            'breakdown': '{}'},
        'status_code': 303,
        'regexes': [
            r"/g_bills/4"]},

    {
        'name': "Stark settlement DC bill parser",
        'path': '/dc_bill_imports',
        'method': 'post',
        'data': {
            'dc_batch_id': "13"},
        'files': {
            'import_file': 'test/electricity/bills.settlement.dc.stark.xlsx'
        },
        'status_code': 303,
        'regexes': [
            r"/dc_bill_imports/16"]},

    {
        'name': "Stark settlement DC bill parser",
        'path': '/dc_bill_imports/16',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"All the bills have been successfully loaded and attached to "
            r"the batch\."]},

    {
        'name': "Stark MOP bill parser for annual charges",
        'path': '/mop_bill_imports',
        'method': 'post',
        'data': {
            'mop_batch_id': "14"},
        'files': {
            'import_file': 'test/electricity/bills.annual.mop.stark.xlsx'
        },
        'status_code': 303,
        'regexes': [
            r"/mop_bill_imports/17"]},

    {
        'name': "Stark MOP bill parser for annual charges",
        'path': '/mop_bill_imports/17',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"All the bills have been successfully loaded and attached to "
            r"the batch\."]},

    {
        'name': "Stark non-settlement DC bill parser",
        'path': '/dc_bill_imports',
        'method': 'post',
        'data': {
            'dc_batch_id': "13"},
        'files': {
            'import_file': 'test/electricity/bills.nonsettlement.dc.stark.xlsx'
        },
        'status_code': 303,
        'regexes': [
            r"/dc_bill_imports/18"]},

    {
        'name': "Stark non-settlement DC bill parser",
        'path': '/dc_bill_imports/18',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"All the bills have been successfully loaded and attached to "
            r"the batch\."]},

    {
        'name': "Gas batch check. Bills with different LDZs",
        'path': '/g_batches/2/add_bill',
        'method': 'post',
        'data': {
            'bill_type_id': "2",
            'mprn': "750278673",
            'reference': "765988",
            'account': "1",
            'issue_year': "2017",
            'issue_month': "02",
            'issue_day': "03",
            'issue_hour': "00",
            'issue_minute': "00",
            'start_year': "2017",
            'start_month': "03",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00",
            'finish_year': "2017",
            'finish_month': "03",
            'finish_day': "31",
            'finish_hour': "23",
            'finish_minute': "30",
            'kwh': "0.00",
            'net': "0.00",
            'vat': "0.00",
            'gross': "0.00",
            'breakdown': '{}'},
        'status_code': 303,
        'regexes': [
            r"/g_bills/5"]},
    {
        'name': "Gas batch check",
        'path': '/reports/429?g_batch_id=2',
        'status_code': 303},
    {
        'name': "Gas bill check",
        'path': '/downloads',
        'tries': {'max': 20, 'period': 1},
        'regexes': [
            r"0031_FINISHED_adminexamplecom_g_bill_check\.csv"],
        'status_code': 200},
    {
        'name': "Gas bill check",
        'path': '/downloads/0031_FINISHED_adminexamplecom_g_bill_check.csv',
        'status_code': 200,
        'regexes': [
            r'TB2,765988,N,2017-03-01 00:00,2017-03-31 23:30,750278673,'
            r'Main Gas Supply,CH017,Parbola,2017-03-01 00:00,'
            r'2017-03-31 23:30,5,,0,,1.02264,,M3,,1.0,,39.3,0.00,0.0,,'
            r'0.019548,,0.0,,,0.00195,,67.8,,67.8,,0.00,67.8,-67.8,0.00,0,0.0,'
            r'0.00,67.8,-67.8,,\s*'
            r'TB2,8899900012,W,2015-09-01 00:00,2015-09-30 00:00,750278673,'
            r'Main Gas Supply,CH017,Parbola,2015-09-01 00:00,2015-09-30 00:00,'
            r'3,,0,,1.02264,HCUF,M3,2.8317,1,39.300811,0,4500901,0.0,'
            r'0.019448,0.019548,8936.13,0.0,8936.13,,0.00525288,,,,,,6972.33,'
            r'0.0,6972.33,1003.89,0,1003.89,7976.22,0.0,7976.22,,\s*'
            r'TB2,kkhy779,N,2017-03-01 00:00,2017-03-31 23:30,87614362,'
            r'Main Gas 1,CI017,Roselands,2017-03-01 00:00,2017-03-31 23:30,'
            r'4,,0,,1.02264,,M3,,1.0,,39.1,0.00,0.0,,0.019548,,0.0,,,'
            r'0.00195,,67.8,,67.8,,0.00,67.8,-67.8,0.00,0,0.0,0.00,67.8,-67.8,'
            r','
        ]
    },
    {
        'name': "Try adding a DC rate script.",
        'path': '/dc_contracts/8/add_rate_script',
        'method': 'post',
        'data': {
            'start_year': "2010",
            'start_month': "05",
            'start_day': "01",
            'start_hour': "00",
            'start_minute': "00",
            'insert': "Insert"},
        'regexes': [
            r"/dc_rate_scripts/56"],
        'status_code': 303},

    {
        'name': "Stark MOP bill parser for activities",
        'path': '/mop_bill_imports',
        'method': 'post',
        'data': {
            'mop_batch_id': "14"},
        'files': {
            'import_file': 'test/electricity/bills.activity.mop.stark.xlsx'
        },
        'status_code': 303,
        'regexes': [
            r"/mop_bill_imports/19"
        ]
    },

    {
        'name': "Stark MOP bill parser for activities",
        'path': '/mop_bill_imports/19',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"All the bills have been successfully loaded and attached to "
            r"the batch\."
        ]
    },

    {
        'name': "Stark DC Non-settlement bill parser (old)",
        'path': '/dc_bill_imports',
        'method': 'post',
        'data': {
            'dc_batch_id': "13"},
        'files': {
            'import_file': 'test/electricity/bills_old.nonsettlement.dc.stark.'
            'xlsx'
        },
        'status_code': 303,
        'regexes': [
            r"/dc_bill_imports/20"
        ]
    },

    {
        'name': "Stark DC Non-settlement bill parser (old)",
        'path': '/dc_bill_imports/20',
        'tries': {},
        'status_code': 200,
        'regexes': [
            r"All the bills have been successfully loaded and attached to "
            r"the batch\."
        ]
    },

    {
        'name': "General import channel snag unignore",
        'path': '/general_imports',
        'method': 'post',
        'files': {
            'import_file': 'test/electricity/gi_channel_snag_ignore.csv'
        },
        'status_code': 303,
        'regexes': [
            r"/general_imports/31"]
    },
    {
        'path': '/general_imports/31',
        'tries': {},

        # Check good error message
        'regexes': [
            r"The file has been imported successfully\."
        ],
        'status_code': 200
    },
    {
        'name': "Check it's been un-ignored.",
        'path': '/channel_snags/3',
        'regexes': [
            r'<th>Ignored\?</th>\s*'
            r'<td>\s*'
            r'Not ignored\s*'
            r'</td>\s*'
        ],
        'status_code': 200
    },

    {
        'name': "Scenario with new generation",
        'path': '/supplier_contracts/19/edit',
        'method': 'post',
        'data': {
            'party_id': "106",  # COOP
            'name': "scenario_used",
            'start_year': "2000",
            'start_month': "01",
            'start_day': "03",
            'start_hour': "00",
            'start_minute': "00",
            'charge_script': "",
            'properties': """
{
  "scenario_start": 2009-08-01T00:00:00Z,
  "scenario_duration": 1,

  "era_maps": {
    2000-08-01T00:00:00Z: {
      "llfcs": {
        "22": {
          "new_export": "521"
        }
      },
      "supplier_contracts": {
        "new_export": 10
      }
    }
  },

  "hh_data": {
    "CI017": {
      "generated": "
            2009-08-01 00:00, 40
            2009-08-15 00:00, 40"
    }
  }
}
"""},
        'regexes': [
            r"/supplier_contracts/19"],
        'status_code': 303},

    {
        'name': "Scenario with new generation",
        'path': '/reports/247?site_id=4&scenario_id=19&compression=False',
        'status_code': 303},
    {
        'name': "Scenario with new generation",
        'path': '/downloads',
        'tries': {'max': 30, 'period': 1},
        'status_code': 200,
        'regexes': [
            r"0032_FINISHED_adminexamplecom_scenario_used_20090801_0000_for_1"
            r"_months_site_CI017\.ods"]},
    {
        'name': "Scenario with new generation",
        'path': '/downloads/'
        '0032_FINISHED_adminexamplecom_scenario_used_20090801_0000_for_1_'
        'months_site_CI017.ods',
        'status_code': 200,
        'regexes': [
            r'<office:spreadsheet>\s*'
            r'<table:table table:name="Site Level">\s*'
            r'<table:table-column/>\s*'
            r'<table:table-row>\s*'
            r'<table:table-cell office:string-value="creation-date" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="site-id" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="site-name" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="associated-site-ids" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="month" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="metering-type" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="sources" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="generator-types" '
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
            r'</table:table-row>\s*'
            r'<table:table-row>\s*'
            r'<table:table-cell '
            r'office:date-value="\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:string-value="CI017" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="Roselands" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:date-value="2009-08-31T23:30:00" '
            r'office:value-type="date" table:style-name="cell_date"/>\s*'
            r'<table:table-cell office:string-value="hh" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="gen, net" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:string-value="chp" '
            r'office:value-type="string"/>\s*'
            r'<table:table-cell office:value="4326.415548931821" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="74.17709885742673" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="80.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="3"/>\s*'
            r'<table:table-cell office:value="5.822901142573274" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="4332.238450074394" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="3428.802108\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="94.42832606\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="4"/>\s*'
            r'<table:table-cell office:value="0.0" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="3428.802108\d*" '
            r'office:value-type="float"/>\s*'
            r'<table:table-cell office:value="0" office:value-type="float" '
            r'table:number-columns-repeated="3"/>\s*'
            r'</table:table-row>\s*'
            r'</table:table>\s*'
        ]
    },

    {
        'name': "Delete a gas era",
        'path': '/g_eras/3/edit',
        'method': 'post',
        'data': {
            'delete': 'Delete'
        },
        'status_code': 303,
        'regexes': [
            r'/g_supplies/1'
        ]
    },

    {
        'name': "View add gas read",
        'path': '/g_bills/4/add_read',
        'status_code': 200,
        'regexes': [
            r'<input type="checkbox" name="is_corrected" value="true">'
        ]
    },

    {
        'name': "Delete a gas rate script",
        'path': '/g_rate_scripts/2/edit',
        'method': 'post',
        'data': {
            'delete': 'Delete'
        },
        'status_code': 303,
        'regexes': [
            r'/g_contracts/1'
        ]
    },

    {
        'name': "Gas read delete",
        'path': '/g_reads/3/edit',
        'method': 'post',
        'data': {
            'delete': 'Delete'
        },
        'status_code': 303,
        'regexes': [
            r'/g_bills/3'
        ]
    },

    {
        'name': "View gas notes",
        'path': '/g_supplies/4/notes',
        'status_code': 200
    },

    {
        'name': "View add gas note",
        'path': '/g_supplies/4/notes/add',
        'status_code': 200
    }
]
