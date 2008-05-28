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
					<xsl:value-of
						select="/source/supply-generation/supply/@name" />
					&gt; Generation:
					<xsl:value-of
						select="/source/supply-generation/@id" />
				</title>
			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/{/source/supply-generation/supply/org/@id}/reports/0/screen/output/">
						<xsl:value-of select="/source/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/49/screen/output/">
						<xsl:value-of select="'Supplies'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/1/reports/3/screen/output/?supply-id={/source/supply-generation/supply/@id}">
						<xsl:value-of
							select="/source/supply-generation/supply/@id" />
					</a>
					&gt;
					<xsl:value-of
						select="concat('Generation: ', /source/supply-generation/@id, ' [')" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/supplies/{/source/supply-generation/supply/@id}/generations/{/source/supply-generation/@id}/">
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
				<table>
					<caption>
						Sites powered by this supply generation
					</caption>
					<thead>
						<tr>
							<th>Code</th>
							<th>Name</th>
							<xsl:if
								test="count(/source/supply-generation/site-supply-generation) &gt; 1">
								<th></th>
							</xsl:if>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each
							select="/source/supply-generation/site-supply-generation">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/1/reports/2/screen/output/?site-id={site/@id}">
										<xsl:value-of
											select="site/@code" />
									</a>
								</td>
								<td>
									<xsl:value-of select="site/@name" />
								</td>
								<xsl:if
									test="count(/source/supply-generation/site-supply-generation) &gt; 1">
									<td>
										<xsl:if
											test="@is-physical='true'">
											Located here
										</xsl:if>
									</td>
								</xsl:if>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
				<h3>Supply</h3>
				<ul>
					<li>
						<xsl:value-of select="'Supply Name: '" />
						<a
							href="{/source/request/@context-path}/orgs/1/reports/3/screen/output/?supply-id={/source/supply-generation/supply/@id}">
							<xsl:value-of
								select="/source/supply-generation/supply/@name" />
						</a>
					</li>
					<li>
						<xsl:value-of
							select="concat('Source: ', /source/supply-generation/supply/source/@code, ' - ', /source/supply-generation/supply/source/@name)" />
					</li>
				</ul>
				<h3>Generation</h3>

				<ul>
					<li>
						From:
						<xsl:value-of
							select="concat(/source/supply-generation/hh-end-date[@label='start']/@year, '-', /source/supply-generation/hh-end-date[@label='start']/@month, '-', /source/supply-generation/hh-end-date[@label='start']/@day)" />
					</li>
					<li>
						To:
						<xsl:choose>
							<xsl:when
								test="/source/supply-generation/hh-end-date[@label='finish']">
								<xsl:value-of
									select="concat(/source/supply-generation/hh-end-date[@label='finish']/@year, '-', /source/supply-generation/hh-end-date[@label='finish']/@month, '-', /source/supply-generation/hh-end-date[@label='finish']/@day)" />
							</xsl:when>
							<xsl:otherwise>Ongoing</xsl:otherwise>
						</xsl:choose>
					</li>
				</ul>

				<table>
					<caption>MPANs</caption>
					<thead>
						<tr>
							<th></th>
							<th>Import</th>
							<th>Export</th>
						</tr>
					</thead>
					<tbody>
						<tr>
							<th>Profile Class</th>
							<td>
								<xsl:value-of
									select="concat(/source/supply-generation/mpan[mpan-top/llf/@is-import='true']/mpan-top/profile-class/@code, ' - ', /source/supply-generation/mpan[mpan-top/llf/@is-import='true']/mpan-top/profile-class/@description)" />
							</td>
							<td>
								<xsl:value-of
									select="concat(/source/supply-generation/mpan[mpan-top/llf/@is-import='false']/mpan-top/profile-class/@code, ' - ', /source/supply-generation/mpan[mpan-top/llf/@is-import='false']/mpan-top/profile-class/@description)" />
							</td>
						</tr>
						<tr>
							<th>Meter Timeswitch Code</th>
							<td>
								<xsl:value-of
									select="concat(/source/supply-generation/mpan[mpan-top/llf/@is-import='true']/mpan-top/meter-timeswitch/@code, ' - ', /source/supply-generation/mpan[mpan-top/llf/@is-import='true']/mpan-top/meter-timeswitch/@description)" />
							</td>
							<td>
								<xsl:value-of
									select="concat(/source/supply-generation/mpan[mpan-top/llf/@is-import='false']/mpan-top/meter-timeswitch/@code, ' - ', /source/supply-generation/mpan[mpan-top/llf/@is-import='false']/mpan-top/meter-timeswitch/@description)" />
							</td>
						</tr>
						<tr>
							<th>Line Loss Factor</th>
							<td>
								<xsl:value-of
									select="concat(/source/supply-generation/mpan[mpan-top/llf/@is-import='true']/mpan-top/llf/@code, ' - ', /source/supply-generation/mpan[mpan-top/llf/@is-import='true']/mpan-top/llf/@description)" />
							</td>
							<td>
								<xsl:value-of
									select="concat(/source/supply-generation/mpan[mpan-top/llf/@is-import='false']/mpan-top/llf/@code, ' - ', /source/supply-generation/mpan[mpan-top/llf/@is-import='false']/mpan-top/llf/@description)" />
							</td>
						</tr>
						<tr>
							<th>MPAN Core</th>
							<td>
								<xsl:value-of
									select="/source/supply-generation/mpan[mpan-top/llf/@is-import='true']/mpan-core/@core" />
							</td>
							<td>
								<xsl:value-of
									select="/source/supply-generation/mpan[mpan-top/llf/@is-import='false']/mpan-core/@core" />
							</td>
						</tr>
						<tr>
							<th>Agreed Supply Capacity</th>
							<td>
								<xsl:value-of
									select="/source/supply-generation/mpan[mpan-top/llf/@is-import='true']/@agreed-supply-capacity" />
							</td>
							<td>
								<xsl:value-of
									select="/source/supply-generation/mpan[mpan-top/llf/@is-import='false']/@agreed-supply-capacity" />
							</td>
						</tr>
						<tr>
							<th>Channels</th>
							<td>
								<ul>
									<xsl:if
										test="/source/supply-generation/mpan[mpan-top/llf/@is-import='true']/@has-import-kwh='true'">
										<li>Import kWh</li>
									</xsl:if>
									<xsl:if
										test="/source/supply-generation/mpan[mpan-top/llf/@is-import='true']/@has-import-kvarh='true'">
										<li>Import kVArh</li>
									</xsl:if>
									<xsl:if
										test="/source/supply-generation/mpan[mpan-top/llf/@is-import='true']/@has-export-kwh='true'">
										<li>Export kWh</li>
									</xsl:if>
									<xsl:if
										test="/source/supply-generation/mpan[mpan-top/llf/@is-import='true']/@has-export-kvarh='true'">
										<li>Export kVArh</li>
									</xsl:if>
								</ul>
							</td>
							<td>
								<ul>
									<xsl:if
										test="/source/supply-generation/mpan[mpan-top/llf/@is-import='false']/@has-import-kwh='true'">
										<li>Import kWh</li>
									</xsl:if>
									<xsl:if
										test="/source/supply-generation/mpan[mpan-top/llf/@is-import='false']/@has-import-kvarh='true'">
										<li>Import kVArh</li>
									</xsl:if>
									<xsl:if
										test="/source/supply-generation/mpan[mpan-top/llf/@is-import='false']/@has-export-kwh='true'">
										<li>Export kWh</li>
									</xsl:if>
									<xsl:if
										test="/source/supply-generation/mpan[mpan-top/llf/@is-import='false']/@has-export-kvarh='true'">
										<li>Export kVArh</li>
									</xsl:if>
								</ul>
							</td>
						</tr>
						<tr>
							<th>DCE</th>
							<td>
								<xsl:value-of
									select="/source/supply-generation/mpan[mpan-top/llf/@is-import='true']/dce-service/dce/@name" />
							</td>
							<td>
								<xsl:value-of
									select="/source/supply-generation/mpan[mpan-top/llf/@is-import='false']/dce-service/dce/@name" />
							</td>
						</tr>
						<tr>
							<th>DCE Service</th>
							<td>
								<xsl:value-of
									select="/source/supply-generation/mpan[mpan-top/llf/@is-import='true']/dce-service/@name" />
							</td>
							<td>
								<xsl:value-of
									select="/source/supply-generation/mpan[mpan-top/llf/@is-import='false']/dce-service/@name" />
							</td>
						</tr>
						<tr>
							<th>Supplier</th>
							<td>
								<a
									href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/36/screen/output/?supplier-id={/source/supply-generation/mpan[mpan-top/llf/@is-import='true']/supplier-service/supplier/@id}">

									<xsl:value-of
										select="/source/supply-generation/mpan[mpan-top/llf/@is-import='true']/supplier-service/supplier/@name" />
								</a>
							</td>
							<td>
								<a
									href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/36/screen/output/?supplier-id={/source/supply-generation/mpan[mpan-top/llf/@is-import='false']/supplier-service/supplier/@id}">

									<xsl:value-of
										select="/source/supply-generation/mpan[mpan-top/llf/@is-import='false']/supplier-service/supplier/@name" />
								</a>
							</td>
						</tr>
						<tr>
							<th>Supplier Service</th>
							<td>
								<a
									href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/38/screen/output/?supplier-service-id={/source/supply-generation/mpan[mpan-top/llf/@is-import='true']/supplier-service/@id}">

									<xsl:value-of
										select="/source/supply-generation/mpan[mpan-top/llf/@is-import='true']/supplier-service/@name" />
								</a>
							</td>
							<td>
								<a
									href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/38/screen/output/?supplier-service-id={/source/supply-generation/mpan[mpan-top/llf/@is-import='false']/supplier-service/@id}">
									<xsl:value-of
										select="/source/supply-generation/mpan[mpan-top/llf/@is-import='false']/supplier-service/@name" />
								</a>
							</td>
						</tr>
						<tr>
							<th>Supplier Account</th>
							<td>
								<a
									href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/41/screen/output/?account-id={/source/supply-generation/mpan[mpan-top/llf/@is-import='true']/account[@label='supplier']/@id}">
									<xsl:value-of
										select="/source/supply-generation/mpan[mpan-top/llf/@is-import='true']/account[@label='supplier']/@reference" />
								</a>
							</td>
							<td>
								<a
									href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/41/screen/output/?account-id={/source/supply-generation/mpan[mpan-top/llf/@is-import='false']/account[@label='supplier']/@id}">
									<xsl:value-of
										select="/source/supply-generation/mpan[mpan-top/llf/@is-import='false']/account[@label='supplier']/@reference" />
								</a>
							</td>
						</tr>
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>