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
					href="{/source/request/@context-path}/style/" />
				<title>
					Chellow &gt; User Roles &gt;
					<xsl:value-of select="/source/user-role/@code" />
				</title>
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img src="{/source/request/@context-path}/logo/"
							alt="Chellow Logo" />
						<span class="logo">Chellow</span>
					</a>
					<xsl:value-of select="' &gt; '" />
					<a
						href="{/source/request/@context-path}/user-roles/">
						<xsl:value-of select="'User Roles'" />
					</a>
					<xsl:value-of
						select="concat(' &gt; ', /source/user-role/@code)" />
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
							<xsl:value-of
								select="/source/user-role/@id" />
						</td>
					</tr>
					<tr>
						<th>Code</th>
						<td>
							<xsl:value-of
								select="/source/user-role/@code" />
						</td>
					</tr>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>