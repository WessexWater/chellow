import odswriter.v1_1
import odswriter.v1_2


def writer(odsfile, version='1.2', *args, **kwargs):
    """
        Returns an ODSWriter object.

        Python 3: Make sure that the file you pass is mode b:
        f = open("spreadsheet.ods", "wb")
        odswriter.writer(f)
        ...
        Otherwise you will get "TypeError: must be str, not bytes"
    """
    if version == '1.1':
        return odswriter.v1_1.ODSWriter(odsfile, *args, **kwargs)
    elif version == '1.2':
        return odswriter.v1_2.ODSWriter(odsfile, *args, **kwargs)
    else:
        raise Exception("The argument 'version' must be '1.1' or '1.2'.")
