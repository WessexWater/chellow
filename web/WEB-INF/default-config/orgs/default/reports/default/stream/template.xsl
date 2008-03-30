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
						select="/source/stream-report/report/reports/organization/@name" />
					&gt; Reports &gt;
					<xsl:value-of select="/source/stream-report/report/@name" />
					&gt; Stream
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
						href="{/source/request/@context-path}/orgs/{/source/stream-report/report/reports/organization/@id}/">
						<xsl:value-of
							select="/source/stream-report/report/reports/organization/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/stream-report/report/reports/organization/@id}/reports/">
						<xsl:value-of select="'Reports'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/stream-report/report/reports/organization/@id}/reports/{/source/stream-report/report/@id}/">
						<xsl:value-of
							select="/source/stream-report/report/@name" />
					</a>
					&gt; Stream
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
				<ul>
				<li>
					<a href="output/">Output</a>
				</li>
				<li>
					<a href="script/">Script</a>
				</li>
</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>