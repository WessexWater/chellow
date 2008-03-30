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
						select="/source/script-output/screen-report/report/organization/@name" />
					&gt; Reports &gt;
					<xsl:value-of select="/source/script-output/screen-report/report/@name" />
					&gt; Screen
					&gt; Script output
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
					<a href="{/source/request/@context-path}/orgs/">
						<xsl:value-of select="'Organizations'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/script-output/screen/report/organization/@id}/">
						<xsl:value-of
							select="/source/script-output/screen/report/organization/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/script-output/screen/report/organization/@id}/reports/">
						<xsl:value-of select="'Reports'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/script-output/screen-report/report/organization/@id}/reports/{/source/script-output/screen-report/report/@id}/">
						<xsl:value-of
							select="/source/script-output/screen-report/report/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/script-output/screen-report/report/organization/@id}/reports/{/source/script-output/report/@id}/screen/">
						<xsl:value-of
							select="'Screen'" />
					</a>
					&gt; Script output
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
					<xsl:value-of select="/source/script-output/result/text()" />
				</pre>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>