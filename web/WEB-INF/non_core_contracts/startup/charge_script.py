import sys
from net.sf.chellow.billing import Contract
from net.sf.chellow.monad import Hiber, Monad
import collections
from java.lang import System
from org.python.util import PythonInterpreter
from java.io import LineNumberReader, File
from org.python.core import PyString
import tempfile
import os

class LibDict(dict):
    pass

def on_start_up(ctx):
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
                        line_reader = LineNumberReader(FileReader(File(lib_path, lib_content)))

                        line = line_reader.readLine()

                        while line is not None:
                            line = line.strip()

                            if len(line) == 0:
                                continue

                            if line.startswith("#"):
                                continue

                            if line.startswith("import"):
                                interp.exec(line)
                                continue

                            archive_file = File(lib_path, line)

                            archive_real_path = archiveFile.getAbsolutePath()

                            sys_state.path.append(PyString(archive_real_path))
                            line = line_reader.readLine()
                    finally:
                        line_reader.close()

    for contract_name in ['utils', 'pre_db', 'db', 'templater', 'bsuos',
            'tlms', 'general_import', 'hh_importer', 'bill_import', 'edi_lib', 'system_price_bmreports', 'system_price_elexon', 'system_price', 'rcrc', 'tlms', 'computer', 'duos', 'triad_rates', 'triad', 'ccl', 'aahedc']:
        try:
            contract = Contract.getNonCoreContract(contract_name)
            nspace = LibDict()
            exec(contract.getChargeScript(), nspace)
            for k, v in nspace.iteritems():
                if not hasattr(nspace, k):
                    setattr(nspace, k, v)
            nspace['db_id'] = contract.id
            setattr(nspace, 'db_id', contract.id)
            ctx.setAttribute(
                "net.sf.chellow." + contract_name, nspace)
        except:
            cont = "\n Problem with contract " + contract_name
            sys.stderr.write(cont)
            System.err.write(cont)
            raise
        
    download_path = Monad.getContext().getRealPath("/downloads")
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    Hiber.close()

    Monad.getUtils()['impt'](globals(), 'hh_importer', 'bsuos', 'rcrc', 'tlms', 'system_price_bmreports', 'system_price_elexon')

    hh_importer.startup()
    bsuos.startup()
    rcrc.startup()
    tlms.startup()
    system_price_elexon.startup()
    system_price_bmreports.startup()
