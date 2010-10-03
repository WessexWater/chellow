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
					href="{/source/request/@context-path}/style/" />
				<title>
					Chellow &gt; Supplier Contracts &gt;
					<xsl:value-of select="/source/batches/supplier-contract/@name" />
					&gt;
					<xsl:value-of select="'Batches'" />
				</title>
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					&gt;
					<a href="{/source/request/@context-path}/supplier-contracts/">
						<xsl:value-of select="'Supplier Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplier-contracts/{/source/batches/supplier-contract/@id}/">
						<xsl:value-of select="/source/batches/supplier-contract/@name" />
					</a>
					&gt;
					<xsl:value-of select="'Batches ['" />
					<a
						href="{/source/request/@context-path}/reports/89/output/?supplier-contract-id={/source/batches/supplier-contract/@id}">
						<xsl:value-of select="'view'" />
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
				<form action="." method="post">
					<fieldset>
						<legend>Add a batch</legend>
						<br />
						<label>
							<xsl:value-of select="'Reference '" />
							<input name="reference"
								value="{/source/request/parameter[@name = 'reference']/value}" />
						</label>
						<xsl:value-of select="' '" />
						<input type="submit" value="Add" />
						<input type="reset" value="Reset" />
					</fieldset>
				</form>
				<ul>
					<xsl:for-each select="/source/batches/batch">
						<li>
							<a href="{@id}/">
								<xsl:value-of select="@reference" />
							</a>
						</li>
					</xsl:for-each>
				</ul>
				<br />
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>