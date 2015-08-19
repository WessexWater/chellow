content_xml = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-content
        xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
        xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
        xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
        xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
        xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
        xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
        xmlns:xlink="http://www.w3.org/1999/xlink"
        xmlns:dc="http://purl.org/dc/elements/1.1/"
        xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
        xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0"
        xmlns:presentation="urn:oasis:names:tc:opendocument:xmlns:presentation:1.0"
        xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"
        xmlns:chart="urn:oasis:names:tc:opendocument:xmlns:chart:1.0"
        xmlns:dr3d="urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0"
        xmlns:math="http://www.w3.org/1998/Math/MathML"
        xmlns:form="urn:oasis:names:tc:opendocument:xmlns:form:1.0"
        xmlns:script="urn:oasis:names:tc:opendocument:xmlns:script:1.0"
        xmlns:dom="http://www.w3.org/2001/xml-events"
        xmlns:xforms="http://www.w3.org/2002/xforms"
        xmlns:of="urn:oasis:names:tc:opendocument:xmlns:of:1.2"
        office:version="1.1">
    <office:body>
        <office:spreadsheet>
        </office:spreadsheet>
    </office:body>
</office:document-content>"""

mimetype = "application/vnd.oasis.opendocument.spreadsheet"

manifest_xml = """<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest
        xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0">
    <manifest:file-entry
            manifest:full-path="/"
            manifest:media-type="application/vnd.oasis.opendocument.spreadsheet"/>
    <manifest:file-entry
            manifest:full-path="settings.xml" manifest:media-type="text/xml"/>
    <manifest:file-entry
            manifest:full-path="content.xml" manifest:media-type="text/xml"/>
    <manifest:file-entry
            manifest:full-path="meta.xml" manifest:media-type="text/xml"/>
     <manifest:file-entry
            manifest:full-path="styles.xml" manifest:media-type="text/xml"/>
</manifest:manifest>
"""

meta_xml = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-meta
        xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
        xmlns:xlink="http://www.w3.org/1999/xlink"
        xmlns:dc="http://purl.org/dc/elements/1.1/"
        xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
        xmlns:ooo="http://openoffice.org/2004/office"
        xmlns:grddl="http://www.w3.org/2003/g/data-view#"
        office:version="1.1">
    <office:meta>
        <meta:creation-date>2015-04-30T19:59:53.102483580</meta:creation-date>
        <meta:document-statistic
                meta:table-count="1" meta:cell-count="0"
                meta:object-count="0"/>
        <meta:generator>
            LibreOffice/4.2.8.2$Linux_X86_64 LibreOffice_project/420m0$Build-2
        </meta:generator>
    </office:meta>
</office:document-meta>
"""

styles_xml = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles
        xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
        xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
        xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
        xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
        xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
        xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
        xmlns:xlink="http://www.w3.org/1999/xlink"
        xmlns:dc="http://purl.org/dc/elements/1.1/"
        xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
        xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0"
        xmlns:presentation="urn:oasis:names:tc:opendocument:xmlns:presentation:1.0"
        xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"
        xmlns:chart="urn:oasis:names:tc:opendocument:xmlns:chart:1.0"
        xmlns:dr3d="urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0"
        xmlns:math="http://www.w3.org/1998/Math/MathML"
        xmlns:form="urn:oasis:names:tc:opendocument:xmlns:form:1.0"
        xmlns:script="urn:oasis:names:tc:opendocument:xmlns:script:1.0"
        xmlns:ooo="http://openoffice.org/2004/office"
        xmlns:ooow="http://openoffice.org/2004/writer"
        xmlns:oooc="http://openoffice.org/2004/calc"
        xmlns:dom="http://www.w3.org/2001/xml-events"
        xmlns:rpt="http://openoffice.org/2005/report"
        xmlns:of="urn:oasis:names:tc:opendocument:xmlns:of:1.2"
        xmlns:xhtml="http://www.w3.org/1999/xhtml"
        xmlns:grddl="http://www.w3.org/2003/g/data-view#"
        xmlns:css3t="http://www.w3.org/TR/css3-text/"
        office:version="1.1">
</office:document-styles>"""

settings_xml = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-settings
        xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0">
</office:document-settings>"""
