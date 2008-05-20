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
					<xsl:value-of select="/source/header-import-processes/org/@name" />
					&gt; Header Data Imports
				</title>

			</head>

			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img src="{/source/request/@context-path}/logo/"
							alt="Chellow Logo" />
						<span class="logo">Chellow</span>
					</a>
					&gt;
					<a href="{/source/request/@context-path}/orgs/">
						<xsl:value-of select="'Organizations'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/header-import-processes/org/@id}/">
						<xsl:value-of
							select="/source/header-import-processes/org/@name" />
					</a>
					&gt; Header Data Imports
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
				<xsl:choose>
					<xsl:when
						test="/source/response/@status-code = '201'">
						<p>
							The
							<a
								href="{/source/response/header[@name = 'Location']/@value}">
								<xsl:value-of
									select="'new header data import'" />
							</a>
							has started off okay.
						</p>
					</xsl:when>
					<xsl:otherwise>
											<form enctype="multipart/form-data"
							method="post" action=".">
							<fieldset>
								<legend>New import</legend>
								<label>
									<a
										href="http://chellow.wikispaces.com/importingheaderdata">
										<xsl:value-of
											select="'CSV File'" />
									</a>
									<xsl:value-of select="' '" />
									<input type="file"
										name="import-file" size="45"
										value="{/source/request/parameter[@name = 'import-file']/value}" />
								</label>
								<input type="submit" value="Import" />
							</fieldset>
						</form>
					<hr />
						<xsl:if
							test="/source/header-import-processes/header-import-process">
							<ul>
								<xsl:for-each
									select="/source/header-import-processes/header-import-process">
									<li>
										<a href="{@id}/">
											<xsl:value-of select="@id" />
										</a>
									</li>
								</xsl:for-each>
							</ul>
						</xsl:if>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

