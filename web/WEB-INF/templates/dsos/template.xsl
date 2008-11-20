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

				<title>Chellow &gt; DSOs</title>
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
					<xsl:value-of select="' &gt; DSOs'" />
				</p>

				<p>
					This is a list of parties that have the
					<a
						href="{/source/request/@context-path}/market-roles/22/">
						<xsl:value-of select="'distributor'" />
					</a>
					role type.
				</p>

				<table>
					<thead>
						<tr>
							<th>Chellow Id</th>
							<th>Code</th>
							<th>Name</th>
						</tr>
					</thead>
					<tbody>

						<xsl:for-each select="/source/dsos/dso">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/dsos/{@id}/">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<xsl:value-of select="@code" />
								</td>
								<td>
									<xsl:value-of select="@name" />
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

