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
						select="/source/account/supplier/@name" />
					&gt; Accounts &gt;
					<xsl:value-of select="/source/account/@reference" />
				</title>
			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/0/screen/output/">
						<xsl:value-of select="/source/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/35/screen/output/">
						<xsl:value-of select="'Suppliers'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/36/screen/output/?supplier-id={/source/account/supplier/@id}">
						<xsl:value-of
							select="/source/account/supplier/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/40/screen/output/?supplier-id={/source/account/supplier/@id}">
						<xsl:value-of select="'Accounts'" />
					</a>
					&gt;
					<xsl:value-of select="/source/account/@reference" />
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
					<caption>Properties</caption>
					<thead>
						<tr>
							<th>Name</th>
							<th>Value</th>
						</tr>
					</thead>
					<tbody>
						<tr>
							<td>Id</td>
							<td>
								<xsl:value-of
									select="/source/account/@id" />
							</td>
						</tr>
						<tr>
							<td>Reference</td>
							<td>
								<xsl:value-of
									select="/source/account/@reference" />
							</td>
						</tr>
					</tbody>
				</table>

				<ul>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/42/screen/output/?account-id={/source/account/@id}">
							Bills
						</a>
					</li>
				</ul>

				<table>
					<caption>MPANs</caption>
					<thead>
						<tr>
							<th rowspan="2">MPAN Core</th>
							<th colspan="2">Supply Generations</th>
						</tr>
						<tr>
							<th>From</th>
							<th>To</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each select="/source/account/item">
							<tr>
								<td>
									<xsl:value-of
										select="mpan-core/@core" />
								</td>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/15/screen/output/?supply-generation-id={supply-generation[@label='start']/@id}">
										<xsl:value-of
											select="'Supply Generation'" />
									</a>
								</td>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/15/screen/output/?supply-generation-id={supply-generation[@label='finish']/@id}">
										<xsl:value-of
											select="'Supply Generation'" />
									</a>
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>