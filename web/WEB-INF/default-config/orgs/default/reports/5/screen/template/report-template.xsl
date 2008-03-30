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

                <title>
                    Chellow &gt; Sites &gt;
                    <xsl:value-of select="/source/site/@name" />
                </title>

            </head>

            <body>
                <p>
                    <a href="{/source/request/@context-path}/">
                        <span class="logo">Chellow</span>
                    </a>
                    &gt;
                    <a
                        href="{/source/request/@context-path}/orgs/1/reports/1/screen/output/">
                        <xsl:value-of select="'Sites'"/>
                    </a>
                    &gt;
                    <a
                        href="{/source/request/@context-path}/orgs/1/reports/2/screen/output/?site-id={/source/site/@id}">
                    <xsl:value-of select="/source/site/@name" />
                    </a>
                    &gt;
                    HH graph of generation
                </p>
                <xsl:if test="//message">
                    <ul>


                        <xsl:for-each select="//message">

                            <li>
                                <xsl:value-of select="@description" />
                            </li>
                        </xsl:for-each>
                    </ul>
                </xsl:if>

                <p><img src="{/source/request/@context-path}/orgs/1/reports/11/stream/output/?site-id={/source/site/@id}&amp;finish-date-year={/source/@finish-date-year}&amp;finish-date-month={/source/@finish-date-month}&amp;months={/source/@months}"/></p>
                <form action=".">
                  <fieldset><legend>Show graph</legend>
                    <input type="hidden" name="site-id" value="{/source/request/parameter[@name='site-id']/value}"/>
                    <xsl:value-of select="'For '"/>
                    <select name="months">
                      <xsl:for-each select="/source/month">
                        <option>
                          <xsl:if test="/source/@months = @value">
                            <xsl:attribute name="selected">selected</xsl:attribute>
                          </xsl:if>
                          <xsl:value-of select="@value"/>
                        </option>
                      </xsl:for-each>
                    </select>
                    <xsl:value-of select="' months finishing in '"/>
                    <input size="4" length="4" name="finish-date-year" value="{/source/@finish-date-year}"/><xsl:value-of select="' - '"/>
                    <select name="finish-date-month">
                      <xsl:for-each select="/source/month">
                        <option>
                          <xsl:if test="number(/source/@finish-date-month) = number(@value)">
                            <xsl:attribute name="selected">selected</xsl:attribute>
                          </xsl:if>
                          <xsl:value-of select="@value"/>
                        </option>
                      </xsl:for-each>
                    </select><xsl:value-of select="' '"/>
                    <input type="submit" value="Show"/>
                  </fieldset>
                </form>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>

