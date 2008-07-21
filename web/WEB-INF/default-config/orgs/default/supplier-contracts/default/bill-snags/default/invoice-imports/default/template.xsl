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
						select="/source/bill-import/batch/supplier-service/supplier/org/@name" />
					&gt; Suppliers &gt;
					<xsl:value-of
						select="/source/bill-import/batch/supplier-service/supplier/@name" />
					&gt; Services &gt;
					<xsl:value-of
						select="/source/bill-import/batch/supplier-service/@name" />
					&gt; Batches &gt;
					<xsl:value-of
						select="/source/bill-import/batch/@name" />
					&gt; Bill Imports &gt;
					<xsl:value-of select="/source/bill-import/@id" />
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
						href="{/source/request/@context-path}/orgs/{/source/bill-import/batch/supplier-service/supplier/org/@id}/">
						<xsl:value-of
							select="/source/bill-import/batch/supplier-service/supplier/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill-import/batch/supplier-service/supplier/org/@id}/suppliers/">
						<xsl:value-of select="'Suppliers'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill-import/batch/supplier-service/supplier/org/@id}/suppliers/{/source/bill-import/batch/supplier-service/supplier/@id}/">
						<xsl:value-of
							select="/source/bill-import/batch/supplier-service/supplier/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill-import/batch/supplier-service/supplier/org/@id}/suppliers/{/source/bill-import/batch/supplier-service/supplier/@id}/services/">
						<xsl:value-of select="'Services'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill-import/batch/supplier-service/supplier/org/@id}/suppliers/{/source/bill-import/batch/supplier-service/supplier/@id}/">
						<xsl:value-of
							select="/source/bill-import/batch/supplier-service/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill-import/batch/supplier-service/supplier/org/@id}/suppliers/{/source/bill-import/batch/supplier-service/supplier/@id}/services/{/source/bill-import/batch/supplier-service/@id}/batches/">
						<xsl:value-of select="'Batches'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill-import/batch/supplier-service/supplier/org/@id}/suppliers/{/source/bill-import/batch/supplier-service/supplier/@id}/services/{/source/bill-import/batch/supplier-service/@id}/batches/{/source/bill-import/batch/@id}/">
						<xsl:value-of
							select="/source/bill-import/batch/@reference" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill-import/batch/supplier-service/supplier/org/@id}/suppliers/{/source/bill-import/batch/supplier-service/supplier/@id}/services/{/source/bill-import/batch/supplier-service/@id}/batches/{/source/bill-import/batch/@id}/bill-imports/">
						<xsl:value-of select="'Bill Imports'" />
					</a>
					&gt;
					<xsl:value-of select="/source/bill-import/@id" />
				</p>
				<br />
				<xsl:if test="//message[not(../../bill-raw)]">
					<ul>
						<xsl:for-each
							select="//message[not(../../bill-raw)]">
							<li>
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>
				<xsl:choose>
					<xsl:when test="/source/bill-import/bill-raw">
						<table>
							<caption>Bills that failed to load</caption>
							<thead>
								<tr>
									<th>Account Text</th>
									<th>MPAN Text</th>
									<th>Invoice Text</th>
									<th>Start Date</th>
									<th>Finish Date</th>
									<th>Net</th>
									<th>VAT</th>
									<th>Problem</th>
								</tr>
							</thead>
							<tbody>
								<xsl:for-each
									select="/source/bill-import/bill-raw">
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
												select="concat(hh-end-date[@label='start']/@year, '-', hh-end-date[@label='start']/@month, '-', hh-end-date[@label='start']/@day)" />
										</td>
										<td>
											<xsl:value-of
												select="concat(hh-end-date[@label='finish']/@year, '-', hh-end-date[@label='finish']/@month, '-', hh-end-date[@label='finish']/@day)" />
										</td>
										<td>
											<xsl:value-of select="@net" />
										</td>
										<td>
											<xsl:value-of select="@vat" />
										</td>
										<td>
											<xsl:value-of
												select="message/@description" />
										</td>

									</tr>
								</xsl:for-each>
							</tbody>
						</table>
						<h2>Failed bills in CSV format</h2>

						<code>
							Account	Text, MPAN Text, Invoice Text, Start Date, Finish Date, Net, VAT
							<br />
							<xsl:for-each
								select="/source/bill-import/bill-raw">
								<xsl:value-of
									select="concat(@account-text, ', &quot;', @mpan-text, '&quot;', ', ', @invoice-text, ', ', hh-end-date[@label='start']/@year, '-', hh-end-date[@label='start']/@month, '-', hh-end-date[@label='start']/@day, ', ', hh-end-date[@label='finish']/@year, '-', hh-end-date[@label='finish']/@month, '-', hh-end-date[@label='finish']/@day, ', ', @net, ', ', @vat)" />
								<br />
							</xsl:for-each>
						</code>
					</xsl:when>
					<xsl:when test="not(//message)">
						<p>
							All the bills have been successfully loaded
							and attached to the batch.
						</p>
					</xsl:when>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>