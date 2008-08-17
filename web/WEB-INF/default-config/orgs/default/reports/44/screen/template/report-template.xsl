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
					href="{/source/request/@context-path}/orgs/{/source/batches/supplier-contract/org/@id}/reports/9/stream/output/" />

				<title>
					<xsl:value-of
						select="/source/batches/supplier-contract/org/@name" />
					&gt; Supplier Contracts &gt;
					<xsl:value-of
						select="/source/batches/supplier-contract/@name" />
					&gt; Batches
				</title>
			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/{/source/batches/supplier-contract/org/@id}/reports/0/screen/output/">
						<xsl:value-of
							select="/source/batches/supplier-contract/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/batches/supplier-contract/org/@id}/reports/37/screen/output/?supplier-id={/source/batches/supplier-contract/@id}">
						<xsl:value-of select="'Supplier Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/batches/supplier-contract/org/@id}/reports/38/screen/output/?contract-id={/source/batches/supplier-contract/@id}">
						<xsl:value-of
							select="/source/batches/supplier-contract/@name" />
					</a>
					&gt;
					<xsl:value-of select="'Batches ['" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/batches/supplier-contract/org/@id}/supplier-contracts/{/source/batches/supplier-contract/@id}/batches/">
						<xsl:value-of select="'edit'" />
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

				<table>
					<caption>Batches</caption>
					<thead>
						<tr>
							<th>Chellow Id</th>
							<th>Reference</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each select="/source/batches/batch">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/batches/supplier-contract/org/@id}/reports/45/screen/output/?batch-id={@id}">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<xsl:value-of select="@reference" />
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>