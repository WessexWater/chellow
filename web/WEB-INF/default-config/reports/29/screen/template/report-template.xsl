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
					&gt; DSOs &gt;
					<xsl:value-of
						select="/source/mpan-top/llf/dso/@code" />
					&gt; MPAN tops &gt;
					<xsl:value-of select="/source/mpan-top/llf/@code" />
				</title>
			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/1/reports/0/screen/output/">
						<xsl:value-of
							select="/source/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/1/reports/22/screen/output/">
						<xsl:value-of select="'DSOs'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/1/reports/23/screen/output/?dso-id={/source/mpan-top/llf/dso/@id}">
						<xsl:value-of
							select="/source/mpan-top/llf/dso/@code" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/1/reports/28/screen/output/?dso-id={/source/mpan-top/llf/dso/@id}">
						<xsl:value-of select="'MPAN tops'" />
					</a>
					&gt;
					<xsl:value-of select="/source/mpan-top/@id" />
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
				<table>
					<caption>MPAN top line properties</caption>
					<thead>
						<tr>
							<th>Property</th>
							<th>Value</th>
						</tr>
					</thead>
					<tbody>
						<tr>
							<td>Profile Class</td>
							<td>
								<a
									href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/27/screen/output/?pc-id={/source/mpan-top/profile-class/@id}">
									<xsl:value-of
										select="concat(/source/mpan-top/profile-class/@code, ' - ', /source/mpan-top/profile-class/@description)" />
								</a>
							</td>
						</tr>
						<tr>
							<td>Meter Timeswitch</td>
							<td>
								<a
									href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/31/screen/output/?mt-id={/source/mpan-top/meter-timeswitch/@id}">
									<xsl:value-of
										select="concat(/source/mpan-top/meter-timeswitch/@code, ' - ', /source/mpan-top/meter-timeswitch/@description)" />
								</a>
							</td>
						</tr>
						<tr>
							<td>Line Loss Factor</td>
							<td>
								<a
									href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/25/screen/output/?llf-id={/source/mpan-top/llf/@id}">
									<xsl:value-of
										select="concat(/source/mpan-top/llf/@code, ' - ', /source/mpan-top/llf/@description)" />
								</a>
							</td>
						</tr>
					</tbody>
				</table>

				<h3>SSCs</h3>

				<ul>
					<xsl:for-each select="/source/mpan-top/ssc">
						<li>
							<a
								href="{/source/request/@context-path}/sscs/{@id}/">
								<xsl:value-of select="@code" />
							</a>
						</li>
					</xsl:for-each>
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>