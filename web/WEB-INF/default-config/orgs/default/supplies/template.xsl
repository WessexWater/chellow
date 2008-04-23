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
					Chellow &gt; Organizations &gt;
					<xsl:value-of
						select="/source/supplies/org/@name" />
					&gt; Supplies
				</title>

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
					&gt;
					<a href="{/source/request/@context-path}/orgs/">
						Organizations
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/supplies/org/@id}/">
						<xsl:value-of
							select="/source/supplies/org/@name" />
					</a>
					&gt; Supplies
				</p>
				<br />

				<table>
					<caption>
						First 50 supplies and their latest generation
					</caption>
					<tr>
						<th>Id</th>
						<th>Name</th>
						<th>Source Code</th>
					</tr>
					<xsl:for-each select="/source/supplies/supply">
						<tr>
							<td>
								<a
									href="{/source/request/@context-path}/orgs/{/source/supplies/org/@id}/supplies/{@id}/">
									<xsl:value-of select="@id" />
								</a>								
							</td>
							<td>
								<a
									href="{/source/request/@context-path}/orgs/{/source/supplies/org/@id}/supplies/{@id}/">
									<xsl:value-of select="@name" />
								</a>
							</td>
							<td>
								<a
									href="{/source/request/@context-path}/sources/">
									<xsl:value-of select="source/@code" />
								</a>
							</td>
						</tr>
					</xsl:for-each>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

