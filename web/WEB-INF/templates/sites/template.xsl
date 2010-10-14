<?xml version="1.0" encoding="us-ascii"?>
<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="html" encoding="US-ASCII"
		doctype-public="-//W3C//DTD HTML 4.01//EN" doctype-system="http://www.w3.org/TR/html4/strict.dtd"
		indent="yes" />
	<xsl:template match="/">
		<html>
			<head>
				<link rel="stylesheet" type="text/css"
					href="{/source/request/@context-path}/reports/19/output/" />
				<title>Chellow &gt; Sites</title>
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					&gt;
					<xsl:value-of select="'Sites ['" />
					<a href="{/source/request/@context-path}/reports/3/output/">
						<xsl:value-of select="'view'" />
					</a>
					<xsl:value-of select="']'" />
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
				<br />
				<form action=".">
					<input name="search-pattern"
						value="{/source/request/parameter[@name='search-pattern']/value}" />

					<input type="submit" value="Search" />
				</form>
				<br />
				<p>
					The search results are truncated after 50.
						</p>
				<ul>
					<xsl:for-each select="/source/sites/site">
						<li>
							<a href="{@id}/">
								<xsl:value-of select="concat(@code, ' ', @name)" />
							</a>
						</li>
					</xsl:for-each>
				</ul>
				<br />
				<form action="." method="post">
					<fieldset>
						<legend>Add site</legend>
						<label>
							Code
							<xsl:value-of select="' '" />
							<input name="code"
								value="{/source/request/parameter[@name='code']/value}" />
						</label>
						<br />
						<label>
							Name
							<xsl:value-of select="' '" />
							<input name="name" length="100"
								value="{/source/request/parameter[@name='name']/value}" />
						</label>
						<br />
						<br />
						<input type="submit" value="Add" />
						<input type="reset" value="Reset" />
					</fieldset>
				</form>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>