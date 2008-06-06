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
						select="/source/bill-snag/supplier-service/supplier/org/@name" />
					&gt; Suppliers &gt;
					<xsl:value-of
						select="/source/bill-snag/supplier-service/supplier/@name" />
					&gt; Services &gt;
					<xsl:value-of
						select="/source/bill-snag/supplier-service/@name" />
					&gt; Bill Snags &gt;
					<xsl:value-of select="/source/bill-snag/@id" />
				</title>
			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill-snag/supplier-service/supplier/org/@id}/reports/0/screen/output/">
						<xsl:value-of
							select="/source/bill-snag/supplier-service/supplier/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill-snag/supplier-service/supplier/org/@id}/reports/35/screen/output/">
						<xsl:value-of select="'Suppliers'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill-snag/supplier-service/supplier/org/@id}/reports/36/screen/output/?supplier-id={/source/bill-snag/supplier-service/supplier/@id}">
						<xsl:value-of
							select="/source/bill-snag/supplier-service/supplier/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill-snag/supplier-service/supplier/org/@id}/reports/37/screen/output/?supplier-id={/source/bill-snag/supplier-service/supplier/@id}">
						<xsl:value-of select="'Services'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill-snag/supplier-service/supplier/org/@id}/reports/38/screen/output/?supplier-service-id={/source/bill-snag/supplier-service/@id}">
						<xsl:value-of
							select="/source/bill-snag/supplier-service/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill-snag/supplier-service/supplier/org/@id}/reports/44/screen/output/?supplier-service-id={/source/bill-snag/supplier-service/@id}">
						<xsl:value-of select="'Bill Snags'" />
					</a>
					&gt;
					<xsl:value-of
						select="concat(/source/bill-snag/@id, ' [')" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/bill-snag/supplier-service/supplier/org/@id}/suppliers/{/source/bill-snag/supplier-service/supplier/@id}/services/{/source/bill-snag/supplier-service/@id}/bill-snags/{/source/bill-snag/@id}/">
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
						<th>Chellow Id</th>
						<th>Bill</th>
						<th>Date Created</th>
						<th>Date Resolved</th>
						<th>Is Ignored?</th>
						<th>Description</th>
					</thead>
					<tbody>
						<tr>
							<td>
								<xsl:value-of
									select="/source/bill-snag/@id" />
							</td>
							<td>
								<a
									href="{/source/request/@context-path}/orgs/{/source/bill-snag/supplier-service/supplier/org/@id}/suppliers/{/source/bill-snag/supplier-service/supplier/@id}/accounts/{/source/bill-snag/bill/account/@id}/bills/{/source/bill-snag/bill/@id}/">
									<xsl:value-of
										select="/source/bill-snag/bill/@id" />
								</a>
							</td>
							<td>
								<xsl:value-of
									select="concat(/source/bill-snag/date[@label='created']/@year, '-', /source/bill-snag/date[@label='created']/@month, '-', /source/bill-snag/date[@label='created']/@day)" />
							</td>
							<td>
								<xsl:choose>
									<xsl:when
										test="date[@label='resolved']">
										<xsl:value-of
											select="concat(/source/bill-snag/date[@label='resolved']/@year, '-', /source/bill-snag/date[@label='resolved']/@month, '-', /source/bill-snag/date[@label='resolved']/@day)" />
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
									<xsl:otherwise>No</xsl:otherwise>
								</xsl:choose>
							</td>
							<td>
								Description:
								<xsl:value-of select="@description" />
							</td>
						</tr>
					</tbody>
				</table>
				<br/>
				<form action="." method="post">
					<fieldset>
						<legend>Ignore Bill Snag</legend>
						<input type="submit" value="Ignore" />
					</fieldset>
				</form>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>