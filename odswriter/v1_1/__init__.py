from zipfile import ZipFile
import decimal
import datetime
from xml.dom.minidom import parseString

import odswriter.v1_1.ods_components
from odswriter.v1_1.formula import Formula

'''
from xml.etree import ElementTree

def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

root = ElementTree.parse('/tmp/xmlfile').getroot()
indent(root)
ElementTree.dump(root)
'''

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
        dom = parseString(odswriter.v1_1.ods_components.content_xml)
        self.dom = dom
        styles_elem = dom.documentElement.insertBefore(
            dom.createElement("office:automatic-styles"),
            dom.documentElement.firstChild)
        date_style_elem = styles_elem.appendChild(
            dom.createElement("number:date-style"))
        date_style_elem.setAttribute("style:name", "DateISO")
        elem = date_style_elem.appendChild(dom.createElement("number:year"))
        elem.setAttribute('number:style', 'long')
        elem = date_style_elem.appendChild(dom.createElement("number:text"))
        elem.appendChild(dom.createTextNode('-'))
        elem = date_style_elem.appendChild(dom.createElement("number:month"))
        elem.setAttribute('number:style', 'long')
        elem = date_style_elem.appendChild(dom.createElement("number:text"))
        elem.appendChild(dom.createTextNode('-'))
        elem = date_style_elem.appendChild(dom.createElement("number:day"))
        elem.setAttribute('number:style', 'long')
        elem = date_style_elem.appendChild(dom.createElement("number:text"))
        elem.appendChild(dom.createTextNode(' '))
        elem = date_style_elem.appendChild(dom.createElement("number:hours"))
        elem.setAttribute('number:style', 'long')
        elem = date_style_elem.appendChild(dom.createElement("number:text"))
        elem.appendChild(dom.createTextNode(':'))
        elem = date_style_elem.appendChild(dom.createElement("number:minutes"))
        elem.setAttribute('number:style', 'long')

        style_elem = styles_elem.appendChild(dom.createElement('style:style'))
        style_elem.setAttribute('style:name', 'cDateISO')
        style_elem.setAttribute('style:family', 'table-cell')
        style_elem.setAttribute('style:data-style-name', 'DateISO')

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
        self.default_sheet = None

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
        self.zipf.writestr(
            "content.xml", self.dom.toxml(encoding="utf-8"))
        # "content.xml", self.dom.toprettyxml(indent='  ', encoding="utf-8"))
        self.zipf.close()

    def writerow(self, cells):
        """
        Write a row of cells into the default sheet of the spreadsheet.
        :param cells: A list of cells (most basic Python types supported).
        :return: Nothing.
        """
        if self.default_sheet is None:
            self.default_sheet = self.new_sheet()
        self.default_sheet.writerow(cells)

    def writerows(self, rows):
        """
        Write rows into the default sheet of the spreadsheet.
        :param rows: A list of rows, rows are lists of cells - see writerow.
        :return: Nothing.
        """
        for row in rows:
            self.writerow(row)

    def new_sheet(self, name=None):
        """
        Create a new sheet in the spreadsheet and return it so content can be
        added.
        :param name: Optional name for the sheet.
        :return: Sheet object
        """
        return Sheet(self.dom, name)


class Sheet(object):
    def __init__(self, dom, name=None):
        self.dom = dom
        spreadsheet = self.dom.getElementsByTagName("office:spreadsheet")[0]
        self.table = self.dom.createElement("table:table")
        spreadsheet.appendChild(self.table)
        if name:
            self.table.setAttribute("table:name", name)
        column = self.dom.createElement("table:table-column")
        self.table.appendChild(column)

    def writerow(self, cells):
        row = self.dom.createElement("table:table-row")
        for cell_data in cells:
            cell = self.dom.createElement("table:table-cell")
            # text = None

            if isinstance(cell_data, (datetime.date, datetime.datetime)):
                cell.setAttribute("office:value-type", "date")
                cell.setAttribute(
                    "office:date-value",
                    cell_data.strftime("%Y-%m-%dT%H:%M:%S"))
                cell.setAttribute("table:style-name", "cDateISO")
                # text = date_str

            elif isinstance(cell_data, datetime.time):
                cell.setAttribute("office:value-type", "time")
                cell.setAttribute("office:time-value",
                                  cell_data.strftime("PT%HH%MM%SS"))
                # text = cell_data.strftime("%H:%M:%S")

            elif isinstance(cell_data, bool):
                # Bool condition must be checked before numeric because:
                # isinstance(True, int): True
                # isinstance(True, bool): True
                cell.setAttribute("office:value-type", "boolean")
                cell.setAttribute("office:boolean-value",
                                  "true" if cell_data else "false")
                # text = "TRUE" if cell_data else "FALSE"

            elif isinstance(cell_data, (float, int, decimal.Decimal, long)):
                cell.setAttribute("office:value-type", "float")
                float_str = unicode(cell_data)
                cell.setAttribute("office:value", float_str)
                # text = float_str

            elif isinstance(cell_data, Formula):
                cell.setAttribute("table:formula", str(cell_data))

            elif cell_data is None:
                pass  # Empty element

            else:
                # String and unknown types become string cells
                cell.setAttribute("office:value-type", "string")
                cell.setAttribute("office:string-value", unicode(cell_data))
                # text = unicode(cell_data)
            '''
            if text:
                p = self.dom.createElement("text:p")
                p.appendChild(self.dom.createTextNode(text))
                cell.appendChild(p)
            '''
            row.appendChild(cell)

        self.table.appendChild(row)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
