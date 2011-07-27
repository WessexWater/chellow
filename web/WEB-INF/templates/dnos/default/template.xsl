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
					Chellow &gt; DNOs &gt;
					<xsl:value-of select="/source/dno/@code" />
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
					<a href="{/source/request/@context-path}/dnos/">
						<xsl:value-of select="'DNOs'" />
					</a>
					<xsl:value-of
						select="concat(' &gt; ', /source/dno/@code)" />
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
							<xsl:value-of select="/source/dno/@id" />
						</td>
					</tr>
					<tr>
						<th>Code</th>
						<td>
							<xsl:value-of select="/source/dno/@code" />
						</td>
					</tr>
					<tr>
						<th>Participant</th>
						<td>
							<a
								href="{/source/request/@context-path}/participants/{/source/dno/participant/@id}/">
								<xsl:value-of
									select="/source/dno/participant/@code" />
							</a>
						</td>
					</tr>
					<tr>
						<th>Role</th>
						<td>
							<a
								href="{/source/request/@context-path}/market-roles/{/source/dno/market-role/@id}/">
								<xsl:value-of
									select="/source/dno/market-role/@description" />
							</a>
						</td>
					</tr>
				</table>
				<ul>
					<li>
						<a href="llfcs/">Line Loss Factor Classes</a>
					</li>
					<li>
						<a href="contracts/">Contracts</a>
					</li>
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>