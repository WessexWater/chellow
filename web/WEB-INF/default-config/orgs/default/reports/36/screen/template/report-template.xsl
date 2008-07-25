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
					&gt; Market Participants &gt;
					<xsl:value-of select="/source/participant/@name" />
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
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/35/screen/output/">
						<xsl:value-of select="'Market Participants'" />
					</a>
					&gt;
					<xsl:value-of select="/source/participant/@name" />
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
					<tbody>
						<tr>
							<th>Chellow Id</th>
							<td>
								<xsl:value-of
									select="/source/participant/@id" />
							</td>
						</tr>
						<tr>
							<th>Code</th>
							<td>
								<xsl:value-of
									select="/source/participant/@code" />
							</td>
						</tr>
						<tr>
							<th>Name</th>
							<td>
								<xsl:value-of
									select="/source/participant/@name" />
							</td>
						</tr>
					</tbody>
				</table>

				<table>
					<caption>Providers</caption>
					<thead>
						<tr>
							<th>Chellow Id</th>
							<th>Name</th>
							<th>Market Role</th>
							<th>DSO Code</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each
							select="/source/participant/provider">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/providers/{@id}/">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<xsl:value-of select="@name" />
								</td>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/61/screen/output/?role-id={market-role/@id}">
										<xsl:value-of
											select="market-role/@description" />
									</a>
								</td>
								<td>
									<xsl:value-of select="@dso-code" />
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>