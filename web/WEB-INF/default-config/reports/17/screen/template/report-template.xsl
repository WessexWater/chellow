<?xml version="1.0" encoding="us-ascii"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" encoding="US-ASCII"
        doctype-public="-//W3C//DTD HTML 4.01//EN"
        doctype-system="http://www.w3.org/TR/html4/strict.dtd" indent="yes" />

    <xsl:template match="/">
        <html>
            <head>
                <link rel="stylesheet" type="text/css"
                    href="{/source/request/@context-path}/orgs/1/reports/9/stream/output/" />

                <title>Chellow &gt; DCE Service: <xsl:value-of select="/source/dce-service/@name"/>
</title>

            </head>

            <body>
                <p>
                    <a href="{/source/request/@context-path}/orgs/1/reports/0/screen/output/">
                        <img
                            src="{/source/request/@context-path}/logo/" />
                        <span class="logo">Chellow</span>
                    </a>
                    &gt; DCE Service: <xsl:value-of select="/source/dce-service/@name"/>
                </p>
                <br />
                <xsl:if test="//message">
                    <ul>
                        <xsl:for-each select="//message">

                            <li>
                                <xsl:value-of select="@description" />
                            </li>
                        </xsl:for-each>
                    </ul>
                </xsl:if>
                <ul>
                    <li>
                        <a href="{/source/request/@context-path}/orgs/1/reports/18/screen/output/?dce-service-id={/source/dce-service/@id}">Channel level snags
                        </a>
                    </li>
                </ul>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>