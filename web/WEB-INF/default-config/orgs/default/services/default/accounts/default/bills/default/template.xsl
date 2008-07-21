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
					href="{/source/request/@context-path}/style/" />

				<title>
					Chellow &gt; Organizations &gt;
					<xsl:value-of
						select="/source/bill/account/supplier/org/@name" />
					&gt; Suppliers &gt;
					<xsl:value-of
						select="/source/bill/account/supplier/@name" />
					&gt; Accounts &gt;
					<xsl:value-of
						select="/source/bill/account/@reference" />
					&gt; Bills &gt;
					<xsl:value-of
						select="/source/bill/account/bill/@id" />
				</title>
			</head>

			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img
							src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					&gt;
					<a href="{/source/request/@context-path}/orgs/">
						<xsl:value-of select="'Organizations'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill/account/supplier/org/@id}/">
						<xsl:value-of
							select="/source/bill/account/supplier/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill/account/supplier/org/@id}/suppliers/">
						<xsl:value-of select="'Suppliers'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill/account/supplier/org/@id}/suppliers/{/source/bill/account/supplier/@id}/">
						<xsl:value-of
							select="/source/bill/account/supplier/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill/account/supplier/org/@id}/suppliers/{/source/bill/account/supplier/@id}/accounts/">
						<xsl:value-of select="'Accounts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill/account/supplier/org/@id}/suppliers/{/source/bill/account/supplier/@id}/accounts/{/source/bill/account/@id}/">
						<xsl:value-of
							select="/source/bill/account/@reference" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill/account/supplier/org/@id}/suppliers/{/source/bill/account/supplier/@id}/accounts/{/source/bill/account/@id}/bills/">
						<xsl:value-of select="'Bills'" />
					</a>
					&gt;
					<xsl:value-of
						select="concat(/source/bill/@id, ' [')" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill/account/supplier/org/@id}/reports/43/screen/output/?bill-id={/source/bill/@id}">
						<xsl:value-of select="'view'" />
					</a>
					<xsl:value-of select="']'" />
				</p>
				<xsl:if test="//message">
					<ul>
						<xsl:for-each select="//message">
							<li>
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>
				<br />
				<ul>
					<li>
						<xsl:value-of
							select="concat('From ', /source/bill/day-start-date/@year, '-', /source/bill/day-start-date/@month, '-', /source/bill/day-start-date/@day)" />
					</li>
					<li>
						<xsl:value-of
							select="concat('To ', /source/bill/day-finish-date/@year, '-', /source/bill/day-finish-date/@month, '-', /source/bill/day-finish-date/@day)" />
					</li>
					<li>
						<xsl:value-of
							select="concat('Net ', /source/bill/@net)" />
					</li>
					<li>
						<xsl:value-of
							select="concat('VAT ', /source/bill/@vat)" />
					</li>
				</ul>

				<table>
					<caption>Invoices</caption>
					<thead>
						<tr>
							<th>Chellow Id</th>
							<th>Batch</th>
							<th>From</th>
							<th>To</th>
							<th>Net</th>
							<th>VAT</th>
							<th>Invoice Number</th>
							<th>Account Text</th>
							<th>MPAN text</th>
							<th>Status</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each select="/source/bill/invoice">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/bill/account/supplier/org/@id}/suppliers/{/source/bill/account/supplier/@id}/services/{batch/supplier-service/@id}/batches/{batch/@id}/invoices/{@id}/">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/bill/account/supplier/org/@id}/suppliers/{/source/bill/account/supplier/@id}/services/{batch/supplier-service/@id}/batches/{batch/@id}/">
										<xsl:value-of
											select="batch/@reference" />
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
									<xsl:value-of
										select="@invoice-text" />
								</td>
								<td>
									<xsl:value-of
										select="@account-text" />
								</td>
								<td>
									<xsl:value-of select="@mpan-text" />
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