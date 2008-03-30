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
					Chellow &gt; Meter Timeswitches &gt;
					<xsl:value-of
						select="/source/meter-timeswitch/@code" />
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
					<a
						href="{/source/request/@context-path}/meter-timeswitches/">
						<xsl:value-of select="'Meter Timeswitches'" />
					</a>
					<xsl:value-of
						select="concat(' &gt; ', /source/meter-timeswitch/@code)" />
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
				<ul>
					<li>
						Code:
						<xsl:value-of
							select="/source/meter-timeswitch/@code" />
					</li>
					<li>
						DSO:
						<xsl:choose>
							<xsl:when
								test="/source/meter-timeswitch/dso">
								<a
									href="{/source/request/@context-path}/dsos/{/source/meter-timeswitch/dso/@id}">
									<xsl:value-of
										select="/source/meter-timeswitch/dso/@code" />
								</a>
							</xsl:when>
							<xsl:otherwise>None</xsl:otherwise>
						</xsl:choose>
					</li>
					<li>
						Is Unmetered?:
						<xsl:value-of
							select="/source/meter-timeswitch/@is-unmetered" />
					</li>
					<li>TPRs
						<ul>
							<xsl:for-each select="/source/meter-timeswitch/register">
								<li>
									<xsl:for-each select="tpr">
										<xsl:value-of select="@code" />
										<xsl:if
											test="position() != last()">
											<xsl:value-of select="', '" />
										</xsl:if>
									</xsl:for-each>
								</li>
							</xsl:for-each>
						</ul>
					</li>
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

