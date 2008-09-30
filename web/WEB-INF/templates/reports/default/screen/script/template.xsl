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
						select="/source/report-script/*/report/reports/org/@name" />
					&gt; Reports &gt;
					<xsl:value-of select="/source/report-script/*/report/@name" />
					&gt; Report Type
					&gt; Script
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
						href="{/source/request/@context-path}/orgs/{/source/report-script/*/report/reports/org/@id}/">
						<xsl:value-of
							select="/source/report-script/*/report/reports/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/report-script/*/report/reports/org/@id}/reports/">
						<xsl:value-of select="'Reports'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/report-script/*/report/reports/org/@id}/reports/{/source/report-script/*/report/@id}/">
						<xsl:value-of
							select="/source/report-script/*/report/@name" />
					</a> &gt;
					<a
						href="..">
						<xsl:value-of
							select="'Report Type'" />
					</a>
					&gt; Script
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
				<form method="post" action=".">
					<fieldset>
						<legend>Update Script</legend>
						<textarea name="script-text" cols="80"
							rows="50">
							<xsl:value-of
								select="/source/report-script/text()" />
						</textarea>
						<input type="submit" value="Save" />
						<input type="reset" value="Reset" />
					</fieldset>
				</form>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>