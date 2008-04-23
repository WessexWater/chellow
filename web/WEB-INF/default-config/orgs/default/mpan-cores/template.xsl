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
						select="/source/mpan-cores/org/@name" />
					&gt; MPAN Cores
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
						<xsl:value-of select="'Organizations'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/mpan-cores/org/@id}/">
						<xsl:value-of
							select="/source/mpan-cores/org/@name" />
					</a>
					&gt; MPAN Cores
				</p>
				<br />

				<form action=".">
					<fieldset>
						<legend>Search by MPAN core</legend>
						<input name="search-pattern"
							value="{/source/request/parameter[@name='search-pattern']/value}" />

						<input type="submit" value="Search" />
					</fieldset>
				</form>

				<table>
					<caption>
						First 50 matching MPANs, ordered by MPAN core
					</caption>
					<tr>
						<th>MPAN Core</th>
						<th>Supply</th>
					</tr>
					<xsl:for-each
						select="/source/mpan-cores/mpan-core">
						<tr>
							<td>
								<code>
									<xsl:value-of select="@core" />
								</code>
							</td>
							<td>
								<a
									href="{/source/request/@context-path}/orgs/{/source/mpan-cores/org/@id}/supplies/{supply/@id}/">
									<xsl:value-of select="supply/@id"/>
								</a>
							</td>
						</tr>
					</xsl:for-each>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>