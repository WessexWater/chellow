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
					href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-contract/org/@id}/reports/9/stream/output/" />
				<title>
					<xsl:value-of
						select="/source/invoice/batch/supplier-contract/org/@name" />
					&gt; Supplier Contracts &gt;
					<xsl:value-of
						select="/source/invoice/batch/supplier-contract/@name" />
					&gt; Batches &gt;
					<xsl:value-of
						select="/source/invoice/batch/@reference" />
					&gt; Invoice:
					<xsl:value-of select="/source/invoice/@id" />
				</title>
			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-contract/org/@id}/reports/0/screen/output/">
						<xsl:value-of
							select="/source/invoice/batch/supplier-contract/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-contract/org/@id}/reports/37/screen/output/">
						<xsl:value-of select="'Supplier Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-contract/org/@id}/reports/38/screen/output/?supplier-contract-id={/source/invoice/batch/supplier-contract/@id}">
						<xsl:value-of
							select="/source/invoice/batch/supplier-contract/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-contract/org/@id}/reports/44/screen/output/?supplier-contract-id={/source/invoice/batch/supplier-contract/@id}">
						<xsl:value-of select="'Batches'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-contract/org/@id}/reports/45/screen/output/?batch-id={/source/invoice/batch/@id}">
						<xsl:value-of
							select="/source/invoice/batch/@reference" />
					</a>
					&gt; Invoice:
					<xsl:value-of
						select="concat(/source/invoice/@id, ' [')" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-contract/org/@id}/supplier-contracts/{/source/invoice/batch/supplier-contract/@id}/batches/{/source/invoice/batch/@id}/invoices/{/source/invoice/@id}/">
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
					<tr>
						<th>Chellow Id</th>
						<td>
							<xsl:value-of select="/source/invoice/@id" />
						</td>
					</tr>
					<tr>
						<th>Reference</th>
						<td>
							<xsl:value-of
								select="/source/invoice/@reference" />
						</td>
					</tr>
					<tr>
						<th>Bill</th>
						<td>
							<a
								href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-contract/org/@id}/reports/43/screen/output/?bill-id={/source/invoice/bill/@id}">
								<xsl:value-of select="/source/invoice/bill/@id" />
							</a>
							<xsl:value-of select="' &lt; '" />
							<a
								href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-contract/org/@id}/reports/42/screen/output/?account-id={/source/invoice/bill/account/@id}">
								<xsl:value-of select="'Bills'" />
							</a>
							&lt;
							<a
								href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-contract/org/@id}/reports/41/screen/output/?account-id={/source/invoice/bill/account/@id}">
								<xsl:value-of
									select="/source/invoice/bill/account/@reference" />
							</a>
							&lt;
							<a
								href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-contract/org/@id}/reports/40/screen/output/?supplier-contract-id={/source/invoice/batch/supplier-contract/@id}">
								<xsl:value-of select="'Accounts'" />
							</a>
							&lt;
							<a
								href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-contract/org/@id}/reports/38/screen/output/?supplier-contract-id={/source/invoice/batch/supplier-contract/@id}">
								<xsl:value-of
									select="/source/invoice/batch/supplier-contract/@name" />
							</a>
						</td>
					</tr>
					<tr>
						<th>Issue Date</th>
						<td>
							<xsl:value-of
								select="concat(/source/invoice/day-start-date[@label='issue']/@year, '-', /source/invoice/day-start-date[@label='issue']/@month, '-', /source/invoice/day-start-date[@label='issue']/@day)" />
						</td>
					</tr>
					<tr>
						<th>Start Date</th>
						<td>
							<xsl:value-of
								select="concat(/source/invoice/day-start-date/@year, '-', /source/invoice/day-start-date/@month, '-', /source/invoice/day-start-date/@day)" />
						</td>
					</tr>
					<tr>
						<th>Finish Date</th>
						<td>
							<xsl:value-of
								select="concat(/source/invoice/day-finish-date/@year, '-', /source/invoice/day-finish-date/@month, '-', /source/invoice/day-finish-date/@day)" />
						</td>
					</tr>
					<tr>
						<th>Net</th>
						<td>
							<xsl:value-of select="/source/invoice/@net" />
						</td>
					</tr>
					<tr>
						<th>VAT</th>
						<td>
							<xsl:value-of select="/source/invoice/@vat" />
						</td>
					</tr>
					<tr>
						<th>Status</th>
						<td>
							<xsl:choose>
								<xsl:when
									test="/source/invoice/@status = 0">
									<xsl:value-of select="'Pending'" />
								</xsl:when>
								<xsl:when
									test="/source/invoice/@status = 1">
									<xsl:value-of select="'Paid'" />
								</xsl:when>
								<xsl:when
									test="/source/invoice/@status = 2">
									<xsl:value-of select="'Rejected'" />
								</xsl:when>
							</xsl:choose>
						</td>
					</tr>
				</table>
				<br />
				<table>
					<caption>Register Reads</caption>
					<thead>
						<tr>
							<th>MPAN</th>
							<th>Coefficient</th>
							<th>Units</th>
							<th>TPR</th>
							<th>Previous Date</th>
							<th>Previous Value</th>
							<th>Previous Type</th>
							<th>Present Date</th>
							<th>Present Value</th>
							<th>Present Type</th>
						</tr>
					</thead>
					<xsl:for-each
						select="/source/invoice/register-read">
						<tr>
							<td>
								<a
									href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-contract/org/@id}/reports/15/screen/output/?supply-generation-id={mpan/supply-generation/@id}">
									<xsl:value-of
										select="mpan/mpan-core/@core" />
								</a>
							</td>
							<td>
								<xsl:value-of select="@coefficient" />
							</td>
							<td>
								<xsl:value-of select="@units" />
							</td>
							<td>
								<a
									href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-contract/org/@id}/reports/48/screen/output/?tpr-id={tpr/@id}">
									<xsl:value-of select="tpr/@code" />
								</a>
							</td>
							<td>
								<xsl:value-of
									select="concat(day-finish-date[@label='previous']/@year, '-', day-finish-date[@label='previous']/@month, '-', day-finish-date[@label='previous']/@day)" />
							</td>
							<td>
								<xsl:value-of select="@previous-value" />
							</td>
							<td>
								<xsl:value-of
									select="read-type[@label='previous']/@code" />
							</td>
							<td>
								<xsl:value-of
									select="concat(day-finish-date[@label='present']/@year, '-', day-finish-date[@label='present']/@month, '-', day-finish-date[@label='present']/@day)" />
							</td>
							<td>
								<xsl:value-of select="@present-value" />
							</td>
							<td>
								<xsl:value-of
									select="read-type[@label='present']/@code" />
							</td>
						</tr>
					</xsl:for-each>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>