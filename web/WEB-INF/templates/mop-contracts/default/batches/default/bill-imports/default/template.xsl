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
					href="{/source/request/@context-path}/reports/19/output/" />
				<style>
					table { width: 300em; }

					caption { text-align: left; }
				</style>
				<title>
					Chellow &gt; MOP Contracts &gt;
					<xsl:value-of select="/source/bill-import/batch/mop-contract/@name" />
					&gt; Batches &gt;
					<xsl:value-of select="/source/bill-import/batch/@reference" />
					&gt; Bill Imports &gt;
					<xsl:value-of select="/source/bill-import/@id" />
				</title>
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					&gt;
					<a href="{/source/request/@context-path}/mop-contracts/">
						<xsl:value-of select="'MOP Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/mop-contracts/{/source/bill-import/batch/mop-contract/@id}/">
						<xsl:value-of select="/source/bill-import/batch/mop-contract/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/mop-contracts/{/source/bill-import/batch/mop-contract/@id}/batches/">
						<xsl:value-of select="'Batches'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/mop-contracts/{/source/bill-import/batch/mop-contract/@id}/batches/{/source/bill-import/batch/@id}/">
						<xsl:value-of select="/source/bill-import/batch/@reference" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/mop-contracts/{/source/bill-import/batch/mop-contract/@id}/batches/{/source/bill-import/batch/@id}/bill-imports/">
						<xsl:value-of select="'Bill Imports'" />
					</a>
					&gt;
					<xsl:value-of select="/source/bill-import/@id" />
				</p>
				<br />
				<xsl:if test="//message[not(../../raw-bill)]">
					<ul>
						<xsl:for-each select="//message[not(../../raw-bill)]">
							<li>
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>
				<p>
					<xsl:value-of select="/source/bill-import/@progress" />
				</p>
				<xsl:if test="/source/bill-import/failed-bills/raw-bill">
					<table>
						<caption>Bills that failed to load</caption>
						<thead>
							<tr>
								<th>Problem</th>
								<th>Reference</th>
								<th>Account Reference</th>
								<th>MPANs</th>
								<th>Issue Date</th>
								<th>Start Date</th>
								<th>Finish Date</th>
								<th>kWh</th>
								<th>Net</th>
								<th>VAT</th>
								<th>Type</th>
								<th>Breakdown</th>
								<th>R1 MPAN</th>
								<th>R1 Meter Serial Number</th>
								<th>R1 Coefficient</th>
								<th>R1 Units</th>
								<th>R1 TPR</th>
								<th>R1 Previous Read Date</th>
								<th>R1 Previous Read Value</th>
								<th>R1 Previous Read Type</th>
								<th>R1 Present Read Date</th>
								<th>R1 Present Read Value</th>
								<th>R1 Present Read Type</th>
								<th>R2 MPAN</th>
								<th>R2 Meter Serial Number</th>
								<th>R2 Coefficient</th>
								<th>R2 Units</th>
								<th>R2 TPR</th>
								<th>R2 Previous Read Date</th>
								<th>R2 Previous Read Value</th>
								<th>R2 Previous Read Type</th>
								<th>R2 Present Read Date</th>
								<th>R2 Present Read Value</th>
								<th>R2 Present Read Type</th>
								<th>R3 MPAN</th>
								<th>R3 Meter Serial Number</th>
								<th>R3 Coefficient</th>
								<th>R3 Units</th>
								<th>R3 TPR</th>
								<th>R3 Previous Read Date</th>
								<th>R3 Previous Read Value</th>
								<th>R3 Previous Read Type</th>
								<th>R3 Present Read Date</th>
								<th>R3 Present Read Value</th>
								<th>R3 Present Read Type</th>
								<th>R4 MPAN</th>
								<th>R4 Meter Serial Number</th>
								<th>R4 Coefficient</th>
								<th>R4 Units</th>
								<th>R4 TPR</th>
								<th>R4 Previous Read Date</th>
								<th>R4 Previous Read Value</th>
								<th>R4 Previous Read Type</th>
								<th>R4 Present Read Date</th>
								<th>R4 Present Read Value</th>
								<th>R4 Present Read Type</th>
							</tr>
							<col class="problem" />
						</thead>
						<tbody>
							<xsl:for-each select="/source/bill-import/failed-bills/raw-bill">
								<tr>
									<td>
										<xsl:value-of select="message/@description" />
									</td>
									<td>
										<xsl:value-of select="@reference" />
									</td>
									<td>
										<xsl:value-of select="@account-reference" />
									</td>
									<td>
										<xsl:value-of select="@mpans" />
									</td>
									<td>
										<xsl:value-of
											select="concat(date[@label='issue']/@year, '-', date[@label='issue']/@month, '-', date[@label='issue']/@day)" />
									</td>
									<td>
										<xsl:value-of
											select="concat(hh-start-date[@label='start']/@year, '-', hh-start-date[@label='start']/@month, '-', hh-start-date[@label='start']/@day)" />
									</td>
									<td>
										<xsl:value-of
											select="concat(hh-start-date[@label='finish']/@year, '-', hh-start-date[@label='finish']/@month, '-', hh-start-date[@label='finish']/@day)" />
									</td>
									<td>
										<xsl:value-of select="@kwh" />
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
										<xsl:value-of select="@breakdown" />
									</td>
									<xsl:for-each select="raw-register-read">
										<td>
											<xsl:value-of select="@mpan" />
										</td>
										<td>
											<xsl:value-of select="@meter-serial-number" />
										</td>
										<td>
											<xsl:value-of select="@coefficient" />
										</td>
										<td>
											<xsl:value-of select="@units" />
										</td>
										<td>
											<xsl:value-of select="@tpr" />
										</td>
										<td>
											<xsl:value-of
												select="concat(hh-start-date[@label='previous']/@year, '-', hh-start-date[@label='previous']/@month, '-', hh-start-date[@label='previous']/@day)" />
										</td>
										<td>
											<xsl:value-of select="@previous-value" />
										</td>
										<td>
											<xsl:value-of select="read-type[@label='previous']/@code" />
										</td>
										<td>
											<xsl:value-of
												select="concat(hh-start-date[@label='present']/@year, '-', hh-start-date[@label='present']/@month, '-', hh-start-date[@label='present']/@day)" />
										</td>
										<td>
											<xsl:value-of select="@present-value" />
										</td>
										<td>
											<xsl:value-of select="read-type[@label='present']/@code" />
										</td>
									</xsl:for-each>
								</tr>
							</xsl:for-each>
						</tbody>
					</table>
				</xsl:if>
				<xsl:if test="/source/bill-import/successful-bills/raw-bill">
					<br />
					<br />
					<table>
						<caption>
							Bills that loaded successfully
						</caption>
						<thead>
							<tr>
								<th>Reference</th>
								<th>Account Reference</th>
								<th>MPANs</th>
								<th>Issue Date</th>
								<th>Start Date</th>
								<th>Finish Date</th>
								<th>kWh</th>
								<th>Net</th>
								<th>VAT</th>
								<th>Type</th>
								<th>Breakdown</th>
								<th>R1 MPAN</th>
								<th>R1 Meter Serial Number</th>
								<th>R1 Coefficient</th>
								<th>R1 Units</th>
								<th>R1 TPR</th>
								<th>R1 Previous Read Date</th>
								<th>R1 Previous Read Value</th>
								<th>R1 Previous Read Type</th>
								<th>R1 Present Read Date</th>
								<th>R1 Present Read Value</th>
								<th>R1 Present Read Type</th>
								<th>R2 MPAN</th>
								<th>R2 Meter Serial Number</th>
								<th>R2 Coefficient</th>
								<th>R2 Units</th>
								<th>R2 TPR</th>
								<th>R2 Previous Read Date</th>
								<th>R2 Previous Read Value</th>
								<th>R2 Previous Read Type</th>
								<th>R2 Present Read Date</th>
								<th>R2 Present Read Value</th>
								<th>R2 Present Read Type</th>
								<th>R3 MPAN</th>
								<th>R3 Meter Serial Number</th>
								<th>R3 Coefficient</th>
								<th>R3 Units</th>
								<th>R3 TPR</th>
								<th>R3 Previous Read Date</th>
								<th>R3 Previous Read Value</th>
								<th>R3 Previous Read Type</th>
								<th>R3 Present Read Date</th>
								<th>R3 Present Read Value</th>
								<th>R3 Present Read Type</th>
								<th>R4 MPAN</th>
								<th>R4 Meter Serial Number</th>
								<th>R4 Coefficient</th>
								<th>R4 Units</th>
								<th>R4 TPR</th>
								<th>R4 Previous Read Date</th>
								<th>R4 Previous Read Value</th>
								<th>R4 Previous Read Type</th>
								<th>R4 Present Read Date</th>
								<th>R4 Present Read Value</th>
								<th>R4 Present Read Type</th>
							</tr>
						</thead>
						<tbody>
							<xsl:for-each select="/source/bill-import/successful-bills/raw-bill">
								<tr>
									<td>
										<xsl:value-of select="@reference" />
									</td>
									<td>
										<xsl:value-of select="@account-reference" />
									</td>
									<td>
										<xsl:value-of select="@mpans" />
									</td>
									<td>
										<xsl:value-of
											select="concat(date[@label='issue']/@year, '-', date[@label='issue']/@month, '-', date[@label='issue']/@day)" />
									</td>
									<td>
										<xsl:value-of
											select="concat(hh-start-date[@label='start']/@year, '-', hh-start-date[@label='start']/@month, '-', hh-start-date[@label='start']/@day)" />
									</td>
									<td>
										<xsl:value-of
											select="concat(hh-start-date[@label='finish']/@year, '-', hh-start-date[@label='finish']/@month, '-', hh-start-date[@label='finish']/@day)" />
									</td>
									<td>
										<xsl:value-of select="@kwh" />
									</td>
									<td>
										<xsl:value-of select="@net" />
									</td>
									<td>
										<xsl:value-of select="@vat" />
									</td>
									<td>
										<xsl:value-of select="bill-type/@code" />
									</td>
									<td>
										<xsl:value-of select="@breakdown" />
									</td>
									<xsl:for-each select="raw-register-read">
										<td>
											<xsl:value-of select="@mpan" />
										</td>
										<td>
											<xsl:value-of select="@meter-serial-number" />
										</td>
										<td>
											<xsl:value-of select="tpr/@code" />
										</td>
										<td>
											<xsl:value-of select="@coefficient" />
										</td>
										<td>
											<xsl:value-of select="@units" />
										</td>
										<td>
											<xsl:value-of
												select="concat(hh-start-date[@label='previous']/@year, '-', hh-start-date[@label='previous']/@month, '-', hh-start-date[@label='previous']/@day)" />
										</td>
										<td>
											<xsl:value-of select="@previous-value" />
										</td>
										<td>
											<xsl:value-of select="read-type[@label='previous']/@code" />
										</td>
										<td>
											<xsl:value-of
												select="concat(hh-start-date[@label='present']/@year, '-', hh-start-date[@label='present']/@month, '-', hh-start-date[@label='present']/@day)" />
										</td>
										<td>
											<xsl:value-of select="@present-value" />
										</td>
										<td>
											<xsl:value-of select="read-type[@label='present']/@code" />
										</td>
									</xsl:for-each>
								</tr>
							</xsl:for-each>
						</tbody>
					</table>
				</xsl:if>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>