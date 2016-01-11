from net.sf.chellow.monad import Monad
import traceback
from chellow import app
from chellow.models import Contract


LIBS = (
    'utils', 'db', 'templater', 'bank_holidays', 'computer', 'scenario',
    'bsuos', 'tlms', 'general_import', 'hh_importer', 'bill_import', 'edi_lib',
    'system_price', 'rcrc', 'duos', 'triad_rates', 'triad', 'ccl', 'aahedc',
    'dloads', 'ro')


class LibDict(dict):
    pass


def on_start_up(ctx):
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

    Monad.getUtils()['impt'](globals(), *LIBS)

    for lib_name in LIBS:
        try:
            globals()[lib_name].startup()
        except AttributeError:
            pass
