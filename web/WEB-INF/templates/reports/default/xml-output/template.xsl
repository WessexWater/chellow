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
					Chellow &gt; Reports &gt;
					<xsl:value-of select="/source/xml-output/report/@name" />
					&gt; XML Output
				</title>

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
						href="{/source/request/@context-path}/reports/">
						<xsl:value-of select="'Reports'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/reports/{/source/xml-output/report/@id}/">
						<xsl:value-of
							select="/source/xml-output/report/@name" />
					</a>
					&gt; XML Output
				</p>
				<br />
				<xsl:if test="//message">
					<ul>
						<xsl:for-each select="//message">
							<li>
								<pre>
									<xsl:value-of select="@description" />
								</pre>
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>

				<pre>
					<xsl:value-of select="/source/xml-output/result/text()" />
				</pre>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>