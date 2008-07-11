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
				<title>Chellow &gt; Providers</title>
			</head>

			<body>
				<xsl:if test="//message">
					<ul>
						<xsl:for-each select="//message">
							<li>
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>

				<p>
					<a href="{/source/request/@context-path}/">
						<img
							src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					<xsl:value-of select="' &gt; Providers'" />
				</p> 
				<table>
					<thead>
						<tr>
							<th>Chellow Id</th>
							<th>Participant</th>
							<th>Market Role</th>
							<th>DSO Code</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each
							select="/source/providers/provider">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/providers/{@id}/">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<a
										href="{/source/request/@context-path}/participants/{participant/@id}/">
										<xsl:value-of
											select="participant/@name" />
									</a>
								</td>
								<td>
									<a
										href="{/source/request/@context-path}/market-roles/{market-role/@id}/">
										<xsl:value-of
											select="market-role/@description" />
									</a>
								</td>
								<td>
																		<xsl:value-of
											select="@dso-code" />
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>
