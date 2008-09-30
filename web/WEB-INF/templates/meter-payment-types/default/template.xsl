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
					Chellow &gt; Meter Payment Types &gt;
					<xsl:value-of
						select="/source/meter-payment-type/@code" />
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
						href="{/source/request/@context-path}/meter-payment-types/">
						<xsl:value-of select="'Meter Payment Types'" />
					</a>
					<xsl:value-of
						select="concat(' &gt; ', /source/meter-payment-type/@code)" />
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
							<xsl:value-of
								select="/source/meter-payment-type/@id" />
						</td>
					</tr>
					<tr>
						<th>Code</th>
						<td>
							<xsl:value-of
								select="/source/meter-payment-type/@code" />
						</td>
					</tr>
					<tr>
						<th>Description</th>
						<td>
							<xsl:value-of
								select="/source/meter-payment-type/@description" />
						</td>
					</tr>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

