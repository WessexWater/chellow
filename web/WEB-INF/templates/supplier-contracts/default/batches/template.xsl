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
					Chellow &gt; Supplier Contracts &gt;
					<xsl:value-of select="/source/batches/supplier-contract/@name" />
					&gt;
					<xsl:value-of select="'Batches'" />
				</title>
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/reports/1/output/">
						<xsl:value-of select="'Chellow'" />
					</a>
					&gt;
					<a href="{/source/request/@context-path}/reports/75/output/">
						<xsl:value-of select="'Supplier Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/reports/77/output/?supplier-contract-id={/source/batches/supplier-contract/@id}">
						<xsl:value-of select="/source/batches/supplier-contract/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/reports/89/output/?supplier-contract-id={/source/batches/supplier-contract/@id}">
						<xsl:value-of select="'Batches'" />
					</a>
					&gt; Edit
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
						<br />
						<label>
							<xsl:value-of select="'Description '" />
							<input name="description"
								value="{/source/request/parameter[@name = 'description']/value}" />
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