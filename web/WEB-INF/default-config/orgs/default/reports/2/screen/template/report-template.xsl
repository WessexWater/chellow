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
                    <xsl:value-of select="/source/site/@name" />
                </title>

            </head>
            <body>
                <p>
                    <a href="{/source/request/@context-path}/orgs/1/reports/0/screen/output/">
                        <img
                            src="{/source/request/@context-path}/logo/" />
                        <span class="logo">Chellow</span>
                    </a>
                    &gt;
                    <a
                        href="{/source/request/@context-path}/orgs/1/reports/1/screen/output/">
                        <xsl:value-of select="'Sites'" />
                    </a>
                    &gt;
                    <span id="title">Site:</span>
                    <xsl:value-of select="/source/site/@name" />
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
                        Code:
                        <xsl:value-of select="/source/site/@code" />
                    </li>
                    <li>
                        Name:
                        <xsl:value-of select="/source/site/@name" />
                    </li>
                </ul>

                <table>
                    <caption>Supplies that power this site</caption>
                    <thead>
                    <tr>
                        <th>Id</th>
                        <th>Name</th>
                        <th>From</th>
                        <th>To</th>
                        <th>Source</th>
                        <th>Import MPAN core</th>
                        <th>Export MPAN core</th>
                    </tr>
                    </thead>
                    <tbody>
                    <xsl:for-each select="/source/site/supply[not(supply-generation[1]/hh-end-date[@label='finish'])]">
                        <tr>
                            <td>
                                <a
                                    href="{/source/request/@context-path}/orgs/1/reports/3/screen/output/?supply-id={@id}">
                                    <xsl:value-of select="@id" />
                                </a>
                            </td>
                            <td>
                                <xsl:value-of select="@name" />
                            </td>
                            <td>
                                <xsl:value-of select="concat(supply-generation[last()]/hh-end-date[@label='start']/@year, '-', supply-generation[last()]/hh-end-date[@label='start']/@month, '-', supply-generation[last()]/hh-end-date[@label='start']/@day)"/>
                            </td>
                            <td>
                                Ongoing
                            </td>
                            <td>
                                <xsl:value-of select="source/@code"/>
                            </td>
                            <td>
                                <xsl:if
                                    test="supply-generation/mpan[@label='import']">
                                    <xsl:value-of
                                        select="supply-generation/mpan[@label='import']/mpan-core/@core" />
                                </xsl:if>
                            </td>
                            <td>
                                <xsl:if
                                    test="supply-generation/mpan[@label='export']">
                                    <xsl:value-of
                                        select="supply-generation/mpan[@label='export']/mpan-core/@core" />
                                </xsl:if>
                            </td>
                        </tr>
                    </xsl:for-each>
                    <xsl:if test="/source/site/supply[supply-generation[1]/hh-end-date[@label='finish']]">
                        <xsl:for-each select="/source/site/supply[supply-generation[1]/hh-end-date[@label='finish']]">
                        <tr>
                            <td>
                                <a
                                    href="{/source/request/@context-path}/orgs/1/reports/3/screen/output/?supply-id={@id}">
                                    <xsl:value-of select="@id" />
                                </a>
                            </td>
                            <td>
                                <xsl:value-of select="@name" />
                            </td>
                            <td>
                                <xsl:value-of select="concat(supply-generation[last()]/hh-end-date[@label='start']/@year, '-', supply-generation[last()]/hh-end-date[@label='start']/@month, '-', supply-generation[last()]/hh-end-date[@label='start']/@day)"/>
                            </td>
                            <td>
                                <xsl:value-of select="concat(supply-generation[1]/hh-end-date[@label='finish']/@year, '-', supply-generation[1]/hh-end-date[@label='finish']/@month, '-', supply-generation[1]/hh-end-date[@label='finish']/@day)"/>
                            </td>                            <td>
                                <xsl:value-of select="source/@code"/>
                            </td>
                            <td>
                                <xsl:if
                                    test="supply-generation/mpan[@label='import']">
                                    <xsl:value-of
                                        select="supply-generation/mpan[@label='import']/mpan-core/@core" />
                                </xsl:if>
                            </td>
                            <td>
                                <xsl:if
                                    test="supply-generation/mpan[@label='export']">
                                    <xsl:value-of
                                        select="supply-generation/mpan[@label='export']/mpan-core/@core" />
                                </xsl:if>
                            </td>
                        </tr>
                    </xsl:for-each>
                    </xsl:if>
                    </tbody>
                </table>
                <ul>
                    <li>
                        <a
                            href="{/source/request/@context-path}/orgs/1/reports/4/screen/output/?site-id={/source/site/@id}">
                            <xsl:value-of
                                select="'Graph of site usage'" />
                        </a>
                    </li>
                    <li>
                        <a
                            href="{/source/request/@context-path}/orgs/1/reports/5/screen/output/?site-id={/source/site/@id}">
                            <xsl:value-of select="'Generation Graphs'" />
                        </a>
                    </li>
                    <li>
                        <a
                            href="{/source/request/@context-path}/orgs/1/reports/6/screen/output/?site-id={/source/site/@id}">
                            <xsl:value-of
                                select="'Table of site level monthly kWh, MD kWh etc.'" />
                        </a>
                    </li>
                    <li>
                        <a
                            href="{/source/request/@context-path}/orgs/1/reports/12/screen/output/?site-code={/source/site/@code}&amp;year={/source/date[@label = 'yesterday']/@year}&amp;month={/source/date[@label = 'yesterday']/@month}&amp;day={/source/date[@label='yesterday']/@day}">
                            <xsl:value-of
                                select="'Table of hh data'" />
                        </a>
                    </li>
                    <li>
                        <a
                            href="{/source/request/@context-path}/orgs/1/reports/13/screen/output/?site-id={/source/site/@id}">
                            <xsl:value-of
                                select="'Bulk hh data download'" />
                        </a>
                    </li>
                </ul>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>

