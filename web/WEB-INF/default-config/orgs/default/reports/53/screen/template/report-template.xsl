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
					href="{/source/request/@context-path}/orgs/{/source/bill-snag/supplier-contract/org/@id}/reports/9/stream/output/" />
				<title>
					<xsl:value-of
						select="/source/bill-snag/supplier-contract/org/@name" />
					&gt; Supplier Contracts &gt;
					<xsl:value-of
						select="/source/bill-snag/supplier-contract/@name" />
					&gt; Bill Snags &gt;
					<xsl:value-of select="/source/bill-snag/@id" />
				</title>
			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill-snag/supplier-contract/org/@id}/reports/0/screen/output/">
						<xsl:value-of
							select="/source/bill-snag/supplier-contract/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill-snag/supplier-contract/org/@id}/reports/37/screen/output/?supplier-id={/source/bill-snag/supplier-contract/@id}">
						<xsl:value-of select="'Supplier Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill-snag/supplier-contract/org/@id}/reports/38/screen/output/?supplier-service-id={/source/bill-snag/supplier-contract/@id}">
						<xsl:value-of
							select="/source/bill-snag/supplier-contract/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill-snag/supplier-contract/org/@id}/reports/44/screen/output/?supplier-contract-id={/source/bill-snag/supplier-contract/@id}">
						<xsl:value-of select="'Bill Snags'" />
					</a>
					&gt;
					<xsl:value-of
						select="concat(/source/bill-snag/@id, ' [')" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill-snag/supplier-contract/org/@id}/supplier-contracts/{/source/bill-snag/supplier-contract/@id}/bill-snags/{/source/bill-snag/@id}/">
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
					<tr>
						<th>Chellow Id</th>
						<td>
							<xsl:value-of
								select="/source/bill-snag/@id" />
						</td>
					</tr>
					<tr>
						<th>Bill</th>
						<td>
							<a
								href="{/source/request/@context-path}/orgs/{/source/bill-snag/supplier-contract/org/@id}/reports/43/screen/output/?bill-id={/source/bill-snag/bill/@id}">
								<xsl:value-of
									select="/source/bill-snag/bill/@id" />
							</a>
						</td>

					</tr>
					<tr>
						<th>Date Created</th>
						<td>
							<xsl:value-of
								select="concat(/source/bill-snag/date[@label='created']/@year, '-', /source/bill-snag/date[@label='created']/@month, '-', /source/bill-snag/date[@label='created']/@day)" />
						</td>

					</tr>
					<tr>
						<th>Date Resolved</th>
						<td>
							<xsl:choose>
								<xsl:when
									test="/source/bill-snag/date[@label='resolved']">
									<xsl:value-of
										select="concat(/source/bill-snag/date[@label='resolved']/@year, '-', /source/bill-snag/date[@label='resolved']/@month, '-', /source/bill-snag/date[@label='resolved']/@day)" />
								</xsl:when>
								<xsl:otherwise>
									Unresolved
								</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
					<tr>
						<th>Is Ignored?</th>
						<td>
							<xsl:choose>
								<xsl:when
									test="/source/bill-snag/@is-ignored = 'true'">
									Yes
								</xsl:when>
								<xsl:otherwise>No</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
					<tr>
						<th>Description</th>
						<td>
							<xsl:value-of
								select="/source/bill-snag/@description" />
						</td>
					</tr>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>