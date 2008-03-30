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
					&gt; Monthly figures
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
						<a href="{/source/request/@context-path}/">
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
					&gt; Monthly figures

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
					<fieldset>
						<legend>Show table</legend>
						<input type="hidden" name="site-id"
							value="{/source/request/parameter[@name='site-id']/value}" />
						<xsl:value-of
							select="'For 12 months finishing at the end of '" />
						<input size="4" length="4"
							name="finish-date-year" value="{/source/@finish-date-year}" />
						<xsl:value-of select="' - '" />
						<select name="finish-date-month">
							<xsl:for-each
								select="/source/month-in-year">
								<option>
									<xsl:if
										test="number(/source/@finish-date-month) = number(@value)">
										<xsl:attribute
											name="selected">selected</xsl:attribute>
									</xsl:if>
									<xsl:value-of select="@value" />
								</option>
							</xsl:for-each>
						</select>
						<xsl:value-of select="' '" />
						<input type="submit" value="Show" />
					</fieldset>
				</form>

				<table>
					<caption>Months</caption>
					<colgroup />
					<colgroup class="gray" span="3" />
					<colgroup span="3" />
					<colgroup class="gray" span="3" />
					<colgroup span="3" />
					<colgroup class="gray" span="3" />
					<colgroup span="3" />
					<tfoot>
						<tr>
							<th>For all months</th>
							<th>
								<xsl:value-of
									select="/source/@max-imported-kw" />
							</th>
							<th>
								<xsl:choose>
									<xsl:when
										test="/source/@max-imported-kw-date">
										<xsl:value-of
											select="/source/@max-imported-kw-date" />
									</xsl:when>
									<xsl:otherwise>NA</xsl:otherwise>
								</xsl:choose>
							</th>
							<th>
								<xsl:value-of
									select="/source/@imported-kwh" />
							</th>
							<th>
								<xsl:value-of
									select="/source/@max-used-kw" />
							</th>
							<th>
								<xsl:choose>
									<xsl:when
										test="/source/@max-used-kw-date">
										<xsl:value-of
											select="/source/@max-used-kw-date" />
									</xsl:when>
									<xsl:otherwise>NA</xsl:otherwise>
								</xsl:choose>
							</th>
							<th>
								<xsl:value-of
									select="/source/@used-kwh" />
							</th>
							<th>
								<xsl:value-of
									select="/source/@max-displaced-kw" />
							</th>
							<th>
								<xsl:choose>
									<xsl:when
										test="/source/@max-displaced-kw-date">
										<xsl:value-of
											select="/source/@max-displaced-kw-date" />
									</xsl:when>
									<xsl:otherwise>NA</xsl:otherwise>
								</xsl:choose>
							</th>
							<th>
								<xsl:value-of
									select="/source/@displaced-kwh" />
							</th>
							<th>
								<xsl:value-of
									select="/source/@max-generated-kw" />
							</th>
							<th>
								<xsl:choose>
									<xsl:when
										test="/source/@max-generated-kw-date">
										<xsl:value-of
											select="/source/@max-generated-kw-date" />
									</xsl:when>
									<xsl:otherwise>NA</xsl:otherwise>
								</xsl:choose>
							</th>
							<th>
								<xsl:value-of
									select="/source/@generated-kwh" />
							</th>
							<th>
								<xsl:value-of
									select="/source/@max-exported-kw" />
							</th>
							<th>
								<xsl:choose>
									<xsl:when
										test="/source/@max-exported-kw-date">
										<xsl:value-of
											select="/source/@max-exported-kw-date" />
									</xsl:when>
									<xsl:otherwise>NA</xsl:otherwise>
								</xsl:choose>
							</th>
							<th>
								<xsl:value-of
									select="/source/@exported-kwh" />
							</th>
							<th>
								<xsl:value-of
									select="/source/@max-parasitic-kw" />
							</th>
							<th>
								<xsl:choose>
									<xsl:when
										test="/source/@max-parasitic-kw-date">
										<xsl:value-of
											select="/source/@max-parasitic-kw-date" />
									</xsl:when>
									<xsl:otherwise>NA</xsl:otherwise>
								</xsl:choose>
							</th>
							<th>
								<xsl:value-of
									select="/source/@parasitic-kwh" />
							</th>
						</tr>
					</tfoot>
					<thead>
						<tr>
							<th rowspan="2">Month</th>
							<th colspan="3">Imported</th>
							<th colspan="3">Used</th>
							<th colspan="3">Displaced</th>
							<th colspan="3">Generated</th>
							<th colspan="3">Exported</th>
							<th colspan="3">Parasitic</th>
						</tr>
						<tr>
							<th>MD / kW</th>
							<th>Date of MD</th>
							<th>kWh</th>
							<th>MD / kW</th>
							<th>Date of MD</th>
							<th>kWh</th>
							<th>MD / kW</th>
							<th>Date of MD</th>
							<th>kWh</th>
							<th>MD / kW</th>
							<th>Date of MD</th>
							<th>kWh</th>
							<th>MD / kW</th>
							<th>Date of MD</th>
							<th>kWh</th>
							<th>MD / kW</th>
							<th>Date of MD</th>
							<th>kWh</th>
							<th>Data quality</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each select="/source/month">
							<tr>
								<xsl:if test="@has-site-snags">
									<xsl:attribute name="class">
                                        <xsl:value-of select="'error'" />
                                    </xsl:attribute>
								</xsl:if>
								<td>
									<xsl:value-of
										select="concat(hh-end-date[@label='start']/@year, '-', hh-end-date[@label='start']/@month)" />
								</td>
								<td>
									<xsl:value-of
										select="@max-imported-kw" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when
											test="@max-imported-kw-date">
											<xsl:value-of
												select="@max-imported-kw-date" />
										</xsl:when>
										<xsl:otherwise>
											NA
										</xsl:otherwise>
									</xsl:choose>
								</td>
								<td>
									<xsl:value-of
										select="@imported-kwh" />
								</td>
								<td>
									<xsl:value-of select="@max-used-kw" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when
											test="@max-used-kw-date">
											<xsl:value-of
												select="@max-used-kw-date" />
										</xsl:when>
										<xsl:otherwise>
											NA
										</xsl:otherwise>
									</xsl:choose>
								</td>
								<td>
									<xsl:value-of select="@used-kwh" />
								</td>
								<td>
									<xsl:value-of
										select="@max-displaced-kw" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when
											test="@max-displaced-kw-date">
											<xsl:value-of
												select="@max-displaced-kw-date" />
										</xsl:when>
										<xsl:otherwise>
											NA
										</xsl:otherwise>
									</xsl:choose>
								</td>
								<td>
									<xsl:value-of
										select="@displaced-kwh" />
								</td>
								<td>
									<xsl:value-of
										select="@max-generated-kw" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when
											test="@max-generated-kw-date">
											<xsl:value-of
												select="@max-generated-kw-date" />
										</xsl:when>
										<xsl:otherwise>
											NA
										</xsl:otherwise>
									</xsl:choose>
								</td>
								<td>
									<xsl:value-of
										select="@generated-kwh" />
								</td>
								<td>
									<xsl:value-of
										select="@max-exported-kw" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when
											test="@max-exported-kw-date">
											<xsl:value-of
												select="@max-exported-kw-date" />
										</xsl:when>
										<xsl:otherwise>
											NA
										</xsl:otherwise>
									</xsl:choose>
								</td>
								<td>
									<xsl:value-of
										select="@exported-kwh" />
								</td>
								<td>
									<xsl:value-of
										select="@max-parasitic-kw" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when
											test="@max-parasitic-kw-date">
											<xsl:value-of
												select="@max-parasitic-kw-date" />
										</xsl:when>
										<xsl:otherwise>
											NA
										</xsl:otherwise>
									</xsl:choose>
								</td>
								<td>
									<xsl:value-of
										select="@parasitic-kwh" />
								</td>
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
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

