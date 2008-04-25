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

				<title>
					<xsl:value-of select="/source/org/@name" />
					&gt; Sites &gt; Supply:
					<xsl:value-of select="/source/supply/@name" />
				</title>

			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/1/reports/0/screen/output/">
						<xsl:value-of select="/source/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/1/reports/1/screen/output/">
						<xsl:value-of select="'Sites'" />
					</a>
					&gt;
					<span id="title">
						Supply:
						<xsl:value-of select="/source/supply/@name" />
					</span>
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
				<ul>
					<li>
						<xsl:value-of
							select="concat('Name: ', /source/supply/@name)" />
					</li>
					<li>
						<xsl:value-of
							select="concat('Source: ', /source/supply/source/@code, ' - ', /source/supply/source/@name)" />
					</li>
				</ul>

				<table>
					<caption>Generations</caption>
					<thead>
						<tr>
							<th rowspan="2">Id</th>
							<th rowspan="2">From</th>
							<th rowspan="2">To</th>
							<th colspan="3">Import</th>
							<th colspan="3">Export</th>
						</tr>
						<tr>
							<th>MPAN</th>
							<th>kVA</th>
							<th>Supplier Account</th>
							<th>MPAN</th>
							<th>kVA</th>
							<th>Supplier Account</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each
							select="/source/supply/supply-generation">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/1/reports/15/screen/output/?supply-generation-id={@id}">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<xsl:value-of
										select="concat(hh-end-date[@label='start']/@year, '-', hh-end-date[@label='start']/@month, '-', hh-end-date[@label='start']/@day)" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when
											test="hh-end-date[@label='finish']">
											<xsl:value-of
												select="concat(hh-end-date[@label='finish']/@year, '-', hh-end-date[@label='finish']/@month, '-', hh-end-date[@label='finish']/@day)" />
										</xsl:when>
										<xsl:otherwise>
											Ongoing
										</xsl:otherwise>
									</xsl:choose>
								</td>
								<td>
									<xsl:if
										test="mpan[@label='import']">
										<xsl:value-of
											select="concat(mpan[@label='import']/line-loss-factor/profile-class/@code, ' ', mpan[@label='import']/meter-timeswitch/@code, ' ', mpan[@label='import']/line-loss-factor/@code, ' ', mpan[@label='import']/mpan-core/@core)" />
									</xsl:if>
								</td>
								<td>
									<xsl:if
										test="mpan[@label='import']">
										<xsl:value-of
											select="mpan[@label='import']/@agreed-supply-capacity" />
									</xsl:if>
								</td>
								<td>
									<xsl:if
										test="mpan[@label='import']">
										<a
											href="{/source/request/@context-path}/orgs/1/reports/21/screen/output/?account-id={mpan[@label='import']/account/@id}">
											<xsl:value-of
												select="mpan[@label='import']/account/@reference" />
										</a>
									</xsl:if>
								</td>
								<td>
									<xsl:if
										test="mpan[@label='export']">
										<xsl:value-of
											select="concat(mpan[@label='export']/line-loss-factor/profile-class/@code, ' ', mpan[@label='export']/meter-timeswitch/@code, ' ', mpan[@label='export']/line-loss-factor/@code, ' ', mpan[@label='export']/mpan-core/@core)" />
									</xsl:if>
								</td>
								<td>
									<xsl:if
										test="mpan[@label='export']">
										<xsl:value-of
											select="mpan[@label='export']/@agreed-supply-capacity" />
									</xsl:if>
								</td>
								<td>
									<xsl:if
										test="mpan[@label='export']">
										<a
											href="{/source/request/@context-path}/orgs/1/reports/21/screen/output/?account-id={mpan[@label='import']/account/@id}">
											<xsl:value-of
												select="mpan[@label='export']/account/@reference" />
										</a>
									</xsl:if>
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>

				<ul>
					<li>
						kWh, kVA, MD etc. by month:
						<a
							href="{/source/request/@context-path}/orgs/1/reports/7/screen/output/?supply-id={/source/supply/@id}&amp;is-import=true">
							<xsl:value-of select="'Import'" />
						</a>
						<xsl:value-of select="' '" />
						<a
							href="{/source/request/@context-path}/orgs/1/reports/7/screen/output/?supply-id={/source/supply/@id}&amp;is-import=false">
							<xsl:value-of select="'Export'" />
						</a>

					</li>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/1/reports/8/screen/output/?supply-id={/source/supply/@id}&amp;start-year={/source/date/@year}&amp;start-month={/source/date/@month}">
							Raw HH data
						</a>
					</li>
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

