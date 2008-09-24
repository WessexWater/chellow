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
						select="/source/account-snag/supplier-service/supplier/org/@name" />
					&gt; Suppliers &gt;
					<xsl:value-of
						select="/source/account-snag/supplier-service/supplier/@name" />
					&gt; Services &gt;
					<xsl:value-of
						select="/source/account-snag/supplier-service/@name" />
					&gt; account-snages &gt;
					<xsl:value-of select="/source/account-snag/@id" />
				</title>
			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/{/source/account-snag/supplier-service/supplier/org/@id}/reports/0/screen/output/">
						<xsl:value-of
							select="/source/account-snag/supplier-service/supplier/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/account-snag/supplier-service/supplier/org/@id}/reports/35/screen/output/">
						<xsl:value-of select="'Suppliers'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/account-snag/supplier-service/supplier/org/@id}/reports/36/screen/output/?supplier-id={/source/account-snag/supplier-service/supplier/@id}">
						<xsl:value-of
							select="/source/account-snag/supplier-service/supplier/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/account-snag/supplier-service/supplier/org/@id}/reports/37/screen/output/?supplier-id={/source/account-snag/supplier-service/supplier/@id}">
						<xsl:value-of select="'Services'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/account-snag/supplier-service/supplier/org/@id}/reports/38/screen/output/?supplier-service-id={/source/account-snag/supplier-service/@id}">
						<xsl:value-of
							select="/source/account-snag/supplier-service/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/account-snag/supplier-service/supplier/org/@id}/reports/44/screen/output/?supplier-service-id={/source/account-snag/supplier-service/@id}">
						<xsl:value-of select="'Account Snags'" />
					</a>
					&gt;
					<xsl:value-of
						select="concat(/source/account-snag/@id, ' [')" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/account-snag/supplier-service/supplier/org/@id}/suppliers/{/source/account-snag/supplier-service/supplier/@id}/services/{/source/account-snag/supplier-service/@id}/account-snags/{/source/account-snag/@id}/">
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
								select="/source/account-snag/@id" />
						</td>
					</tr>
					<tr>
						<th>Account</th>
						<td>
							<a
								href="{/source/request/@context-path}/orgs/{/source/account-snag/supplier-service/supplier/org/@id}/reports/41/screen/output/?account-id={/source/account-snag/account/@id}">
								<xsl:value-of
									select="/source/account-snag/account/@reference" />
							</a>
						</td>
					</tr>
					<tr>
						<th>Start Date</th>
						<td>
							<xsl:value-of
								select="concat(' ', /source/account-snag/hh-end-date[@label='start']/@year, '-', /source/account-snag/hh-end-date[@label='start']/@month, '-', /source/account-snag/hh-end-date[@label='start']/@day)" />
						</td>
					</tr>
					<tr>
						<th>Finish Date</th>
						<td>
							<xsl:value-of
								select="concat(' ', /source/account-snag/hh-end-date[@label='finish']/@year, '-', /source/account-snag/hh-end-date[@label='finish']/@month, '-', /source/account-snag/hh-end-date[@label='finish']/@day)" />
						</td>
					</tr>
					<tr>
						<th>Date Created</th>
						<td>
							<xsl:value-of
								select="concat(' ', /source/account-snag/date[@label='created']/@year, '-', /source/account-snag/date[@label='created']/@month, '-', /source/account-snag/date[@label='created']/@day)" />
						</td>
					</tr>
					<tr>
						<th>Date Resolved</th>
						<td>
							<xsl:choose>
								<xsl:when
									test="/source/account-snag/hh-end-date[@label='resolved']">
									<xsl:value-of
										select="concat(/source/account-snag/hh-end-date[@label='resolved']/@year, '-', /source/account-snag/hh-end-date[@label='resolved']/@month, '-', /source/account-snag/hh-end-date[@label='resolved']/@day)" />
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
									test="/source/account-snag/@is-ignored = 'true'">
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
								select="/source/account-snag/@description" />
						</td>
					</tr>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>