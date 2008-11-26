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
					Chellow &gt; HHDC Contracts &gt;
					<xsl:value-of
						select="/source/stark-automatic-hh-data-importer/hhdc-contract/@name" />
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
					<a
						href="{/source/request/@context-path}/hhdc-contracts/">
						<xsl:value-of select="'HHDC Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/hhdc-contracts/{/source/stark-automatic-hh-data-importer/hhdc-contract/@id}/">
						<xsl:value-of
							select="/source/stark-automatic-hh-data-importer/hhdc-contract/@name" />
					</a>
					&gt; Stark Automatic HH Data Downloader
				</p>
				<br />
				<h1>Log</h1>
				<ul>
					<xsl:for-each select="//message">
						<li>
							<xsl:value-of select="@description" />
						</li>
					</xsl:for-each>
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>