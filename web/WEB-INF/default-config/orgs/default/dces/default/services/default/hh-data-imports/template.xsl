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
						select="/source/hh-data-imports/dce-service/dce/organization/@name" />
					&gt; DCEs &gt;
					<xsl:value-of
						select="/source/hh-data-imports/dce-service/dce/@name" />
					&gt; Services
					<xsl:value-of
						select="/source/hh-data-imports/dce-service/@id" />
					&gt; HH Data Imports
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
						href="{/source/request/@context-path}/orgs/{/source/hh-data-imports/dce-service/dce/organization/@id}/">
						<xsl:value-of
							select="/source/hh-data-imports/dce-service/dce/organization/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/hh-data-imports/dce-service/dce/organization/@id}/dces/">
						<xsl:value-of select="'DCEs'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/hh-data-imports/dce-service/dce/organization/@id}/dces/{/source/hh-data-imports/dce-service/dce/@id}/">
						<xsl:value-of
							select="/source/hh-data-imports/dce-service/dce/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/hh-data-imports/dce-service/dce/organization/@id}/dces/{/source/hh-data-imports/dce-service/dce/@id}/services/">

						<xsl:value-of select="'Services'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/hh-data-imports/dce-service/dce/organization/@id}/dces/{/source/hh-data-imports/dce-service/dce/@id}/services/{/source/hh-data-imports/dce-service/@id}/">
						<xsl:value-of
							select="/source/hh-data-imports/dce-service/@name" />
					</a>
					&gt; HH Data Imports
				</p>
				<br />
				<xsl:choose>
					<xsl:when
						test="/source/response/@status-code = '201'">
						<p>
							The
							<a
								href="{/source/response/header[@name = 'Location']/@value}">
								<xsl:value-of
									select="'new hh data import'" />
							</a>
							has been successfully created.
						</p>
					</xsl:when>
					<xsl:otherwise>
						<ul>
							<xsl:for-each
								select="/source/hh-data-imports/hh-data-import">
								<li>
									<a href="{@uri-id}/">
										<xsl:value-of select="@uri-id" />
									</a>
								</li>
							</xsl:for-each>
						</ul>
						<br />
						<hr />
						<xsl:if test="//message[not(../../hh-data-import)]">
							<ul>
								<xsl:for-each select="//message">
									<li>
										<xsl:value-of
											select="@description" />
									</li>
								</xsl:for-each>
							</ul>
						</xsl:if>
						<form enctype="multipart/form-data"
							method="post" action=".">
							<fieldset>
								<legend>Import HH data</legend>
								<br />
								<label>
									<a
										href="http://chellow.wikispaces.com/HhDataFormats">
										<xsl:value-of select="'File'" />
									</a>
									<xsl:value-of select="' '" />
									<input type="file"
										name="import-file" size="45"
										value="{/source/request/parameter[@name = 'import-file']}" />
								</label>

								<input type="submit" value="Import" />
							</fieldset>
						</form>

						<br />
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>