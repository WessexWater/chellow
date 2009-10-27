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
					href="{/source/request/@context-path}/style/" />
				<title>
					Chellow &gt; Supplier Contracts &gt;
					<xsl:value-of select="/source/bills/batch/supplier-contract/@name" />
					&gt; Batches &gt;
					<xsl:value-of select="/source/bills/batch/@name" />
					&gt; bills
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
						<img src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					&gt;
					<a href="{/source/request/@context-path}/supplier-contracts/">
						<xsl:value-of select="'Supplier Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplier-contracts/{/source/bills/batch/supplier-contract/@id}/">
						<xsl:value-of select="/source/bills/batch/supplier-contract/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplier-contracts/{/source/bills/batch/supplier-contract/@id}/batches/">
						<xsl:value-of select="'Batches'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplier-contracts/{/source/bills/batch/supplier-contract/@id}/batches/{/source/bills/batch/@id}/">
						<xsl:value-of select="/source/bills/batch/@reference" />
					</a>
					&gt;
					<xsl:value-of select="'Bills'" />
				</p>
				<br />
				<table>
					<caption>Bills</caption>
					<thead>
						<tr>
							<th>Chellow Id</th>
							<th>Reference</th>
							<th>From</th>
							<th>To</th>
							<th>Net</th>
							<th>VAT</th>
							<th>Type</th>
							<th>Is Cancelled Out?</th>
							<th>Status</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each select="/source/bills/bill">
							<tr>
								<td>
									<a href="{@id}/">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<xsl:value-of select="@reference" />
								</td>
								<td>
									<xsl:value-of
										select="concat(hh-end-date/@year, '-', hh-end-date/@month, '-', hh-end-date/@day)" />
								</td>
								<td>
									<xsl:value-of
										select="concat(hh-end-date/@year, '-', hh-end-date/@month, '-', hh-end-date/@day)" />
								</td>
								<td>
									<xsl:value-of select="@net" />
								</td>
								<td>
									<xsl:value-of select="@vat" />
								</td>
								<td>
									<xsl:value-of select="@type" />
								</td>
								<td>
									<xsl:if test="@is-cancelled-out='true'">
										Cancelled Out
									</xsl:if>
								</td>
								<td>
									<xsl:choose>
										<xsl:when test="not(@is-paid)">
											Pending
										</xsl:when>
										<xsl:when test="@is-paid='true'">
											Paid
										</xsl:when>
										<xsl:when test="@is-paid='false'">
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
						<legend>Add a bill</legend>
						<input type="submit" value="Add" />
						<input type="reset" value="Reset" />
					</fieldset>
				</form>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>