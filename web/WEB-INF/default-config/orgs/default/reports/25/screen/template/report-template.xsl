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
					&gt; Providers &gt;
					<xsl:value-of
						select="/source/llfc/provider/@dso-code" />
					&gt; LLFCs &gt;
					<xsl:value-of select="/source/llfc/@code" />
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
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/22/screen/output/">
						<xsl:value-of select="'Providers'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/23/screen/output/?provider-id={/source/llfc/provider/@id}">
						<xsl:value-of
							select="/source/llfc/provider/@dso-code" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/24/screen/output/?dso-id={/source/llfc/provider/@id}">
						<xsl:value-of select="'LLFCs'" />
					</a>
					&gt;
					<xsl:value-of select="/source/llfc/@code" />
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
					<tr>
						<th>Chellow Id</th>
						<td>
							<xsl:value-of select="/source/llfc/@id" />
						</td>
					</tr>
					<tr>
						<th>Code</th>
						<td>
							<xsl:value-of select="/source/llfc/@code" />
						</td>
					</tr>
					<tr>
						<th>Description</th>
						<td>
							<xsl:value-of
								select="/source/llfc/@description" />
						</td>

					</tr>
					<tr>
						<th>Voltage Level</th>
						<td>
							<xsl:value-of
								select="concat(/source/llfc/voltage-level/@code, ' - ', /source/llfc/voltage-level/@name)" />
						</td>
					</tr>
					<tr>
						<th>Is Substation?</th>
						<td>
							<xsl:value-of
								select="/source/llfc/@is-substation" />
						</td>
					</tr>
					<tr>
						<th>Is Import?</th>
						<td>
							<xsl:value-of
								select="/source/llfc/@is-import" />
						</td>
					</tr>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

