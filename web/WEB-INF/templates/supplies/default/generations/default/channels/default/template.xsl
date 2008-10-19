<?xml version="1.0" encoding="iso-8859-1"?>
<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="html" encoding="US-ASCII"
		doctype-public="-//W3C//DTD HTML 4.01//EN"
		doctype-system="http://www.w3.org/TR/html4/strict.dtd" indent="yes" />
	<xsl:template match="/">
		<html>
			<head>
				<title>
					Chellow &gt; Supplies &gt;
					<xsl:value-of
						select="/source/channel/supply-generation/supply/@id" />
					&gt; Generations &gt;
					<xsl:value-of
						select="/source/channel/supply-generation/supply/@id" />
					&gt; Channels &gt;
					<xsl:value-of select="/source/channel/@id" />
				</title>
				<link rel="stylesheet" type="text/css"
					href="{/source/request/@context-path}/style/" />
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img
							src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/">
						<xsl:value-of select="'Supplies'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/channel/supply-generation/supply/@id}/">
						<xsl:value-of
							select="/source/channel/supply-generation/supply/@id" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/channel/supply-generation/supply/@id}/generations/">
						<xsl:value-of select="'Generations'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/channel/supply-generation/supply/@id}/generations/{/source/channel/supply-generation/@id}/">
						<xsl:value-of
							select="/source/channel/supply-generation/@id" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/channel/supply-generation/supply/@id}/generations/{/source/channel/supply-generation/@id}/channels/">
						<xsl:value-of select="'Channels'" />
					</a>
					&gt;
					<xsl:value-of select="/source/channel/@id" />
				</p>
				<xsl:if test="/source/message">
					<ul>
						<xsl:for-each select="/source/message">
							<li>
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>
				<br />
				<ul>
					<li>
						<xsl:choose>
							<xsl:when
								test="/source/channel/@is-import='true'">
								Import
							</xsl:when>
							<xsl:otherwise>Export</xsl:otherwise>
						</xsl:choose>
					</li>
					<li>
						<xsl:choose>
							<xsl:when
								test="/source/channel/@is-kwh='true'">
								kWh
							</xsl:when>
							<xsl:otherwise>kVArh</xsl:otherwise>
						</xsl:choose>
					</li>
				</ul>
				<h4>
					<a href="hh-data/">HH Data</a>
				</h4>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>