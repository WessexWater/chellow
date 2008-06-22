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
                    href="{/source/request/@context-path}/orgs/{/source/site/org/@id}/reports/9/stream/output/" />

                <title>
                    <xsl:value-of select="/source/site/org/@name"/> &gt; Sites &gt;
                    <xsl:value-of
                        select="concat(/source/site/@code, ' ', /source/site/@name)" />
                    &gt; HH data
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
                        <a href="{/source/request/@context-path}/orgs/{/source/site/org/@id}/reports/0/screen/output/">
                             <xsl:value-of select="/source/site/org/@name" />
                        </a>
                    &gt;
                    <a
                        href="{/source/request/@context-path}/orgs/{/source/site/org/@id}/reports/1/screen/output/">
                        <xsl:value-of select="'Sites'" />
                    </a>
                    &gt;
                    <a
                        href="{/source/request/@context-path}/orgs/{/source/site/org/@id}/reports/2/screen/output/?site-id={/source/site/@id}">
                        <xsl:value-of
                            select="concat(/source/site/@code, ' ', /source/site/@name)" />
                    </a>
                    &gt; HH data

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
                <form action=".">
                  <fieldset><legend>Show data</legend>
                    <br/>
                    <label>
                      <xsl:value-of select="'Site Code '"/><input name="site-code" value="{/source/request/parameter[@name='site-code']/value}"/>
                    </label>
                    <br/>
                    <br/>
                    <fieldset>
                      <legend>Date</legend>
                      <br/>
                      <input size="4" length="4" name="year" value="{/source/hh/hh-end-date/@year}"/><xsl:value-of select="' - '"/>
                      <select name="month">
                        <xsl:for-each select="/source/months/month">
                          <option>
                            <xsl:if test="number(/source/hh/hh-end-date/@month) = number(@number)">
                              <xsl:attribute name="selected">selected</xsl:attribute>
                            </xsl:if>
                            <xsl:value-of select="@number"/>
                          </option>
                        </xsl:for-each>
                      </select><xsl:value-of select="' - '"/>
                     <select name="day">
                        <xsl:for-each select="/source/days/day">
                          <option>
                            <xsl:if test="number(/source/hh/hh-end-date/@day) = number(@number)">
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

                <table>
                    <caption>HH Data</caption>
                    <colgroup />
                    <colgroup class="gray" />
                    <colgroup />
                    <colgroup class="gray" />
                    <colgroup />
                    <colgroup class="gray" />
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Imported</th>
                            <th>Used</th>
                            <th>Displaced</th>
                            <th>Generated</th>
                            <th>Exported</th>
                            <th>Parasitic</th>
                        </tr>
                    </thead>
                    <tbody>
                        <xsl:for-each select="/source/hh">
                            <tr>
                                <xsl:if test="@has-site-snags">
                                    <xsl:attribute name="class">
                                        <xsl:value-of select="'error'" />
                                    </xsl:attribute>
                                </xsl:if>
                                <td>
                                    <xsl:value-of
                                        select="concat(hh-end-date/@year, '-', hh-end-date/@month, '-', hh-end-date/@day, ' ', hh-end-date/@hour, ':', hh-end-date/@minute, 'Z')" />
                                </td>
                                <td>
                                    <xsl:value-of
                                        select="@imported-kwh" />
                                </td>
                                <td>
                                    <xsl:value-of select="@used-kwh" />
                                </td>
                                <td>
                                    <xsl:value-of
                                        select="@displaced-kwh" />
                                </td>
                                <td>
                                    <xsl:value-of
                                        select="@generated-kwh" />
                                </td>
                                <td>
                                    <xsl:value-of
                                        select="@exported-kwh" />
                                </td>
                                <td>
                                    <xsl:value-of
                                        select="@parasitic-kwh" />
                                </td>
<!--
                                <td>
                                    <xsl:if
                                        test="@has-site-snags = 'true'">
                                        See
                                        <a
                                            href="{/source/request/@context-path}/orgs/1/reports/5/screen/output/?site-id={/source/site/@id}&amp;months=1&amp;finish-date-year={hh-end-date[@label='start']/@year}&amp;finish-date-month={hh-end-date[@label='start']/@month}">
                                            generation graph
                                        </a>
                                        for errors.
                                    </xsl:if>
                                </td>
-->
                            </tr>
                        </xsl:for-each>
                    </tbody>
                </table>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>

