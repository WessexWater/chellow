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
				<title>
					Chellow &gt; HHDC Contracts
					<xsl:value-of select="/source/hh-data-imports/hhdc-contract/@id" />
					&gt; HH Data Imports
				</title>
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					&gt;
					<a href="{/source/request/@context-path}/hhdc-contracts/">
						<xsl:value-of select="'HHDC Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/hhdc-contracts/{/source/hh-data-imports/hhdc-contract/@id}/">
						<xsl:value-of select="/source/hh-data-imports/hhdc-contract/@name" />
					</a>
					&gt; HH Data Imports
				</p>
				<br />
				<xsl:if test="/source/hh-data-imports/hh-data-import">
					<ul>
						<xsl:for-each select="/source/hh-data-imports/hh-data-import">
							<li>
								<a href="{@uri-id}/">
									<xsl:value-of select="@uri-id" />
								</a>
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>
				<xsl:if test="//message[not(../../hh-data-import)]">
					<ul>
						<xsl:for-each select="//message">
							<li>
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>
				<form enctype="multipart/form-data" method="post" action=".">
					<fieldset>
						<legend>Import HH data</legend>
						<br />
						<input type="file" name="import-file" size="45"
							value="{/source/request/parameter[@name = 'import-file']}" />
						<input type="submit" value="Import" />
					</fieldset>
				</form>
				<br />
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>