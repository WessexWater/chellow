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
					Chellow &gt; TPRs &gt;
					<xsl:value-of select="/source/tpr/@code" />
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
					<a href="{/source/request/@context-path}/tprs/">
						<xsl:value-of select="'TPRs'" />
					</a>
					<xsl:value-of
						select="concat(' &gt; ', /source/tpr/@code)" />
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
							<xsl:value-of select="/source/tpr/@id" />
						</td>
					</tr>
					<tr>
						<th>Code</th>
						<td>
							<xsl:value-of select="/source/tpr/@code" />
						</td>
					</tr>
					<tr>
						<th>Teleswitch or Clock</th>
						<td>
							<xsl:choose>
								<xsl:when
									test="/source/tpr/@is-teleswitch='true'">
									Teleswitch
								</xsl:when>
								<xsl:otherwise>Clock</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
					<tr>
						<th>GMT or Clock Time</th>
						<td>
							<xsl:choose>
								<xsl:when test="@is-gmt='true'">
									GMT
								</xsl:when>
								<xsl:otherwise>
									Clock Time
								</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
				</table>

				<ul>
					<li>
						<a href="clock-intervals">Clock Intervals</a>
					</li>
				</ul>

				<h3>SSCs</h3>

				<ul>
					<xsl:for-each select="/source/tpr/measurement-requirement/ssc">
						<li>
							<a
								href="{/source/request/@context-path}/sscs/{@id}/">
								<xsl:value-of select="@code"></xsl:value-of>
							</a>
						</li>
					</xsl:for-each>
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

