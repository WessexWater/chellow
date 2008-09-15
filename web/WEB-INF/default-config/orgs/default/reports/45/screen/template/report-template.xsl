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
					href="{/source/request/@context-path}/orgs/{/source/batch/supplier-contract/org/@id}/reports/9/stream/output/" />

				<title>
					<xsl:value-of
						select="/source/batch/supplier-contract/org/@name" />
					&gt; Supplier Contracts &gt;
					<xsl:value-of
						select="/source/batch/supplier-contract/@name" />
					&gt; Batches &gt;
					<xsl:value-of select="/source/batch/@reference" />
				</title>
			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/{/source/batch/supplier-contract/org/@id}/reports/0/screen/output/">
						<xsl:value-of
							select="/source/batch/supplier-contract/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/batch/supplier-contract/org/@id}/reports/37/screen/output/">
						<xsl:value-of select="'Supplier Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/batch/supplier-contract/org/@id}/reports/38/screen/output/?supplier-contract-id={/source/batch/supplier-contract/@id}">
						<xsl:value-of
							select="/source/batch/supplier-contract/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/batch/supplier-contract/org/@id}/reports/44/screen/output/?supplier-contract-id={/source/batch/supplier-contract/@id}">
						<xsl:value-of select="'Batches'" />
					</a>
					&gt;
					<xsl:value-of
						select="concat(/source/batch/@reference, ' [')" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/batch/supplier-contract/org/@id}/supplier-contracts/{/source/batch/supplier-contract/@id}/batches/{/source/batch/@id}/">
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
					<caption>Invoices</caption>
					<thead>
						<tr>
							<th>Chellow Id</th>
							<th>Reference</th>
							<th>Bill</th>
							<th>From</th>
							<th>To</th>
							<th>Net</th>
							<th>VAT</th>
							<th>Status</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each select="/source/batch/invoice">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/batch/supplier-contract/org/@id}/reports/46/screen/output/?invoice-id={@id}">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<xsl:value-of select="@reference" />
								</td>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/batch/supplier-contract/org/@id}/reports/43/screen/output/?bill-id={bill/@id}">
										<xsl:value-of select="bill/@id" />
									</a>
									<xsl:value-of select="' &gt; '" />
									<a
										href="{/source/request/@context-path}/orgs/{/source/batch/supplier-contract/org/@id}/reports/41/screen/output/?account-id={bill/account/@id}">
										<xsl:value-of
											select="bill/account/@reference" />
									</a>
								</td>
								<td>
									<xsl:value-of
										select="concat(day-start-date/@year, '-', day-start-date/@month, '-', day-start-date/@day)" />
								</td>
								<td>
									<xsl:value-of
										select="concat(day-finish-date/@year, '-', day-finish-date/@month, '-', day-finish-date/@day)" />
								</td>
								<td>
									<xsl:value-of select="@net" />
								</td>
								<td>
									<xsl:value-of select="@vat" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when test="@status='0'">
											Pending
										</xsl:when>
										<xsl:when test="@status='1'">
											Paid
										</xsl:when>
										<xsl:when test="@status='2'">
											Rejected
										</xsl:when>
									</xsl:choose>
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>