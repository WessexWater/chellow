<?xml version="1.0" encoding="us-ascii"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="xml" encoding="US-ASCII"
        doctype-public="-//W3C//DTD XHTML 1.1//EN"
        doctype-system="http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd"
        indent="yes" />
    <xsl:template match="/">
        <html>
            <head>
                <link rel="stylesheet" type="text/css"
                    href="{/source/request/@context-path}/style/" />

                <title>Chellow &gt; EDF virtual bill</title>

            </head>
            <body>
                 This is where the data will be output in the finished report
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>

