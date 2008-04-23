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
				<style>
					table { width: 300em; }

					caption { text-align: left; }
				</style>
				<title>
					Chellow &gt; Organizations &gt;
					<xsl:value-of
						select="/source/invoice-import/batch/supplier-service/supplier/org/@name" />
					&gt; Suppliers &gt;
					<xsl:value-of
						select="/source/invoice-import/batch/supplier-service/supplier/@name" />
					&gt; Services &gt;
					<xsl:value-of
						select="/source/invoice-import/batch/supplier-service/@name" />
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
						href="{/source/request/@context-path}/orgs/{/source/invoice-import/batch/supplier-service/supplier/org/@id}/">
						<xsl:value-of
							select="/source/invoice-import/batch/supplier-service/supplier/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice-import/batch/supplier-service/supplier/org/@id}/suppliers/">
						<xsl:value-of select="'Suppliers'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice-import/batch/supplier-service/supplier/org/@id}/suppliers/{/source/invoice-import/batch/supplier-service/supplier/@id}/">
						<xsl:value-of
							select="/source/invoice-import/batch/supplier-service/supplier/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice-import/batch/supplier-service/supplier/org/@id}/suppliers/{/source/invoice-import/batch/supplier-service/supplier/@id}/services/">
						<xsl:value-of select="'Services'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice-import/batch/supplier-service/supplier/org/@id}/suppliers/{/source/invoice-import/batch/supplier-service/supplier/@id}/services/{/source/invoice-import/batch/supplier-service/@id}/">
						<xsl:value-of
							select="/source/invoice-import/batch/supplier-service/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice-import/batch/supplier-service/supplier/org/@id}/suppliers/{/source/invoice-import/batch/supplier-service/supplier/@id}/services/{/source/invoice-import/batch/supplier-service/@id}/batches/">
						<xsl:value-of select="'Batches'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice-import/batch/supplier-service/supplier/org/@id}/suppliers/{/source/invoice-import/batch/supplier-service/supplier/@id}/services/{/source/invoice-import/batch/supplier-service/@id}/batches/{/source/invoice-import/batch/@id}/">
						<xsl:value-of
							select="/source/invoice-import/batch/@reference" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice-import/batch/supplier-service/supplier/org/@id}/suppliers/{/source/invoice-import/batch/supplier-service/supplier/@id}/services/{/source/invoice-import/batch/supplier-service/@id}/batches/{/source/invoice-import/batch/@id}/invoice-imports/">
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
								<th>Account Text</th>
								<th>MPAN Text</th>
								<th>Invoice Text</th>
								<th>Issue Date</th>
								<th>Start Date</th>
								<th>Finish Date</th>
								<th>Net</th>
								<th>VAT</th>
								<th>R1 MPAN</th>
								<th>R1 Date</th>
								<th>R1 Meter Serial Number</th>
								<th>R1 Read</th>
								<th>R1 Coefficient</th>
								<th>R1 Anti Read?</th>
								<th>R1 Units</th>
								<th>R1 Type</th>
								<th>R1 TPR</th>
								<th>R2 MPAN</th>
								<th>R2 Date</th>
								<th>R2 Meter Serial Number</th>
								<th>R2 Read</th>
								<th>R2 Coefficient</th>
								<th>R2 Anti Read?</th>
								<th>R2 Units</th>
								<th>R2 Type</th>
								<th>R2 TPR</th>
								<th>R3 MPAN</th>
								<th>R3 Date</th>
								<th>R3 Meter Serial Number</th>
								<th>R3 Read</th>
								<th>R3 Coefficient</th>
								<th>R3 Anti Read?</th>
								<th>R3 Units</th>
								<th>R3 Type</th>
								<th>R3 TPR</th>
								<th>R4 MPAN</th>
								<th>R4 Date</th>
								<th>R4 Meter Serial Number</th>
								<th>R4 Read</th>
								<th>R4 Coefficient</th>
								<th>R4 Anti Read?</th>
								<th>R4 Units</th>
								<th>R4 Type</th>
								<th>R4 TPR</th>
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
											select="@account-text" />
									</td>
									<td>
										<xsl:value-of
											select="@mpan-text" />
									</td>
									<td>
										<xsl:value-of
											select="@invoice-text" />
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
												select="concat(day-finish-date/@year, '-', day-finish-date/@month, '-', day-finish-date/@day)" />
										</td>
										<td>
											<xsl:value-of
												select="@meter-serial-number" />
										</td>
										<td>
											<xsl:value-of
												select="@value" />
										</td>
										<td>
											<xsl:value-of
												select="@coefficient" />
										</td>
										<td>
											<xsl:value-of
												select="@is-anti-read" />
										</td>
										<td>
											<xsl:value-of
												select="@units" />
										</td>
										<td>
											<xsl:value-of
												select="@type" />
										</td>
										<td>
											<xsl:value-of select="@tpr" />
										</td>
									</xsl:for-each>
								</tr>
							</xsl:for-each>
						</tbody>
					</table>
					<h2>Failed invoices in CSV format</h2>

					<code>
						Account Text, MPAN Text, Invoice Text, Issue
						Date, Start Date, Finish Date, Net, VAT, R1
						MPAN, R1 Date, R1 Meter Serial Number, R1 Read,
						R1 Coefficient, R1 Anti Read?, R1 Units, R1
						Type, R1 TPR, R2 MPAN, R2 Date, R2 Meter Serial
						Number, R2 Read, R2 Coefficient, R2 Anti Read?,
						R2 Units, R2 Type, R2 TPR, R3 MPAN, R3 Date, R3
						Meter Serial Number, R3 Read, R3 Coefficient, R3
						Anti Read?, R3 Units, R3 Type, R3 TPR, R4 MPAN,
						R4 Date, R4 Meter Serial Number, R4 Read, R4
						Coefficient, R4 Anti Read?, R4 Units, R4 Type,
						R4 TPR, R5 MPAN, R5 Date, R5 Meter Serial
						Number, R5 Read, R5 Coefficient, R5 Anti Read?,
						R5 Units, R5 Type, R5 TPR, R6 MPAN, R6 Date, R6
						Meter Serial Number, R6 Read, R6 Coefficient, R6
						Anti Read?, R6 Units, R6 Type, R6 TPR, R7 MPAN,
						R7 Date, R7 Meter Serial Number, R7 Read, R7
						Coefficient, R7 Anti Read?, R7 Units, R7 Type,
						R7 TPR, R8 MPAN, R8 Date, R8 Meter Serial
						Number, R8 Read, R8 Coefficient, R8 Anti Read?,
						R8 Units, R8 Type, R8 TPR
						<br />
						<xsl:for-each
							select="/source/invoice-import/failed-invoices/invoice-raw">
							<xsl:value-of
								select="concat(@account-text, ', &quot;', @mpan-text, '&quot;', ', ', @invoice-text, ', ', day-start-date[@label='issue']/@year, '-', day-start-date[@label='issue']/@month, '-', day-start-date[@label='issue']/@day, ', ', day-start-date[@label='start']/@year, '-', day-start-date[@label='start']/@month, '-', day-start-date[@label='start']/@day, ', ', day-finish-date[@label='finish']/@year, '-', day-finish-date[@label='finish']/@month, '-', day-finish-date[@label='finish']/@day, ', ', @net, ', ', @vat)" />
							<xsl:for-each select="register-read-raw">
								<xsl:value-of
									select="concat(', ', @mpan, ', ', day-finish-date/@year, '-', day-finish-date/@month, '-', day-finish-date/@day, ', ', @meter-serial-number, ', ', @value, ', ', @coefficient, ', ', @is-anti-read, ', ', @units, ', ', @type, ', ', @tpr)" />
							</xsl:for-each>
							<br />
						</xsl:for-each>
					</code>
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
								<th>Account Text</th>
								<th>MPAN Text</th>
								<th>Invoice Text</th>
								<th>Issue Date</th>
								<th>Start Date</th>
								<th>Finish Date</th>
								<th>Net</th>
								<th>VAT</th>
								<th>R1 MPAN</th>
								<th>R1 Date</th>
								<th>R1 Meter Serial Number</th>
								<th>R1 Read</th>
								<th>R1 Coefficient</th>
								<th>R1 Anti Read?</th>
								<th>R1 Units</th>
								<th>R1 Type</th>
								<th>R1 TPR</th>
								<th>R2 MPAN</th>
								<th>R2 Date</th>
								<th>R2 Meter Serial Number</th>
								<th>R2 Read</th>
								<th>R2 Coefficient</th>
								<th>R2 Anti Read?</th>
								<th>R2 Units</th>
								<th>R2 Type</th>
								<th>R2 TPR</th>
								<th>R3 MPAN</th>
								<th>R3 Date</th>
								<th>R3 Meter Serial Number</th>
								<th>R3 Read</th>
								<th>R3 Coefficient</th>
								<th>R3 Anti Read?</th>
								<th>R3 Units</th>
								<th>R3 Type</th>
								<th>R3 TPR</th>
								<th>R4 MPAN</th>
								<th>R4 Date</th>
								<th>R4 Meter Serial Number</th>
								<th>R4 Read</th>
								<th>R4 Coefficient</th>
								<th>R4 Anti Read?</th>
								<th>R4 Units</th>
								<th>R4 Type</th>
								<th>R4 TPR</th>
							</tr>
						</thead>
						<tbody>
							<xsl:for-each
								select="/source/invoice-import/successful-invoices/invoice-raw">
								<tr>
									<td>
										<xsl:value-of
											select="@account-text" />
									</td>
									<td>
										<xsl:value-of
											select="@mpan-text" />
									</td>
									<td>
										<xsl:value-of
											select="@invoice-text" />
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
												select="concat(day-finish-date/@year, '-', day-finish-date/@month, '-', day-finish-date/@day)" />
										</td>
										<td>
											<xsl:value-of
												select="@meter-serial-number" />
										</td>
										<td>
											<xsl:value-of
												select="@value" />
										</td>
										<td>
											<xsl:value-of
												select="@coefficient" />
										</td>
										<td>
											<xsl:value-of
												select="@is-anti-read" />
										</td>
										<td>
											<xsl:value-of
												select="@units" />
										</td>
										<td>
											<xsl:value-of
												select="@type" />
										</td>
										<td>
											<xsl:value-of select="@tpr" />
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