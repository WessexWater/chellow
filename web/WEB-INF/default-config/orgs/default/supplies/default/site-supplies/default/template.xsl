<?xml version="1.0" encoding="iso-8859-1"?>
<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="html" encoding="US-ASCII"
		doctype-public="-//W3C//DTD HTML 4.01//EN"
		doctype-system="http://www.w3.org/TR/html4/strict.dtd" indent="yes" />

	<xsl:template match="/">
		<html>
			<head>
				<title>
					Chellow &gt; Organizations &gt;
					<xsl:value-of
						select="/source/site-supply/supply/organization/@name" />
					&gt; Supplies &gt;
					<xsl:value-of select="/source/site-supply/supply/@id" /> &gt;
					Site Supplies &gt;
					<xsl:value-of select="/source/site-supply/@id" />
				</title>

				<link rel="stylesheet" type="text/css"
					href="{/source/request/@context-path}/style/" />
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
						href="{/source/request/@context-path}/orgs/{/source/site-supply/supply/organization/@id}/">
						<xsl:value-of
							select="/source/site-supply/supply/organization/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/site-supply/supply/organization/@id}/supplies/">
						<xsl:value-of select="'Supplies'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/site-supply/supply/organization/@id}/supplies/{/source/site-supply/supply/@id}">
					<xsl:value-of select="/source/site-supply/supply/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/site-supply/supply/organization/@id}/supplies/{/source/site-supply/supply/@id}/site-supplies/">
						<xsl:value-of select="'Site Supplies'" />
					</a>
					&gt;
					<xsl:value-of select="/source/site-supply/@id" />
				</p>
				<xsl:if test="/source/message">
					<ul>
						<xsl:for-each select="/source/message">
							<li>
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>

				<br />


				<br />
				<form action="?view=confirm-delete">
					<fieldset>
						<legend>Delete this site-supply</legend>
						<input type="submit" value="Delete" />
					</fieldset>
				</form>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

