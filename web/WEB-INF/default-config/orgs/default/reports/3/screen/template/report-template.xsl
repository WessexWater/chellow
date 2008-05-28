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
					href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/9/stream/output/" />

				<title>
					<xsl:value-of select="/source/org/@name" />
					&gt; Supplies &gt;
					<xsl:value-of select="/source/supply/@id" />
				</title>

			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/0/screen/output/">
						<xsl:value-of select="/source/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/49/screen/output/">
						<xsl:value-of select="'Supplies'" />
					</a>
					&gt;
					<xsl:value-of
						select="concat(/source/supply/@id, ' [')" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/supplies/{/source/supply/@id}/">
						<xsl:value-of select="'edit'" />
					</a>
					<xsl:value-of select="']'" />
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
									<xsl:value-of
										select="concat(mpan[mpan-top/llf/@is-import='true']/mpan-top/profile-class/@code, ' ', mpan[mpan-top/llf/@is-import='true']/mpan-top/meter-timeswitch/@code, ' ', mpan[mpan-top/llf/@is-import='true']/llf/@code, ' ', mpan[mpan-top/llf/@is-import='true']/mpan-core/@core)" />
								</td>
								<td>
									<xsl:value-of
										select="mpan[mpan-top/llf/@is-import='true']/@agreed-supply-capacity" />
								</td>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/41/screen/output/?account-id={mpan[mpan-top/llf/@is-import='true']/account/@id}">
										<xsl:value-of
											select="mpan[mpan-top/llf/@is-import='true']/account[@label='supplier']/@reference" />
									</a>
								</td>
								<td>
									<xsl:value-of
										select="concat(mpan[mpan-top/llf/@is-import='false']/profile-class/@code, ' ', mpan[mpan-top/llf/@is-import='false']/meter-timeswitch/@code, ' ', mpan[mpan-top/llf/@is-import='false']/llf/@code, ' ', mpan[mpan-top/llf/@is-import='false']/mpan-core/@core)" />
								</td>
								<td>
									<xsl:value-of
										select="mpan[mpan-top/llf/@is-import='false']/@agreed-supply-capacity" />
								</td>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/41/screen/output/?account-id={mpan[mpan-top/llf/@is-import='false']/account/@id}">
										<xsl:value-of
											select="mpan[mpan-top/llf/@is-import='false']/account[@label='supplier']/@reference" />
									</a>
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

