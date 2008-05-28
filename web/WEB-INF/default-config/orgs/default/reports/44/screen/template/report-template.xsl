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
					href="{/source/request/@context-path}/orgs/1/reports/9/stream/output/" />

				<title>
					<xsl:value-of select="/source/org/@name" />
					&gt; Suppliers &gt;
					<xsl:value-of
						select="/source/batches/supplier-service/supplier/@name" />
					&gt; Services &gt;
					<xsl:value-of
						select="/source/batches/supplier-service/@name" />
					&gt; Batches
				</title>
			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/{/source/batches/supplier-service/supplier/org/@id}/reports/0/screen/output/">
						<xsl:value-of
							select="/source/batches/supplier-service/supplier/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/batches/supplier-service/supplier/org/@id}/reports/35/screen/output/">
						<xsl:value-of select="'Suppliers'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/batches/supplier-service/supplier/org/@id}/reports/36/screen/output/?supplier-id={/source/batches/supplier-service/supplier/@id}">
						<xsl:value-of
							select="/source/batches/supplier-service/supplier/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/batches/supplier-service/supplier/org/@id}/reports/37/screen/output/?supplier-id={/source/batches/supplier-service/supplier/@id}">
						<xsl:value-of select="'Services'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/batches/supplier-service/supplier/org/@id}/reports/38/screen/output/?supplier-service-id={/source/batches/supplier-service/@id}">
						<xsl:value-of
							select="/source/batches/supplier-service/@name" />
					</a>
					&gt;
					<xsl:value-of select="'Batches ['" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/batches/supplier-service/supplier/org/@id}/suppliers/{/source/batches/supplier-service/supplier/@id}/services/{/source/batches/supplier-service/@id}/batches/">
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
							<th>Id</th>
							<th>Reference</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each select="/source/batches/batch">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/batches/supplier-service/supplier/org/@id}/reports/45/screen/output/?batch-id={@id}">
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