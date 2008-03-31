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
						href="{/source/request/@context-path}/sscs/">
						<xsl:value-of
							select="'Standard Settlement Configurations'" />
					</a>
					<xsl:value-of
						select="concat(' &gt; ', /source/ssc/@code)" />
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
						<xsl:value-of select="/source/ssc/@code" />
					</li>
					<li>
						TPRs
						<ul>
							<xsl:for-each select="tpr">
								<li>
									<xsl:value-of select="@code" />
									<xsl:if
										test="position() != last()">
										<xsl:value-of select="', '" />
									</xsl:if>
								</li>
							</xsl:for-each>
						</ul>
					</li>
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

