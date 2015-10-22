import sys
from net.sf.chellow.monad import Monad
import traceback

LIBS = (
    'utils', 'db', 'templater', 'bank_holidays', 'computer', 'scenario',
    'bsuos', 'tlms', 'general_import', 'hh_importer', 'bill_import', 'edi_lib',
    'system_price', 'rcrc', 'duos', 'triad_rates', 'triad', 'ccl', 'aahedc',
    'dloads', 'ro')


class LibDict(dict):
    pass


def jython_start(ctx):
    from net.sf.chellow.billing import Contract
    from net.sf.chellow.monad import Hiber
    from org.python.util import PythonInterpreter
    from java.io import LineNumberReader, File, FileReader
    from org.python.core import PyString

    interp = PythonInterpreter()

    sys_state = interp.getSystemState()

    lib_path = ctx.getRealPath("/WEB-INF/lib-python")
    if lib_path is not None:
        lib_dir = File(lib_path)
        if lib_dir.exists():
            sys_state.path.append(PyString(lib_path))

            # Now check for .pth files in lib-python and process each one

            for lib_content in lib_dir.list():
                if lib_content.endswith(".pth"):
                    line_reader = None
                    try:
                        line_reader = LineNumberReader(
                            FileReader(File(lib_path, lib_content)))

                        line = line_reader.readLine()

                        while line is not None:
                            line = line.strip()

                            if len(line) == 0:
                                continue

                            if line.startswith("#"):
                                continue

                            if line.startswith("import"):
                                efunc = getattr(interp, 'exec')
                                efunc(line)
                                continue

                            archive_file = File(lib_path, line)

                            archive_real_path = archive_file.getAbsolutePath()

                            sys_state.path.append(PyString(archive_real_path))
                            line = line_reader.readLine()
                    finally:
                        line_reader.close()

    for contract_name in LIBS:
        contract = Contract.getNonCoreContract(contract_name)
        nspace = LibDict()
        nspace['db_id'] = contract.id
        exec(contract.getChargeScript(), nspace)
        for k, v in nspace.items():
            if not hasattr(nspace, k):
                setattr(nspace, k, v)
        ctx.setAttribute("net.sf.chellow." + contract_name, nspace)

    Hiber.close()


def cpython_start():
    from chellow import app
    from chellow.models import Contract

    libs = {}
    app.config['libs'] = libs
    for contract_name in LIBS:
        try:
            contract = Contract.get_non_core_by_name(contract_name)
            nspace = LibDict()
            nspace['db_id'] = contract.id
            exec(contract.charge_script, nspace)
            for k, v in nspace.items():
                if not hasattr(nspace, k):
                    setattr(nspace, k, v)
            libs[contract_name] = nspace
        except Exception:
            raise Exception(
                "While importing " + contract_name + " " +
                traceback.format_exc())


def on_start_up(ctx):
    if sys.platform.startswith('java'):
        jython_start(ctx)
    else:
        cpython_start()

    Monad.getUtils()['impt'](globals(), *LIBS)

    for lib_name in LIBS:
        try:
            globals()[lib_name].startup()
        except AttributeError:
            pass
