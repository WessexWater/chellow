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
					Chellow &gt; HHDC Contracts &gt;
					<xsl:value-of select="/source/bill-imports/batch/hhdc-contract/@name" />
					&gt; Batches &gt;
					<xsl:value-of select="/source/bill-imports/batch/@reference" />
					&gt; Bill Imports
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
						href="{/source/request/@context-path}/hhdc-contracts/{/source/bill-imports/batch/hhdc-contract/@id}/">
						<xsl:value-of select="/source/bill-imports/batch/hhdc-contract/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/hhdc-contracts/{/source/bill-imports/batch/hhdc-contract/@id}/batches/">
						<xsl:value-of select="'Batches'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/hhdc-contracts/{/source/bill-imports/batch/hhdc-contract/@id}/batches/{/source/bill-imports/batch/@id}/">
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
						<br />
						<br />
						<input type="submit" value="Import" />
						<input type="reset" value="Reset" />
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