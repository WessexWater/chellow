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
									select="concat(/source/supply-generation/mpan[mpan-top/llfc/@is-import='true']/mpan-top/pc/@code, ' - ', /source/supply-generation/mpan[mpan-top/llfc/@is-import='true']/mpan-top/pc/@description)" />
							</td>
							<td>
								<xsl:value-of
									select="concat(/source/supply-generation/mpan[mpan-top/llfc/@is-import='false']/mpan-top/pc/@code, ' - ', /source/supply-generation/mpan[mpan-top/llfc/@is-import='false']/mpan-top/pc/@description)" />
							</td>
						</tr>
						<tr>
							<th>Meter Timeswitch Code</th>
							<td>
								<xsl:value-of
									select="concat(/source/supply-generation/mpan[mpan-top/llfc/@is-import='true']/mpan-top/mtc/@code, ' - ', /source/supply-generation/mpan[mpan-top/llfc/@is-import='true']/mpan-top/mtc/@description)" />
							</td>
							<td>
								<xsl:value-of
									select="concat(/source/supply-generation/mpan[mpan-top/llfc/@is-import='false']/mpan-top/mtc/@code, ' - ', /source/supply-generation/mpan[mpan-top/llfc/@is-import='false']/mpan-top/mtc/@description)" />
							</td>
						</tr>
						<tr>
							<th>Line Loss Factor Code</th>
							<td>
								<xsl:value-of
									select="concat(/source/supply-generation/mpan[mpan-top/llfc/@is-import='true']/mpan-top/llfc/@code, ' - ', /source/supply-generation/mpan[mpan-top/llfc/@is-import='true']/mpan-top/llfc/@description)" />
							</td>
							<td>
								<xsl:value-of
									select="concat(/source/supply-generation/mpan[mpan-top/llfc/@is-import='false']/mpan-top/llfc/@code, ' - ', /source/supply-generation/mpan[mpan-top/llfc/@is-import='false']/mpan-top/llfc/@description)" />
							</td>
						</tr>
						<tr>
							<th>MPAN Core</th>
							<td>
								<xsl:value-of
									select="/source/supply-generation/mpan[mpan-top/llfc/@is-import='true']/mpan-core/@core" />
							</td>
							<td>
								<xsl:value-of
									select="/source/supply-generation/mpan[mpan-top/llfc/@is-import='false']/mpan-core/@core" />
							</td>
						</tr>
						<tr>
							<th>Agreed Supply Capacity</th>
							<td>
								<xsl:value-of
									select="/source/supply-generation/mpan[mpan-top/llfc/@is-import='true']/@agreed-supply-capacity" />
							</td>
							<td>
								<xsl:value-of
									select="/source/supply-generation/mpan[mpan-top/llfc/@is-import='false']/@agreed-supply-capacity" />
							</td>
						</tr>
						<tr>
							<th>Channels</th>
							<td>
								<ul>
									<xsl:if
										test="/source/supply-generation/mpan[mpan-top/llfc/@is-import='true']/@has-import-kwh='true'">
										<li>Import kWh</li>
									</xsl:if>
									<xsl:if
										test="/source/supply-generation/mpan[mpan-top/llfc/@is-import='true']/@has-import-kvarh='true'">
										<li>Import kVArh</li>
									</xsl:if>
									<xsl:if
										test="/source/supply-generation/mpan[mpan-top/llfc/@is-import='true']/@has-export-kwh='true'">
										<li>Export kWh</li>
									</xsl:if>
									<xsl:if
										test="/source/supply-generation/mpan[mpan-top/llfc/@is-import='true']/@has-export-kvarh='true'">
										<li>Export kVArh</li>
									</xsl:if>
								</ul>
							</td>
							<td>
								<ul>
									<xsl:if
										test="/source/supply-generation/mpan[mpan-top/llfc/@is-import='false']/@has-import-kwh='true'">
										<li>Import kWh</li>
									</xsl:if>
									<xsl:if
										test="/source/supply-generation/mpan[mpan-top/llfc/@is-import='false']/@has-import-kvarh='true'">
										<li>Import kVArh</li>
									</xsl:if>
									<xsl:if
										test="/source/supply-generation/mpan[mpan-top/llfc/@is-import='false']/@has-export-kwh='true'">
										<li>Export kWh</li>
									</xsl:if>
									<xsl:if
										test="/source/supply-generation/mpan[mpan-top/llfc/@is-import='false']/@has-export-kvarh='true'">
										<li>Export kVArh</li>
									</xsl:if>
								</ul>
							</td>
						</tr>
						<tr>
							<th>HHDC Account</th>
							<td>
								<a
									href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/55/screen/output/?account-id={/source/supply-generation/mpan[mpan-top/llfc/@is-import='true']/account[hhdc-contract]/@id}">
									<xsl:value-of
										select="/source/supply-generation/mpan[mpan-top/llfc/@is-import='true']/account[hhdc-contract]/@reference" />
								</a>
								<xsl:value-of select="' &gt; '" />
								<a
									href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/57/screen/output/?hhdc-contract-id={/source/supply-generation/mpan[mpan-top/llfc/@is-import='true']/account/hhdc-contract/@id}">
									<xsl:value-of
										select="/source/supply-generation/mpan[mpan-top/llfc/@is-import='true']/account/hhdc-contract/@name" />
								</a>
							</td>
							<td>
								<a
									href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/55/screen/output/?account-id={/source/supply-generation/mpan[mpan-top/llfc/@is-import='false']/account[hhdc-contract]/@id}">
									<xsl:value-of
										select="/source/supply-generation/mpan[mpan-top/llfc/@is-import='false']/account[hhdc-contract]/@reference" />
								</a>
								<xsl:value-of select="' &gt; '" />
								<a
									href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/57/screen/output/?hhdc-contract-id={/source/supply-generation/mpan[mpan-top/llfc/@is-import='false']/account/hhdc-contract/@id}">
									<xsl:value-of
										select="/source/supply-generation/mpan[mpan-top/llfc/@is-import='false']/account/hhdc-contract/@name" />
								</a>
							</td>
						</tr>
						<tr>
							<th>Supplier Account</th>
							<td>
								<a
									href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/41/screen/output/?account-id={/source/supply-generation/mpan[mpan-top/llfc/@is-import='true']/account[supplier-contract]/@id}">
									<xsl:value-of
										select="/source/supply-generation/mpan[mpan-top/llfc/@is-import='true']/account[supplier-contract]/@reference" />
								</a>
								<xsl:value-of select="' &gt; '" />
								<a
									href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/38/screen/output/?supplier-contract-id={/source/supply-generation/mpan[mpan-top/llfc/@is-import='true']/account/supplier-contract/@id}">
									<xsl:value-of
										select="/source/supply-generation/mpan[mpan-top/llfc/@is-import='true']/account/hhdc-contract/@name" />
								</a>
							</td>
							<td>
								<a
									href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/41/screen/output/?account-id={/source/supply-generation/mpan[mpan-top/llfc/@is-import='false']/account[supplier-contract]/@id}">
									<xsl:value-of
										select="/source/supply-generation/mpan[mpan-top/llfc/@is-import='false']/account[supplier-contract]/@reference" />
								</a>
								<xsl:value-of select="' &gt; '" />
								<a
									href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/38/screen/output/?supplier-contract-id={/source/supply-generation/mpan[mpan-top/llfc/@is-import='false']/account/supplier-contract/@id}">
									<xsl:value-of
										select="/source/supply-generation/mpan[mpan-top/llfc/@is-import='false']/account/supplier-contract/@name" />
								</a>
							</td>
						</tr>
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>