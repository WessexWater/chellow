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
					Chellow &gt; Sites &gt; Supply:
					<xsl:value-of
						select="/source/supply-generation/supply/@name" />
					&gt; Generation:
					<xsl:value-of
						select="/source/supply-generation/@id" />
				</title>
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/orgs/{/source/supply-generation/supply/organization/@id}/reports/0/screen/output/">
						<img src="{/source/request/@context-path}/logo/"
							alt="Chellow logo" />
						<span class="logo">Chellow</span>
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/1/reports/1/screen/output/">
						<xsl:value-of select="'Sites'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/1/reports/3/screen/output/?supply-id={/source/supply-generation/supply/@id}">
						Supply:
						<xsl:value-of
							select="/source/supply-generation/supply/@name" />
					</a>
					&gt;
					<span id="title">
						Generation:
						<xsl:value-of
							select="/source/supply-generation/@id" />
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
							<th>Profile</th>
							<th>Meter Timeswitch</th>
							<th>Line Loss Factor</th>
							<th>Core</th>
							<th>Supply Capacity</th>
							<th>Channels</th>
							<th>DCE</th>
							<th>DCE Service</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each
							select="/source/supply-generation/mpan">
							<tr>
								<td>
									<xsl:value-of select="@label" />
								</td>
								<td>
									<xsl:value-of
										select="concat(mpan-top/profile-class/@code, ' - ', mpan-top/profile-class/@description)" />
								</td>
								<td>
									<xsl:value-of
										select="concat(mpan-top/meter-timeswitch/@code, ' - ', mpan-top/meter-timeswitch/@description)" />
								</td>
								<td>
									<xsl:value-of
										select="concat(mpan-top/line-loss-factor/@code, ' - ', mpan-top/line-loss-factor/@description)" />
								</td>
								<td>
									<xsl:value-of
										select="mpan-core/@core" />
								</td>
								<td>
									<xsl:value-of
										select="@agreed-supply-capacity" />
								</td>
								<td>
									<ul>
										<xsl:if
											test="@has-import-kwh='true'">
											<li>Import kWh</li>
										</xsl:if>
										<xsl:if
											test="@has-import-kvarh='true'">
											<li>Import kVArh</li>
										</xsl:if>
										<xsl:if
											test="@has-export-kwh='true'">
											<li>Export kWh</li>
										</xsl:if>
										<xsl:if
											test="@has-export-kvarh='true'">
											<li>Export kVArh</li>
										</xsl:if>
									</ul>
								</td>
								<td>
									<xsl:value-of
										select="dce-service/dce/@name" />
								</td>
								<td>
									<xsl:value-of
										select="dce-service/@name" />
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

