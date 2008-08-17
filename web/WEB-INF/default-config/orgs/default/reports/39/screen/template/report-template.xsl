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
					href="{/source/request/@context-path}/orgs/{/source/rate-script/supplier-contract/org/@id}/reports/9/stream/output/" />
				<title>
					<xsl:value-of
						select="/source/rate-script/supplier-contract/org/@name" />
					&gt; Supplier Contracts &gt;
					<xsl:value-of
						select="/source/rate-script/supplier-contract/@name" />
					&gt; Rate Script
					<xsl:value-of select="/source/rate-script/@id" />
				</title>
			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/{/source/rate-script/supplier-contract/org/@id}/reports/0/screen/output/">
						<xsl:value-of
							select="/source/rate-script/supplier-contract/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/rate-script/supplier-contract/org/@id}/reports/37/screen/output/">
						<xsl:value-of select="'Supplier Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/rate-script/supplier-contract/org/@id}/reports/38/screen/output/?contract-id={/source/rate-script/supplier-contract/@id}">
						<xsl:value-of
							select="/source/rate-script/supplier-contract/@name" />
					</a>
					&gt; Rate Script
					<xsl:value-of
						select="concat(/source/rate-script/@id, ' [')" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/rate-script/supplier-contract/org/@id}/supplier-contracts/{/source/rate-script/supplier-contract/@id}/rate-scripts/{/source/rate-script/@id}/">
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
								select="/source/rate-script/@id" />
						</td>
					</tr>
					<tr>
						<th>Start Date</th>
						<td>
							<xsl:value-of
								select="concat(/source/rate-script/hh-end-date[@label='start']/@year, '-', /source/rate-script/hh-end-date[@label='start']/@month, '-', /source/rate-script/hh-end-date[@label='start']/@day)" />
						</td>
					</tr>
					<tr>
						<th>Finish Date</th>
						<td>
							<xsl:choose>
								<xsl:when
									test="/source/rate-script/hh-end-date[@label='finish']">
									<xsl:value-of
										select="concat(/source/rate-script/hh-end-date[@label='finish']/@year, '-', /source/rate-script/hh-end-date[@label='finish']/@month, '-', /source/rate-script/hh-end-date[@label='finish']/@day)" />
								</xsl:when>
								<xsl:otherwise>Ongoing</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
				</table>

				<h2>Script</h2>

				<pre>
					<xsl:value-of select="/source/rate-script/@script" />
				</pre>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

