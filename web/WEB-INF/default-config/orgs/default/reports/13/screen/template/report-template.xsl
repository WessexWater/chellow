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
                    href="{/source/request/@context-path}/orgs/1/reports/9/stream/output/" />

                <title>
                    Chellow &gt; Sites &gt;
                    <xsl:value-of
                        select="concat(/source/site/@code, ' ', /source/site/@name)" />
                    &gt; HH data selector
                </title>
                <style>
                    <![CDATA[
                colgroup.gray {
                    background: silver;
                }

                tr.error {
                    color: red;
                }
                ]]>
                </style>
            </head>

            <body>
                <p>
                    <span class="logo">
                        <a href="{/source/request/@context-path}/orgs/1/reports/0/stream/output/">
                            <img
                                src="{/source/request/@context-path}/logo/" alt="Chellow logo" />
                            <xsl:value-of select="'Chellow'" />
                        </a>
                    </span>
                    &gt;
                    <a
                        href="{/source/request/@context-path}/orgs/1/reports/1/screen/output/">
                        <xsl:value-of select="'Sites'" />
                    </a>
                    &gt;
                    <a
                        href="{/source/request/@context-path}/orgs/1/reports/2/screen/output/?site-id={/source/site/@id}">
                        <xsl:value-of
                            select="concat(/source/site/@code, ' ', /source/site/@name)" />
                    </a>
                    &gt; HH data selector
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
                <form action="{/source/request/@context-path}/orgs/1/reports/14/stream/output/">
                  <fieldset><legend>Download HH data</legend>
                    <input type="hidden" name="site-id" value="{/source/site/@id}"/>
                    <br/>
                    <label>
                      <xsl:value-of select="'Type '"/>
                      <select name="type">
                        <option value="used">Used</option>
                        <option value="imported">Imported</option>
                        <option value="exported">Exported</option>
                        <option value="generated">Generated</option>
                        <option value="displaced">Displaced</option>
                        <option value="parasitic">Parasitic</option>
                      </select>
                    </label>
                    <br/>
                    <br/>
                    <label><xsl:value-of select="'Year '"/>
                      <input size="4" length="4" name="year" value="{/source/date/@year}"/></label>
                    <br/>
                    <br/>
                    <input type="submit" value="Download"/>
                  </fieldset>
                </form>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>

