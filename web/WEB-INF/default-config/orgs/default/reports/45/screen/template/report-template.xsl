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
					<xsl:value-of
						select="/source/batch/supplier-service/supplier/org/@name" />
					&gt; Suppliers &gt;
					<xsl:value-of
						select="/source/batch/supplier-service/supplier/@name" />
					&gt; Services &gt;
					<xsl:value-of
						select="/source/batch/supplier-service/@name" />
					&gt; Batches &gt;
					<xsl:value-of select="/source/batch/@reference" />
				</title>
			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/{/source/batch/supplier-service/supplier/org/@id}/reports/0/screen/output/">
						<xsl:value-of
							select="/source/batch/supplier-service/supplier/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/batch/supplier-service/supplier/org/@id}/reports/35/screen/output/">
						<xsl:value-of select="'Suppliers'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/batch/supplier-service/supplier/org/@id}/reports/36/screen/output/?supplier-id={/source/batch/supplier-service/supplier/@id}">
						<xsl:value-of
							select="/source/batch/supplier-service/supplier/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/batch/supplier-service/supplier/org/@id}/reports/37/screen/output/?supplier-id={/source/batch/supplier-service/supplier/@id}">
						<xsl:value-of select="'Services'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/batch/supplier-service/supplier/org/@id}/reports/38/screen/output/?supplier-service-id={/source/batch/supplier-service/@id}">
						<xsl:value-of
							select="/source/batch/supplier-service/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/batch/supplier-service/supplier/org/@id}/reports/44/screen/output/?supplier-service-id={/source/batch/supplier-service/@id}">
						<xsl:value-of select="'Batches'" />
					</a>
					&gt;
					<xsl:value-of select="/source/batch/@reference" />
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
							<th>Id</th>
							<th>Bill</th>
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
						<xsl:for-each select="/source/batch/invoice">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/batch/supplier-service/supplier/org/@id}/reports/46/screen/output/?invoice-id={@id}">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/batch/supplier-service/supplier/org/@id}/reports/43/screen/output/?bill-id={bill/@id}">
										<xsl:value-of select="bill/@id" />
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