from zipfile import ZipFile
import decimal
import datetime
import odswriter.v1_1.ods_components
from odswriter.v1_1.formula import Formula
import xml.sax.saxutils
import tempfile
import os.path
import shutil

CONTENT_ATTRS = {
    'xmlns:office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
    'xmlns:style': "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
    'xmlns:text': "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    'xmlns:table': "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    'xmlns:draw': "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0",
    'xmlns:fo': 'urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0',
    'xmlns:xlink': "http://www.w3.org/1999/xlink",
    'xmlns:dc': "http://purl.org/dc/elements/1.1/",
    'xmlns:meta': "urn:oasis:names:tc:opendocument:xmlns:meta:1.0",
    'xmlns:number': "urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0",
    'xmlns:presentation':
        "urn:oasis:names:tc:opendocument:xmlns:presentation:1.0",
    'xmlns:svg': "urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0",
    'xmlns:chart': "urn:oasis:names:tc:opendocument:xmlns:chart:1.0",
    'xmlns:dr3d': "urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0",
    'xmlns:math': "http://www.w3.org/1998/Math/MathML",
    'xmlns:form': "urn:oasis:names:tc:opendocument:xmlns:form:1.0",
    'xmlns:script': "urn:oasis:names:tc:opendocument:xmlns:script:1.0",
    'xmlns:dom': "http://www.w3.org/2001/xml-events",
    'xmlns:xforms': "http://www.w3.org/2002/xforms",
    'xmlns:of': "urn:oasis:names:tc:opendocument:xmlns:of:1.2",
    'office:version': "1.1"}


# Basic compatibility setup for Python 2 and Python 3.

try:
    long
except NameError:
    long = int

try:
    unicode
except NameError:
    unicode = str

# End compatibility setup.


def att_str(atts):
    return ''.join(
        ' ' + k + '=' + xml.sax.saxutils.quoteattr(v)
        for k, v in sorted(atts.items()))


def begin_elem(f, tag, atts=None):
    if atts is None:
        atts = {}
    f.write('<' + tag + att_str(atts) + '>')


def end_elem(f, tag):
    f.write('</' + tag + '>')


def empty_elem(f, tag, atts=None):
    if atts is None:
        atts = {}
    f.write('<' + tag + att_str(atts) + '/>')


class ODSWriter(object):
    """
    Utility for writing OpenDocument Spreadsheets. Can be used in simple 1
    sheet mode (use writerow/writerows) or with multiple sheets (use
    new_sheet). It is suggested that you use with object like a
    context manager.
    """
    def __init__(self, odsfile):
        self.zipf = ZipFile(odsfile, "w")
        # Make the skeleton of an ODS.

        self.zipf.writestr(
            "mimetype",
            odswriter.v1_1.ods_components.mimetype.encode("utf-8"))
        self.zipf.writestr(
            "meta.xml",
            odswriter.v1_1.ods_components.meta_xml.encode("utf-8"))
        self.zipf.writestr(
            "styles.xml",
            odswriter.v1_1.ods_components.styles_xml.encode("utf-8"))
        self.zipf.writestr(
            "settings.xml",
            odswriter.v1_1.ods_components.settings_xml.encode("utf-8"))
        self.zipf.writestr(
            "META-INF/manifest.xml",
            odswriter.v1_1.ods_components.manifest_xml.encode("utf-8"))
        self.sheets = []

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.close()

    def close(self):
        """
        Finalises the compressed version of the spreadsheet. If you aren't
        using the context manager ('with' statement, you must call this
        manually, it is not triggered automatically like on a file object.
        :return: Nothing.
        """

        f_dir = tempfile.mkdtemp()
        f_path = os.path.join(f_dir, "content.xml")
        with open(f_path, "w") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>')
            begin_elem(f, 'office:document-content', CONTENT_ATTRS)
            begin_elem(f, "office:automatic-styles")
            empty_elem(f, "number:date-style", {"style:name": "DateISO"})
            empty_elem(f, "number:year", {'number:style': 'long'})
            begin_elem(f, "number:text", {})
            f.write('-')
            end_elem(f, "number:text")
            empty_elem(f, "number:month", {'number:style': 'long'})
            begin_elem(f, "number:text", {})
            f.write('-')
            end_elem(f, "number:text")
            empty_elem(f, "number:day", {'number:style': 'long'})
            begin_elem(f, "number:text", {})
            f.write(' ')
            end_elem(f, "number:text")
            empty_elem(f, "number:hours", {'number:style': 'long'})
            begin_elem(f, "number:text", {})
            f.write(':')
            end_elem(f, "number:text")
            empty_elem(f, "number:minutes", {'number:style': 'long'})
            empty_elem(f, 'style:style', {
                'style:name': 'cDateISO',
                'style:family': 'table-cell',
                'style:data-style-name': 'DateISO'})
            end_elem(f, "office:automatic-styles")
            begin_elem(f, 'office:body')
            begin_elem(f, 'office:spreadsheet')
            for sheet in self.sheets:
                begin_elem(f, "table:table", {"table:name": sheet.name})
                empty_elem(f, "table:table-column")

                for row in sheet.rows:
                    begin_elem(f, "table:table-row")
                    row_list = []
                    for cell in row:
                        atts = {}

                        if isinstance(
                                cell, (datetime.date, datetime.datetime)):
                            atts["office:value-type"] = "date"
                            atts["office:date-value"] = cell.strftime(
                                "%Y-%m-%dT%H:%M:%S")
                            atts["table:style-name"] = "cDateISO"

                        elif isinstance(cell, datetime.time):
                            atts["office:value-type"] = "time"
                            atts["office:time-value"] = cell.strftime(
                                "PT%HH%MM%SS")

                        elif isinstance(cell, bool):
                            # Bool condition must be checked before numeric
                            # because:
                            # isinstance(True, int): True
                            # isinstance(True, bool): True
                            atts["office:value-type"] = "boolean"
                            atts["office:boolean-value"] = \
                                "true" if cell else "false"

                        elif isinstance(cell, (float, int, decimal.Decimal)):
                            atts["office:value-type"] = "float"
                            atts["office:value"] = str(cell)

                        elif isinstance(cell, Formula):
                            atts["table:formula"] = str(cell)

                        elif cell is None:
                            pass  # Empty element

                        else:
                            # String and unknown types become string cells
                            atts["office:value-type"] = "string"
                            atts["office:string-value"] = str(cell)
                        if len(row_list) > 0 and row_list[-1]['atts'] == atts:
                            row_list[-1]['count'] += 1
                        else:
                            row_list.append({'count': 1, 'atts': atts})

                    for cell_dict in row_list:
                        ct = cell_dict['count']
                        atts = cell_dict['atts']
                        if ct > 1:
                            atts['table:number-columns-repeated'] = str(ct)
                        empty_elem(f, "table:table-cell", atts)
                    end_elem(f, "table:table-row")
                end_elem(f, "table:table")
            end_elem(f, 'office:spreadsheet')
            end_elem(f, 'office:body')
            end_elem(f, 'office:document-content')

        self.zipf.write(f_path, "content.xml")
        self.zipf.close()
        shutil.rmtree(f_dir)

    def new_sheet(self, name):
        sheet = Sheet(name)
        self.sheets.append(sheet)
        return sheet


class Sheet(object):
    def __init__(self, name):
        self.name = name
        self.rows = []

    def writerow(self, row):
        self.rows.append(row)
