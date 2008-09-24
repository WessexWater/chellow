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
            <body><ul>
                 <xsl:for-each select="/source/supply">
<li>
<xsl:value-of select="concat(site-supply/site/@code, ';', site-supply/site/@name, ';', supply-generation/mpan/line-loss-factor/VoltageLevel/@code)"/>
</li>
                 </xsl:for-each>
</ul>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>

