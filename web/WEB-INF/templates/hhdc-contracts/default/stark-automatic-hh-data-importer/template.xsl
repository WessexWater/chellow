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
						select="/source/stark-automatic-hh-data-importer/dce-service/dce/org/@name" />
					&gt; DCEs &gt;
					<xsl:value-of
						select="/source/stark-automatic-hh-data-importer/dce-service/dce/@name" />
					&gt; Services &gt;
					<xsl:value-of
						select="/source/stark-automatic-hh-data-importer/dce-service/@name" />
					&gt; Stark Automatic HH Data Downloader
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
						href="{/source/request/@context-path}/orgs/{/source/stark-automatic-hh-data-importer/dce-service/dce/org/@id}/">
						<xsl:value-of
							select="/source/stark-automatic-hh-data-importer/dce-service/dce/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/stark-automatic-hh-data-importer/dce-service/dce/org/@id}/dces/">
						<xsl:value-of select="'DCEs'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/stark-automatic-hh-data-importer/dce-service/dce/org/@id}/dces/{/source/stark-automatic-hh-data-importer/dce-service/dce/@id}/">
						<xsl:value-of
							select="/source/stark-automatic-hh-data-importer/dce-service/dce/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/stark-automatic-hh-data-importer/dce-service/dce/org/@id}/dces/{/source/stark-automatic-hh-data-importer/dce-service/dce/@id}/services/">
						<xsl:value-of select="'Services'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/stark-automatic-hh-data-importer/dce-service/dce/org/@id}/dces/{/source/stark-automatic-hh-data-importer/dce-service/dce/@id}/services/{/source/stark-automatic-hh-data-importer/dce-service/@id}/">
						<xsl:value-of
							select="/source/stark-automatic-hh-data-importer/dce-service/@name" />
					</a>
					&gt; Stark Automatic HH Data Downloader
				</p>
				<br />

				<h1>Log</h1>
				<ul>
					<xsl:for-each
						select="//message">
						<li>
							<xsl:value-of select="@description" />
						</li>
					</xsl:for-each>
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>