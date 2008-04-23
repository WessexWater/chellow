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
						select="/source/channels/supply/org/@name" />
					&gt; Supplies &gt;
					<xsl:value-of select="/source/channels/supply/@id" />
					&gt; Channels &gt;
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
						href="{/source/request/@context-path}/orgs/{/source/channels/supply/site/org/@id}/">
						<xsl:value-of
							select="/source/channels/supply/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/channels/supply/org/@id}/supplies/">
						Supplies
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/channels/supply/org/@id}/supplies/{/source/channels/supply/@id}/">
						<xsl:value-of
							select="/source/channels/supply/@id" />
					</a>
					&gt; Channels
				</p>
				<br />
				<table>
					<thead>
						<tr>
							<th>Channel</th>
							<th>Import / Export</th>
							<th>kWh / kVArh</th>
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