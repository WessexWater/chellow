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
					<xsl:value-of select="/source/org/@name" />
					&gt; Sites
				</title>

			</head>

			<body>
				<xsl:if test="//message">
					<ul>
						<xsl:for-each select="//message">
							<li>
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>
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
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/">
						<xsl:value-of select="/source/org/@name" />
					</a>
					&gt;
					<xsl:value-of select="'Sites ['" />
					<a
						href="{/source/request/@context-path}/orgs/1/reports/1/screen/output/">
						<xsl:value-of select="'view'" />
					</a>
					<xsl:value-of select="']'" />
				</p>
				<br />
				<xsl:choose>
					<xsl:when
						test="/source/response/@status-code = '201'">
						<p>
							The
							<a
								href="{/source/response/header[@name = 'Location']/@value}">
								<xsl:value-of select="'new site'" />
							</a>
							has been successfully created.
						</p>
					</xsl:when>
					<xsl:otherwise>
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
							<xsl:for-each select="/source/org/site">
								<li>
									<a href="{@id}/">
										<xsl:value-of
											select="concat(@code, ' ', @name)" />
									</a>
								</li>
							</xsl:for-each>
						</ul>
						<hr />
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
									<input name="name"
										value="{/source/request/parameter[@name='name']/value}" />
								</label>
								<br />
								<br />
								<input type="submit" value="Add" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

