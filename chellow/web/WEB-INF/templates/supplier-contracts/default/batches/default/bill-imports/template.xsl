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
					<xsl:value-of select="/source/bill-imports/batch/supplier-contract/@name" />
					&gt; Batches &gt;
					<xsl:value-of select="/source/bill-imports/batch/@reference" />
					&gt; Bill Imports
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
						href="{/source/request/@context-path}/reports/77/output/?supplier-contract-id={/source/bill-imports/batch/supplier-contract/@id}">
						<xsl:value-of select="/source/bill-imports/batch/supplier-contract/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/reports/89/output/?supplier-contract-id={/source/bill-imports/batch/supplier-contract/@id}">
						<xsl:value-of select="'Batches'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/reports/91/output/?batch-id={/source/bill-imports/batch/@id}">
						<xsl:value-of select="/source/bill-imports/batch/@reference" />
					</a>
					&gt;
					<xsl:value-of select="'Bill Imports'" />
				</p>
				<xsl:if test="/source/message">
					<ul>
						<xsl:for-each select="/source/message">
							<li>
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>
				<br />
				<form enctype="multipart/form-data" action="." method="post">
					<fieldset>
						<legend>Import Bills</legend>
						<br />
						<input type="file" name="file"
							value="{/source/request/parameter[@name = 'file']/value}" />
						<xsl:value-of select="' '" />
						<input type="submit" value="Import" />
					</fieldset>
				</form>
				<ul>
					<xsl:for-each select="/source/bill-imports/bill-import">
						<li>
							<a href="{@id}/">
								<xsl:value-of select="@id" />
							</a>
						</li>
					</xsl:for-each>
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>