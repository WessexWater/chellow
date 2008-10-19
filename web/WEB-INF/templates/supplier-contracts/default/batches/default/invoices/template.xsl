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
					Chellow &gt; Supplier Contracts &gt;
					<xsl:value-of
						select="/source/invoices/batch/supplier-contract/@name" />
					&gt; Batches &gt;
					<xsl:value-of select="/source/invoices/batch/@name" />
					&gt; Invoices
				</title>
			</head>
			<body>
				<xsl:if test="//message">
					<ul>
						<xsl:for-each select="//message">
							<li>
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>
				<p>
					<a href="{/source/request/@context-path}/">
						<img
							src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplier-contracts/">
						<xsl:value-of select="'Supplier Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplier-contracts/{/source/invoices/batch/supplier-contract/@id}/">
						<xsl:value-of
							select="/source/invoices/batch/supplier-contract/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplier-contracts/{/source/invoices/batch/supplier-contract/@id}/batches/">
						<xsl:value-of select="'Batches'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplier-contracts/{/source/invoices/batch/supplier-contract/@id}/batches/{/source/invoices/batch/@id}/">
						<xsl:value-of
							select="/source/invoices/batch/@reference" />
					</a>
					&gt;
					<xsl:value-of select="'Invoices'" />
				</p>
				<br />
				<xsl:choose>
					<xsl:when
						test="/source/response/@status-code = '201'">
						<p>
							The
							<a
								href="{/source/response/header[@name = 'Location']/@value}">
								<xsl:value-of select="'new invoice'" />
							</a>
							has been successfully created.
						</p>
					</xsl:when>
					<xsl:otherwise>
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
								<xsl:for-each
									select="/source/invoices/invoice">
									<tr>
										<td>
											<a href="{@id}/">
												<xsl:value-of
													select="@id" />
											</a>
										</td>
										<td>
											<xsl:value-of
												select="@reference" />
										</td>

										<td>
											<a
												href="{/source/request/@context-path}/suppliers/{/source/invoices/batch/supplier-contract/@id}/accounts/{bill/account/@id}/bills/{bill/@id}/">
												<xsl:value-of
													select="bill/@id" />
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
												<xsl:when
													test="@status='0'">
													Pending
												</xsl:when>
												<xsl:when
													test="@status='1'">
													Paid
												</xsl:when>
												<xsl:when
													test="@status='2'">
													Rejected
												</xsl:when>
											</xsl:choose>
										</td>
									</tr>
								</xsl:for-each>
							</tbody>
						</table>
						<br />
						<form action="." method="post">
							<fieldset>
								<legend>Add an invoice</legend>
								<input type="submit" value="Add" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>