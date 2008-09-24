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
					href="{/source/request/@context-path}/orgs/1/reports/9/stream/output/" />

				<title>
					<xsl:value-of select="/source/org/@name" />
					&gt; Sites
				</title>
			</head>

			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/1/reports/0/screen/output/">
						<xsl:value-of select="/source/org/@name" />
					</a>
					&gt;
					<xsl:value-of select="'Sites ['" />
					<a
						href="{/source/request/@context-path}/orgs/1/sites/">
						<xsl:value-of select="'edit'" />
					</a>
					<xsl:value-of select="']'" />
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
				<form action=".">
					<fieldset>
						<input name="search-pattern"
							value="{/source/request/parameter[@name='search-pattern']/value}" />
						<xsl:value-of select="' '" />
						<input type="submit" value="Search" />
					</fieldset>
				</form>
				<xsl:choose>
					<xsl:when test="/source/site">
						<p>
							Only the first 50 sites of the search
							results are shown.
						</p>
						<ul>
							<xsl:for-each select="/source/site">
								<li>
									<a
										href="{/source/request/@context-path}/orgs/1/reports/2/screen/output/?site-id={@id}">
										<xsl:value-of
											select="concat(@code, ' ', @name)" />
									</a>
								</li>
							</xsl:for-each>
						</ul>
					</xsl:when>
					<xsl:when
						test="/source/request/parameter[@name='search-pattern']">
						<p>No sites matched your search</p>
					</xsl:when>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

