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
					href="{/source/request/@context-path}/orgs/{/source/invoice-import/batch/supplier-contract/org/@id}/reports/9/stream/output/" />
				<style>
					table { width: 300em; }

					caption { text-align: left; }
				</style>
				<title>
					Chellow &gt; Organizations &gt;
					<xsl:value-of
						select="/source/invoice-import/batch/supplier-contract/org/@name" />
					&gt; Supplier Contracts &gt;
					<xsl:value-of
						select="/source/invoice-import/batch/supplier-contract/@name" />
					&gt; Batches &gt;
					<xsl:value-of
						select="/source/invoice-import/batch/@reference" />
					&gt; Invoice Imports &gt;
					<xsl:value-of select="/source/invoice-import/@id" />
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
						href="{/source/request/@context-path}/orgs/{/source/invoice-import/batch/supplier-contract/org/@id}/">
						<xsl:value-of
							select="/source/invoice-import/batch/supplier-contract/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice-import/batch/supplier-contract/org/@id}/supplier-contracts/">
						<xsl:value-of select="'Supplier Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice-import/batch/supplier-contract/org/@id}/supplier-contracts/{/source/invoice-import/batch/supplier-contract/@id}/">
						<xsl:value-of
							select="/source/invoice-import/batch/supplier-contract/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice-import/batch/supplier-contract/org/@id}/supplier-contracts/{/source/invoice-import/batch/supplier-contract/@id}/batches/">
						<xsl:value-of select="'Batches'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice-import/batch/supplier-contract/org/@id}/supplier-contracts/{/source/invoice-import/batch/supplier-contract/@id}/batches/{/source/invoice-import/batch/@id}/">
						<xsl:value-of
							select="/source/invoice-import/batch/@reference" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice-import/batch/supplier-contract/org/@id}/supplier-contracts/{/source/invoice-import/batch/supplier-contract/@id}/batches/{/source/invoice-import/batch/@id}/invoice-imports/">
						<xsl:value-of select="'Invoice Imports'" />
					</a>
					&gt;
					<xsl:value-of select="/source/invoice-import/@id" />
				</p>
				<br />
				<xsl:if test="//message[not(../../invoice-raw)]">
					<ul>
						<xsl:for-each
							select="//message[not(../../invoice-raw)]">
							<li>
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>
				<p>
					<xsl:value-of
						select="/source/invoice-import/@progress" />
				</p>
				<xsl:if
					test="/source/invoice-import/failed-invoices/invoice-raw">
					<table>
						<caption>Invoices that failed to load</caption>
						<thead>
							<tr>
								<th>Problem</th>
								<th>Reference</th>
								<th>Account Reference</th>
								<th>MPAN Text</th>
								<th>Issue Date</th>
								<th>Start Date</th>
								<th>Finish Date</th>
								<th>Net</th>
								<th>VAT</th>
								<th>R1 MPAN</th>
								<th>R1 Meter Serial Number</th>
								<th>R1 TPR</th>
								<th>R1 Coefficient</th>
								<th>R1 Units</th>
								<th>R1 Previous Read Date</th>
								<th>R1 Previous Read Value</th>
								<th>R1 Previous Read Type</th>
								<th>R1 Present Read Date</th>
								<th>R1 Present Read Value</th>
								<th>R1 Present Read Type</th>
								<th>R2 MPAN</th>
								<th>R2 Meter Serial Number</th>
								<th>R2 TPR</th>
								<th>R2 Coefficient</th>
								<th>R2 Units</th>
								<th>R2 Previous Read Date</th>
								<th>R2 Previous Read Value</th>
								<th>R2 Previous Read Type</th>
								<th>R2 Present Read Date</th>
								<th>R2 Present Read Value</th>
								<th>R2 Present Read Type</th>
								<th>R3 MPAN</th>
								<th>R3 Meter Serial Number</th>
								<th>R3 TPR</th>
								<th>R3 Coefficient</th>
								<th>R3 Units</th>
								<th>R3 Previous Read Date</th>
								<th>R3 Previous Read Value</th>
								<th>R3 Previous Read Type</th>
								<th>R3 Present Read Date</th>
								<th>R3 Present Read Value</th>
								<th>R3 Present Read Type</th>
								<th>R4 MPAN</th>
								<th>R4 Meter Serial Number</th>
								<th>R4 TPR</th>
								<th>R4 Coefficient</th>
								<th>R4 Units</th>
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
							<xsl:for-each
								select="/source/invoice-import/failed-invoices/invoice-raw">
								<tr>
									<td>
										<xsl:value-of
											select="message/@description" />
									</td>
									<td>
										<xsl:value-of
											select="@reference" />
									</td>
									<td>
										<xsl:value-of
											select="@account-reference" />
									</td>
									<td>
										<xsl:value-of
											select="@mpan-text" />
									</td>
									<td>
										<xsl:value-of
											select="concat(day-start-date[@label='issue']/@year, '-', day-start-date[@label='issue']/@month, '-', day-start-date[@label='issue']/@day)" />
									</td>
									<td>
										<xsl:value-of
											select="concat(day-start-date[@label='start']/@year, '-', day-start-date[@label='start']/@month, '-', day-start-date[@label='start']/@day)" />
									</td>
									<td>
										<xsl:value-of
											select="concat(day-finish-date[@label='finish']/@year, '-', day-finish-date[@label='finish']/@month, '-', day-finish-date[@label='finish']/@day)" />
									</td>
									<td>
										<xsl:value-of select="@net" />
									</td>
									<td>
										<xsl:value-of select="@vat" />
									</td>
									<xsl:for-each
										select="register-read-raw">
										<td>
											<xsl:value-of
												select="@mpan" />
										</td>
										<td>
											<xsl:value-of
												select="@meter-serial-number" />
										</td>
										<td>
											<xsl:value-of select="@tpr" />
										</td>
										<td>
											<xsl:value-of
												select="@coefficient" />
										</td>
										<td>
											<xsl:value-of
												select="@units" />
										</td>
										<td>
											<xsl:value-of
												select="concat(day-finish-date[@label='previous']/@year, '-', day-finish-date[@label='previous']/@month, '-', day-finish-date[@label='previous']/@day)" />
										</td>
										<td>
											<xsl:value-of
												select="@previous-value" />
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
											<xsl:value-of
												select="@present-value" />
										</td>
										<td>
											<xsl:value-of
												select="read-type[@label='present']/@code" />
										</td>
									</xsl:for-each>
								</tr>
							</xsl:for-each>
						</tbody>
					</table>
					<!--
						<h2>Failed invoices in CSV format</h2>
						
						<code>
						Reference, Account Reference, MPAN Text, Issue
						Date, Start Date, Finish Date, Net, VAT, R1
						MPAN, R1 Meter Serial Number, R1 TPR, R1
						Coefficient, R1 Units, R1 Previous Date, R1
						Previous Value, R1 Previous Type, R1 Present
						Date, R1 Present Value, R1 Present Type, R2
						MPAN, R2 Meter Serial Number, R2 TPR, R2
						Coefficient, R2 Units, R2 Previous Date, R2
						Previous Value, R2 Previous Type,R2 Present
						Date, R2 Present Value, R2 Present Type, R3
						MPAN, R3 Meter Serial Number, R3 TPR, R3
						Coefficient, R3 Units, R3 Previous Date, R3
						Previous Value, R3 Previous Type,R3 Present
						Date, R3 Present Value, R3 Present Type, R4
						MPAN, R4 Meter Serial Number, R4 TPR, R4
						Coefficient, R4 Units, R4 Previous Date, R4
						Previous Value, R4 Previous Type,R4 Present
						Date, R4 Present Value, R4 Present Type, R5
						MPAN, R5 Meter Serial Number, R5 TPR, R5
						Coefficient, R5 Units, R5 Previous Date, R5
						Previous Value, R5 Previous Type,R5 Present
						Date, R5 Present Value, R5 Present Type, R6
						MPAN, R6 Meter Serial Number, R6 TPR, R6
						Coefficient, R6 Units, R6 Previous Date, R6
						Previous Value, R6 Previous Type,R6 Present
						Date, R6 Present Value, R6 Present Type, R7
						MPAN, R7 Meter Serial Number, R7 TPR, R7
						Coefficient, R7 Units, R7 Previous Date, R7
						Previous Value, R7 Previous Type,R7 Present
						Date, R7 Present Value, R7 Present Type, R8
						MPAN, R8 Meter Serial Number, R8 TPR, R8
						Coefficient, R8 Units, R8 Previous Date, R8
						Previous Value, R8 Previous Type,R8 Present
						Date, R8 Present Value, R8 Present Type,
						<br />
						<xsl:for-each
						select="/source/invoice-import/failed-invoices/invoice-raw">
						<xsl:value-of
						select="concat(@reference, ', ', @account-reference, ', &quot;', @mpan-text, '&quot;', ', ', day-start-date[@label='issue']/@year, '-', day-start-date[@label='issue']/@month, '-', day-start-date[@label='issue']/@day, ', ', day-start-date[@label='start']/@year, '-', day-start-date[@label='start']/@month, '-', day-start-date[@label='start']/@day, ', ', day-finish-date[@label='finish']/@year, '-', day-finish-date[@label='finish']/@month, '-', day-finish-date[@label='finish']/@day, ', ', @net, ', ', @vat)" />
						<xsl:for-each select="register-read-raw">
						<xsl:value-of
						select="concat(', ', @mpan, ', ', @meter-serial-number, ', ', @tpr, ', ', @coefficient, ', ', @units, ', ', day-finish-date[@label='previous']/@year, '-', day-finish-date[@label='previous']/@month, '-', day-finish-date[@label='previous']/@day, ', ', @previous-value, ', ', @previous-type, ', ', day-finish-date[@label='present']/@year, '-', day-finish-date[@label='present']/@month, '-', day-finish-date[@label='present']/@day, ', ', @present-value, ', ', @present-type)" />
						</xsl:for-each>
						<br />
						</xsl:for-each>
						</code>
					-->
				</xsl:if>
				<xsl:if
					test="/source/invoice-import/successful-invoices/invoice-raw">
					<br />
					<br />
					<table>
						<caption>
							Invoices that loaded successfully
						</caption>
						<thead>
							<tr>
								<th>Reference</th>
								<th>Account Reference</th>
								<th>MPAN Text</th>
								<th>Issue Date</th>
								<th>Start Date</th>
								<th>Finish Date</th>
								<th>Net</th>
								<th>VAT</th>
								<th>R1 MPAN</th>
								<th>R1 Meter Serial Number</th>
								<th>R1 TPR</th>
								<th>R1 Coefficient</th>
								<th>R1 Units</th>
								<th>R1 Previous Read Date</th>
								<th>R1 Previous Read Value</th>
								<th>R1 Previous Read Type</th>
								<th>R1 Present Read Date</th>
								<th>R1 Present Read Value</th>
								<th>R1 Present Read Type</th>
								<th>R2 MPAN</th>
								<th>R2 Meter Serial Number</th>
								<th>R2 TPR</th>
								<th>R2 Coefficient</th>
								<th>R2 Units</th>
								<th>R2 Previous Read Date</th>
								<th>R2 Previous Read Value</th>
								<th>R2 Previous Read Type</th>
								<th>R2 Present Read Date</th>
								<th>R2 Present Read Value</th>
								<th>R2 Present Read Type</th>
								<th>R3 MPAN</th>
								<th>R3 Meter Serial Number</th>
								<th>R3 TPR</th>
								<th>R3 Coefficient</th>
								<th>R3 Units</th>
								<th>R3 Previous Read Date</th>
								<th>R3 Previous Read Value</th>
								<th>R3 Previous Read Type</th>
								<th>R3 Present Read Date</th>
								<th>R3 Present Read Value</th>
								<th>R3 Present Read Type</th>
								<th>R4 MPAN</th>
								<th>R4 Meter Serial Number</th>
								<th>R4 TPR</th>
								<th>R4 Coefficient</th>
								<th>R4 Units</th>
								<th>R4 Previous Read Date</th>
								<th>R4 Previous Read Value</th>
								<th>R4 Previous Read Type</th>
								<th>R4 Present Read Date</th>
								<th>R4 Present Read Value</th>
								<th>R4 Present Read Type</th>
							</tr>
						</thead>
						<tbody>
							<xsl:for-each
								select="/source/invoice-import/successful-invoices/invoice-raw">
								<tr>
									<td>
										<xsl:value-of
											select="@reference" />
									</td>
									<td>
										<xsl:value-of
											select="@account-reference" />
									</td>
									<td>
										<xsl:value-of
											select="@mpan-text" />
									</td>
									<td>
										<xsl:value-of
											select="concat(day-start-date[@label='issue']/@year, '-', day-start-date[@label='issue']/@month, '-', day-start-date[@label='issue']/@day)" />
									</td>
									<td>
										<xsl:value-of
											select="concat(day-start-date[@label='start']/@year, '-', day-start-date[@label='start']/@month, '-', day-start-date[@label='start']/@day)" />
									</td>
									<td>
										<xsl:value-of
											select="concat(day-finish-date[@label='finish']/@year, '-', day-finish-date[@label='finish']/@month, '-', day-finish-date[@label='finish']/@day)" />
									</td>
									<td>
										<xsl:value-of select="@net" />
									</td>
									<td>
										<xsl:value-of select="@vat" />
									</td>
									<xsl:for-each
										select="register-read-raw">
										<td>
											<xsl:value-of
												select="@mpan" />
										</td>
										<td>
											<xsl:value-of
												select="@meter-serial-number" />
										</td>
										<td>
											<xsl:value-of select="@tpr" />
										</td>
										<td>
											<xsl:value-of
												select="@coefficient" />
										</td>
										<td>
											<xsl:value-of
												select="@units" />
										</td>
										<td>
											<xsl:value-of
												select="concat(day-finish-date[@label='previous']/@year, '-', day-finish-date[@label='previous']/@month, '-', day-finish-date[@label='previous']/@day)" />
										</td>
										<td>
											<xsl:value-of
												select="@previous-value" />
										</td>
										<td>
											<xsl:value-of
												select="@previous-type" />
										</td>
										<td>
											<xsl:value-of
												select="concat(day-finish-date[@label='present']/@year, '-', day-finish-date[@label='present']/@month, '-', day-finish-date[@label='present']/@day)" />
										</td>
										<td>
											<xsl:value-of
												select="@present-value" />
										</td>
										<td>
											<xsl:value-of
												select="@present-type" />
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