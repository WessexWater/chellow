<?xml version="1.0" encoding="us-ascii"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="xml" encoding="US-ASCII"
        doctype-public="-//W3C//DTD XHTML 1.1//EN"
        doctype-system="http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd" indent="yes" />

    <xsl:template match="/">
        <html>
             <head>
        <link rel="stylesheet" type="text/css"
            href="{/source/request/@context-path}/orgs/1/reports/9/stream/output/" />

                <title>
                    Chellow &gt; Sites &gt; Supply:
                    <xsl:value-of select="/source/supply/@name" />
                    &gt; Hh data
                </title>

            </head>
            <body>
                <p>
                    <a href="{/source/request/@context-path}/">
                        <img src="{/source/request/@context-path}/logo/"
                            alt="Chellow logo" />
                        <span class="logo">Chellow</span>
                    </a>
                    &gt;
                    <a
                        href="{/source/request/@context-path}/orgs/1/reports/1/screen/output/">
                        <xsl:value-of select="'Sites'" />
                    </a>
                    &gt; <a href="{/source/request/@context-path}/orgs/1/reports/3/screen/output/?supply-id={/source/supply/@id}">Supply:
                    <xsl:value-of select="/source/supply/@name" /></a>
                    &gt; <span id="title">Hh data</span>

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

                <h3>Supply details</h3>
                
                <ul>
                <li>Name: <xsl:value-of select="/source/supply/@name"/></li>
                <li>Import MPAN core: <xsl:value-of select="/source/supply/supply-generation/mpan[@label='import']/mpan-core/@core"/></li>
                <li>Export MPAN core: <xsl:value-of select="/source/supply/supply-generation/mpan[@label='export']/mpan-core/@core"/></li>
                <li>Source Code: <xsl:value-of select="/source/supply/source/@code"/></li>
                </ul>

                <form action=".">
                    <fieldset><legend>Show hh data</legend>
                    <input type="hidden" name="supply-id" value="{/source/supply/@id}"/>
                    <br/>
                    <fieldset><legend>Month</legend>
                    <input name="start-year" value="{/source/request/parameter[@name='start-year']/value}" size="4" maxlength="4" /><xsl:value-of select="' - '"/>
                        <select name="start-month">
                            <xsl:for-each select="/source/months/month">
                                <option value="{@number}">
                                    <xsl:if test="@number=/source/request/parameter[@name='start-month']/value">
                                        <xsl:attribute name="selected">selected</xsl:attribute>
                                    </xsl:if>
                                    <xsl:value-of select="@number"/>
                                </option>
                            </xsl:for-each>
                        </select>
                    </fieldset>
                    <br/>
                    <input type="submit" value="Show"/>
                    </fieldset>
                </form>
                <table><caption>Hh Data</caption>
                <thead>
                  <tr>
                    <th rowspan="3">Timestamp</th>
                    <th colspan="4">Import</th>
                    <th colspan="4">Export</th>
                  </tr>
                  <tr>
                    <th colspan="2">kWh</th>
                    <th colspan="2">kVArh</th>
                    <th colspan="2">kWh</th>
                    <th colspan="2">kVArh</th>
                  </tr>
                  <tr>
                    <th>Value</th>
                    <th>Status</th>
                    <th>Value</th>
                    <th>Status</th>
                    <th>Value</th>
                    <th>Status</th>
                    <th>Value</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <xsl:for-each select="/source/supply/datum">
                    <tr>
                      <td><xsl:value-of select="@timestamp"/></td>
                      <td><xsl:value-of select="@import-kwh-value"/></td>
                      <td><xsl:value-of select="@import-kwh-status"/></td>
                      <td><xsl:value-of select="@import-kvarh-value"/></td>
                      <td><xsl:value-of select="@import-kvarh-status"/></td>
                      <td><xsl:value-of select="@export-kwh-value"/></td>
                      <td><xsl:value-of select="@export-kwh-status"/></td>
                      <td><xsl:value-of select="@export-kvarh-value"/></td>
                      <td><xsl:value-of select="@export-kvarh-status"/></td>
                    </tr>
                  </xsl:for-each>
                </tbody>
                </table>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>