import sys
inv = globals()['inv']

if sys.platform.startswith('java'):
    from java.text import DecimalFormat
    from java.lang import Runtime, System, Thread
    from java.io import StringWriter, InputStreamReader
    from net.sf.chellow.monad import Hiber, Monad, MonadMessage
    from java.lang.management import ManagementFactory
    from com.jezhumble.javasysmon import JavaSysMon
    from net.sf.chellow.billing import Contract

    source, doc = globals()['source'], globals()['doc']

    interrupt_id = None
    if inv.getRequest().getMethod() == "POST":
        if inv.hasParameter('interrupt'):
            interrupt_id = inv.getLong('thread-id')
            Monad.getUtils()['imprt'](
                globals(), {
                    'db': [
                        'HhDatum', 'Site', 'Supply', 'set_read_write',
                        'session'],
                    'utils': ['UserException', 'HH', 'form_date'],
                    'templater': ['render', 'on_start_report', 'get_report']})

        elif inv.hasParameter('run_shutdown'):
            shutdown_contract = Contract.getNonCoreContract('shutdown')
            shutdown_contract.callFunction(
                'on_shut_down', [Monad.getContext()])
            source.appendChild(
                MonadMessage("Shut down successfully.").toXml(doc))

        elif inv.hasParameter('run_startup'):
            startup_contract = Contract.getNonCoreContract('startup')
            startup_contract.callFunction('on_start_up', [Monad.getContext()])
        elif inv.hasParameter('cancel_backend'):
            backend_pid = inv.getLong('backend_pid')
            con = Hiber.session().connection()
            stmt = con.createStatement()
            stmt.execute(
                "select pg_terminate_backend(" + str(backend_pid) + ")")
            stmt.close()
            Hiber.commit()
            source.appendChild(MonadMessage("Cancelled backend.").toXml(doc))

    df = DecimalFormat("###,###,###,###,##0")
    runtime = Runtime.getRuntime()
    source.setAttribute("free-memory", df.format(runtime.freeMemory()))
    source.setAttribute("max-memory", df.format(runtime.maxMemory()))
    source.setAttribute("total-memory", df.format(runtime.totalMemory()))
    source.setAttribute(
        "available-processors", str(runtime.availableProcessors()))

    source.setAttribute(
        "system-load-average",
        str(ManagementFactory.getOperatingSystemMXBean().
            getSystemLoadAverage()))

    mon = JavaSysMon()
    source.setAttribute(
        'cpu-frequency-in-hz', df.format(mon.cpuFrequencyInHz()))
    source.setAttribute('current-pid', df.format(mon.currentPid()))
    source.setAttribute('num-cpus', df.format(mon.numCpus()))
    source.setAttribute('os-name', mon.osName())
    source.setAttribute('uptime-in-seconds', df.format(mon.uptimeInSeconds()))
    cpu = mon.cpuTimes()
    source.setAttribute('idle-millis', df.format(cpu.getIdleMillis()))
    source.setAttribute('system-millis', df.format(cpu.getSystemMillis()))
    source.setAttribute('total-millis', df.format(cpu.getTotalMillis()))
    source.setAttribute('user-millis', df.format(cpu.getUserMillis()))

    props = doc.createElement('properties')
    source.appendChild(props)
    sw = StringWriter()
    System.getProperties().store(sw, None)
    props.setTextContent(sw.toString())

    req_map = dict(
        [
            [entry.getKey(), entry.getValue()]
            for entry in
            inv.getMonad().getServletConfig().getServletContext()
            .getAttribute('net.sf.chellow.request_map').entrySet()])

    for entry in Thread.getAllStackTraces().entrySet():
        thread_element = doc.createElement('thread')
        source.appendChild(thread_element)
        thread = entry.getKey()

        '''
        if interrupt_id is not None:
            request = get_report(thread.getId())
            if request is not None:
                request.getResponse().getOutputStream().close()
        '''

        if thread.getId() == interrupt_id:
            thread.interrupt()
        '''
        if thread.getId() == 43:
            thread.stop()
        '''

        trace = ''.join([str(item) + "\r\n" for item in entry.getValue()])
        thread_element.setTextContent(trace + " " + str(dir(thread)))
        thread_element.setAttribute('id', str(thread.getId()))
        thread_element.setAttribute('name', thread.getName())
        thread_element.setAttribute(
            'is-interrupted', str(thread.isInterrupted()))
        thread_element.setAttribute('status', thread.getState().toString())
        thread_element.setAttribute('request', req_map.get(thread.getId()))

    con = Hiber.session().connection()
    db_metadata = con.getMetaData()
    source.setAttribute(
        "db-product-name", db_metadata.getDatabaseProductName())
    source.setAttribute(
        "db-product-version", db_metadata.getDatabaseProductVersion())
    source.setAttribute("db-driver-name", db_metadata.getDriverName())
    source.setAttribute("db-driver-version", db_metadata.getDriverVersion())
    istream = InputStreamReader(
        Monad.getContext().getResource("/WEB-INF/VERSION").openStream(),
        "UTF-8")
    c = istream.read()
    sr = StringWriter()
    while c != -1:
        sr.write(c)
        c = istream.read()
    source.setAttribute("chellow-version", sr.toString())

    source.setAttribute(
        'transaction-isolation', str(con.getTransactionIsolation()))

    pstmt = con.prepareStatement("select * from pg_stat_activity")
    rs = pstmt.executeQuery()
    rs_meta = rs.getMetaData()
    pg_stat_activity_el = doc.createElement('pg-stat-activity')
    source.appendChild(pg_stat_activity_el)
    for i in range(1, rs_meta.getColumnCount() + 1):
        column_el = doc.createElement('column')
        pg_stat_activity_el.appendChild(column_el)
        column_el.setAttribute(
            'name',
            rs_meta.getColumnName(i) + ' (' + rs_meta.getColumnTypeName(i) +
            ')')

    while rs.next():
        row_el = doc.createElement('row')
        pg_stat_activity_el.appendChild(row_el)
        for i in range(1, rs_meta.getColumnCount() + 1):
            cell_el = doc.createElement('cell')
            row_el.appendChild(cell_el)
            cell_el.setAttribute('value', rs.getString(i))

    settings_el = doc.createElement('pg-settings')
    source.appendChild(settings_el)
    for setting in (
            'autovacuum', 'autovacuum_naptime', 'autovacuum_max_workers',
            'autovacuum_vacuum_threshold', 'autovacuum_analyze_threshold',
            'autovacuum_vacuum_scale_factor',
            'autovacuum_analyze_scale_factor',
            'max_pred_locks_per_transaction', 'track_counts',
            'track_activities', 'port', 'listen_addresses'):
        pstmt = con.prepareStatement("show " + setting)
        rs = pstmt.executeQuery()
        while rs.next():
            setting_el = doc.createElement('setting')
            settings_el.appendChild(setting_el)
            setting_el.setAttribute('name', setting)
            setting_el.setAttribute('value', str(rs.getString(setting)))

    pstmt = con.prepareStatement(
        "select * from pg_stat_all_tables where schemaname = 'public'")
    rs = pstmt.executeQuery()
    rs_meta = rs.getMetaData()
    pg_stat_all_tables_el = doc.createElement('pg-stat-all-tables')
    source.appendChild(pg_stat_all_tables_el)
    for i in range(1, rs_meta.getColumnCount() + 1):
        column_el = doc.createElement('column')
        pg_stat_all_tables_el.appendChild(column_el)
        column_el.setAttribute(
            'name',
            rs_meta.getColumnName(i) + ' (' + rs_meta.getColumnTypeName(i) +
            ')')

    while rs.next():
        row_el = doc.createElement('row')
        pg_stat_all_tables_el.appendChild(row_el)
        for i in range(1, rs_meta.getColumnCount() + 1):
            cell_el = doc.createElement('cell')
            row_el.appendChild(cell_el)
            cell_el.setAttribute('value', rs.getString(i))

    rs.close()

    pstmt = con.prepareStatement(
        "select t.relname as table_name, i.relname as index_name, "
        "array_to_string(array_agg(a.attname), ', ') as column_names "
        "from pg_class t, pg_class i, pg_index ix, pg_attribute a, "
        "pg_namespace where t.oid = ix.indrelid "
        "and i.oid = ix.indexrelid and a.attrelid = t.oid "
        "and a.attnum = ANY(ix.indkey) and t.relkind = 'r' "
        "and t.relnamespace = pg_namespace.oid "
        "and pg_namespace.nspname = 'public' "
        "group by t.relname, i.relname, pg_namespace.nspname "
        "order by t.relname, i.relname")
    rs = pstmt.executeQuery()
    rs_meta = rs.getMetaData()
    table_el = doc.createElement('pg-indexes')
    source.appendChild(table_el)
    for i in range(1, rs_meta.getColumnCount() + 1):
        column_el = doc.createElement('column')
        table_el.appendChild(column_el)
        column_el.setAttribute(
            'name',
            rs_meta.getColumnName(i) + ' (' + rs_meta.getColumnTypeName(i) +
            ')')

    while rs.next():
        row_el = doc.createElement('row')
        table_el.appendChild(row_el)
        for i in range(1, rs_meta.getColumnCount() + 1):
            cell_el = doc.createElement('cell')
            row_el.appendChild(cell_el)
            cell_el.setAttribute('value', rs.getString(i))

    rs.close()

    py_libs_el = doc.createElement('py-libs')
    source.appendChild(py_libs_el)
    import sqlalchemy
    py_lib_el = doc.createElement('py-lib')
    py_libs_el.appendChild(py_lib_el)
    py_lib_el.setAttribute('name', 'SQLAlchemy')
    py_lib_el.setAttribute('version', sqlalchemy.__version__)

    import pg8000
    py_lib_el = doc.createElement('py-lib')
    py_libs_el.appendChild(py_lib_el)
    py_lib_el.setAttribute('name', 'pg8000')
    py_lib_el.setAttribute('version', pg8000.__version__)

    '''
    con.rollback()
    con.setAutoCommit(True)
    #pstmt = con.prepareStatement("vacuum analyze")
    pstmt = con.prepareStatement(
        "create index hh_datum_channel_id_idx on hh_datum (channel_id)")
    pstmt.execute()
    pstmt.close()
    con.setAutoCommit(False)
    '''
