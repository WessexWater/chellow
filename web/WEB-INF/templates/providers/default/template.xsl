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
					href="{/source/request/@context-path}/reports/19/output/" />
				<title>
					Chellow &gt; Providers &gt;
					<xsl:value-of select="/source/provider/@id" />
				</title>
			</head>

			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img
							src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					<xsl:value-of select="' &gt; '" />
					<a
						href="{/source/request/@context-path}/providers/">
						<xsl:value-of select="'Providers'" />
					</a>
					<xsl:value-of
						select="concat(' &gt; ', /source/provider/@id)" />
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
					<tr>
						<th>Chellow Id</th>
						<td>
							<xsl:value-of select="/source/provider/@id" />
						</td>
					</tr>
					<tr>
						<th>Participant</th>
						<td>
							<a
								href="{/source/request/@context-path}/participants/{/source/provider/participant/@id}/">
								<xsl:value-of
									select="/source/provider/participant/@name" />
							</a>
						</td>
					</tr>
					<tr>
						<th>Role</th>
						<td>
							<a
								href="{/source/request/@context-path}/market-roles/{/source/provider/market-role/@id}/">
								<xsl:value-of
									select="/source/provider/market-role/@description" />
							</a>
						</td>
					</tr>
					<xsl:if
						test="/source/provider/market-role/@code='R'">
						<tr>
							<th>DSO Code</th>
							<td>
								<xsl:value-of
									select="/source/provider/@dso-code" />
							</td>
						</tr>
					</xsl:if>
				</table>
				<!--
				<xsl:if test="/source/provider/market-role/@code='R'">
					<ul>
						<li>
							<a href="llfcs/">LLFCs</a>
						</li>
						<li>
							<a href="mpan-tops/">MPAN Top Lines</a>
						</li>
						<li>
							<a href="services/">Services</a>
						</li>
					</ul>
				</xsl:if>
				-->
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>