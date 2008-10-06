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
						select="/source/channels/supply-generation/supply/org/@name" />
					&gt; Supplies &gt;
					<xsl:value-of
						select="/source/channels/supply-generation/supply/@id" />
					&gt; Generations &gt;
					<xsl:value-of
						select="/source/channels/supply-generation/@id" />
					&gt; Channels
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
						href="{/source/request/@context-path}/orgs/{/source/channels/supply-generation/supply/org/@id}/">
						<xsl:value-of
							select="/source/channels/supply-generation/supply/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/channels/supply-generation/supply/org/@id}/supplies/">
						<xsl:value-of select="'Supplies'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/channels/supply-generation/supply/org/@id}/supplies/{/source/channels/supply-generation/supply/@id}/">
						<xsl:value-of
							select="/source/channels/supply-generation/supply/@id" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/channels/supply-generation/supply/org/@id}/supplies/{/source/channels/supply-generation/supply/@id}/generations/">
						<xsl:value-of select="'Generations'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/channels/supply-generation/supply/org/@id}/supplies/{/source/channels/supply-generation/supply/@id}/generations/{/source/channels/supply-generation/@id}">
						<xsl:value-of
							select="/source/channels/supply-generation/@id" />
					</a>
					&gt; Channels
				</p>
				<br />
				<table>
					<thead>
						<tr>
							<th>Chellow Id</th>
							<th colspan="2">Type</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each
							select="/source/channels/channel">
							<tr>
								<td>
									<a href="{@id}/">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<xsl:choose>
										<xsl:when
											test="@is-import='true'">
											import
										</xsl:when>
										<xsl:otherwise>
											export
										</xsl:otherwise>
									</xsl:choose>
								</td>
								<td>
									<xsl:choose>
										<xsl:when
											test="@is-kwh='true'">
											kWh
										</xsl:when>
										<xsl:otherwise>
											kVArh
										</xsl:otherwise>
									</xsl:choose>
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>