else:
    template = """
<!DOCTYPE html>
<html>
  <head>
    <link rel="stylesheet" type="text/css"
      href="{{ context_path }}/reports/19/output/" />
    <title>Chellow &gt; System</title>
  </head>
  <body>
    <p>
      <a href="/chellow/reports/1/output/">Chellow</a> &gt; System
    </p>

    <p>{{ message }}</p>

    <form method="post" action="/chellow/reports/171/output/">
      <fieldset>
        <legend>Run shutdown script</legend>
        <input type="submit" name="run_shutdown" value="Run">
      </fieldset>
    </form>
    <form method="post" action="/chellow/reports/171/output/">
      <fieldset>
        <legend>Run startup script</legend>
        <input type="submit" name="run_startup" value="Run">
      </fieldset>
    </form>
  </body>
</html>
"""
    from net.sf.chellow.monad import Monad
    import db
    import templater
    import computer
    Monad.getUtils()['impt'](globals(), 'utils', 'templater', 'computer', 'db')

    Contract = db.Contract
    render = templater.render

    sess = None
    try:
        sess = db.session()
        caches = {}

        if inv.getRequest().getMethod() == "POST":
            if inv.hasParameter('run_shutdown'):
                shutdown_contract = Contract.get_non_core_by_name(
                    sess, 'shutdown')
                computer.contract_func(
                    caches, shutdown_contract, 'on_shut_down', None)(None)
                render(inv, template, {'message': 'Shut down successfully.'})
            elif inv.hasParameter('run_startup'):
                shutdown_contract = Contract.get_non_core_by_name(
                    sess, 'startup')
                computer.contract_func(
                    caches, shutdown_contract, 'on_start_up', None)(None)
                render(inv, template, {'message': 'Started up successfully.'})
        else:
            render(inv, template, {})
    finally:
        if sess is not None:
            sess.close()
