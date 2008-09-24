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
					href="{/source/request/@context-path}/orgs/{/source/account/supplier-contract/org/@id}/reports/9/stream/output/" />

				<title>
					<xsl:value-of
						select="/source/account/supplier-contract/org/@name" />
					&gt; Supplier Contracts &gt;
					<xsl:value-of
						select="/source/account/supplier-contract/@name" />
					&gt; Account: 
					<xsl:value-of select="/source/account/@reference" />
				</title>
			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/{/source/account/supplier-contract/org/@id}/reports/0/screen/output/">
						<xsl:value-of
							select="/source/account/supplier-contract/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/account/supplier-contract/org/@id}/reports/37/screen/output/">
						<xsl:value-of select="'Supplier Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/account/supplier-contract/org/@id}/reports/38/screen/output/?supplier-contract-id={/source/account/supplier-contract/@id}">
						<xsl:value-of
							select="/source/account/supplier-contract/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/account/supplier-contract/org/@id}/reports/40/screen/output/?supplier-contract-id={/source/account/supplier-contract/@id}">
						<xsl:value-of
							select="'Accounts'" />
					</a>
&gt;					
					<xsl:value-of
						select="concat(/source/account/@reference , ' [')" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/account/supplier-contract/org/@id}/supplier-contracts/{/source/account/supplier-contract/@id}/accounts/{/source/account/@id}/">
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
					<tbody>
						<tr>
							<th>Chellow Id</th>
							<td>
								<xsl:value-of
									select="/source/account/@id" />
							</td>
						</tr>
						<tr>
							<th>Reference</th>
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
							href="{/source/request/@context-path}/orgs/{/source/account/supplier-contract/org/@id}/reports/42/screen/output/?account-id={/source/account/@id}">
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
										href="{/source/request/@context-path}/orgs/{/source/account/supplier-contract/org/@id}/reports/15/screen/output/?supply-generation-id={supply-generation[@label='start']/@id}">
										<xsl:value-of
											select="'Supply Generation'" />
									</a>
								</td>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/account/supplier-contract/org/@id}/reports/15/screen/output/?supply-generation-id={supply-generation[@label='finish']/@id}">
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