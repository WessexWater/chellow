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
					Chellow
					&gt; Supplier Contracts &gt;
					<xsl:value-of
						select="/source/register-reads/bill/batch/supplier-contract/@name" />
					&gt; Batches &gt;
					<xsl:value-of select="/source/register-reads/bill/batch/@reference" />
					&gt; Bills &gt;
					<xsl:value-of select="/source/register-reads/bill/@id" />
					&gt; Reads
				</title>
			</head>

			<body>
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
						href="{/source/request/@context-path}/supplier-contracts/{/source/register-reads/bill/batch/supplier-contract/@id}/">
						<xsl:value-of
							select="/source/register-reads/bill/batch/supplier-contract/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplier-contracts/{/source/register-reads/bill/batch/supplier-contract/@id}/batches/">
						<xsl:value-of select="'Batches'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplier-contracts/{/source/register-reads/bill/batch/supplier-contract/@id}/batches/{/source/register-reads/bill/batch/@id}/">
						<xsl:value-of select="/source/register-reads/bill/batch/@reference" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplier-contracts/{/source/register-reads/bill/batch/supplier-contract/@id}/batches/{/source/register-reads/bill/batch/@id}/bills/">
						<xsl:value-of select="'Bills'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplier-contracts/{/source/register-reads/bill/batch/supplier-contract/@id}/batches/{/source/register-reads/bill/batch/@id}/bills/{/source/register-reads/bill/@id}/">
						<xsl:value-of select="/source/register-reads/bill/@id" />
					</a>
					&gt;
					<xsl:value-of select="'Reads'" />
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
				<table>
					<thead>
						<tr>
							<th>Chellow Id</th>
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
					<xsl:for-each select="/source/register-reads/register-read">
						<tr>
							<td>
								<a href="{@id}/">
									<xsl:value-of select="@id" />
								</a>
							</td>
							<td>
								<xsl:value-of select="@mpan-str" />
							</td>
							<td>
								<xsl:value-of select="@coefficient" />
							</td>
							<td>
								<xsl:value-of select="@units" />
							</td>
							<td>
								<a href="{/source/request/@context-path}/tprs/{tpr/@id}/">
									<xsl:value-of select="tpr/@code" />
								</a>
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
						</tr>
					</xsl:for-each>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>