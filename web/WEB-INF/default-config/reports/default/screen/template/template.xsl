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
						select="/source/template/screen-report/report/reports/org/@name" />
					&gt; Reports &gt;
					<xsl:value-of
						select="/source/template/screen-report/report/@name" />
					&gt; Screen Report &gt; Template
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
						href="{/source/request/@context-path}/orgs/{/source/template/screen-report/report/reports/org/@id}/">
						<xsl:value-of
							select="/source/template/screen-report/report/reports/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/template/screen-report/report/reports/org/@id}/reports/">
						<xsl:value-of select="'Reports'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/template/screen-report/report/reports/org/@id}/reports/{/source/template/screen-report/report/@id}/">
						<xsl:value-of
							select="/source/template/screen-report/report/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/template/screen-report/report/reports/org/@id}/reports/{/source/template/screen-report/report/@id}/screen/">
						<xsl:value-of select="'Screen'" />
					</a>
					&gt; Template
				</p>
				<br />
				<xsl:if test="//message">
					<ul>
						<xsl:for-each select="//message">
							<li>
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>
				<form method="post" action=".">
					<fieldset>
						<legend>Update template</legend>
						<textarea name="template-text" cols="80"
							rows="50">
							<xsl:value-of
								select="/source/template/text()" />
						</textarea>
						<input type="submit" value="Update" />
						<input type="reset" value="Reset" />
					</fieldset>
				</form>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>