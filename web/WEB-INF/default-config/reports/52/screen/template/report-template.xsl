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
					href="{/source/request/@context-path}/orgs/{/source/bill-snags/supplier-contract/org/@id}/reports/9/stream/output/" />

				<title>
					<xsl:value-of
						select="/source/bill-snags/supplier-contract/org/@name" />
					&gt; Supplier Services &gt;
					<xsl:value-of
						select="/source/bill-snags/supplier-contract/@name" />
					&gt; Bill Snags
				</title>
			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill-snags/supplier-contract/org/@id}/reports/0/screen/output/">
						<xsl:value-of
							select="/source/bill-snags/supplier-contract/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill-snags/supplier-contract/org/@id}/reports/37/screen/output/">
						<xsl:value-of select="'Supplier Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill-snags/supplier-contract/org/@id}/reports/38/screen/output/?contract-id={/source/bill-snags/supplier-contract/@id}">
						<xsl:value-of
							select="/source/bill-snags/supplier-contract/@name" />
					</a>
					&gt;
					<xsl:value-of select="'Bill Snags ['" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill-snags/supplier-contract/org/@id}/supplier-contracts/{/source/bill-snags/supplier-contract/@id}/bill-snags/">
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
					<thead>
						<tr>
							<th>Chellow Id</th>
							<th>Bill</th>
							<th>Date Created</th>
							<th>Date Resolved</th>
							<th>Is Ignored?</th>
							<th>Description</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each
							select="/source/bill-snags/bill-snag">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/bill-snags/supplier-contract/org/@id}/reports/53/screen/output/?snag-id={@id}">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/bill-snags/supplier-contract/org/@id}/reports/43/screen/output/?bill-id={bill/@id}">
										<xsl:value-of select="bill/@id" />
									</a>
								</td>
								<td>
									<xsl:value-of
										select="concat(date[@label='created']/@year, '-', date[@label='created']/@month, '-', date[@label='created']/@day)" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when
											test="hh-end-date[@label='resolved']">
											<xsl:value-of
												select="concat(hh-end-date[@label='resolved']/@year, '-', hh-end-date[@label='resolved']/@month, '-', hh-end-date[@label='resolved']/@day)" />
										</xsl:when>
										<xsl:otherwise>
											Unresolved
										</xsl:otherwise>
									</xsl:choose>
								</td>
								<td>
									<xsl:choose>
										<xsl:when
											test="@is-ignored = 'true'">
											Yes
										</xsl:when>
										<xsl:otherwise>
											No
										</xsl:otherwise>
									</xsl:choose>
								</td>
								<td>
									<xsl:value-of select="@description" />
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>