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
					Chellow &gt; Supplier Contracts &gt;
					<xsl:value-of
						select="/source/bill-snag/supplier-contract/@name" />
					&gt; Bill Snags &gt;
					<xsl:value-of select="/source/bill-snag/@id" />
				</title>
			</head>
			<body>
				<xsl:if test="//message">
					<ul>
						<xsl:for-each select="//message">
							<li>
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>
				<p>
					<a href="{/source/request/@context-path}/">
						<img
							src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplier-contracts/">
						<xsl:value-of select="'Supplier Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplier-contracts/{/source/bill-snag/supplier-contract/@id}/">
						<xsl:value-of
							select="/source/bill-snag/supplier-contract/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplier-contracts/{/source/bill-snag/supplier-contract/@id}/bill-snags/">
						<xsl:value-of select="'Bill Snags'" />
					</a>
					&gt;
					<xsl:value-of
						select="concat(/source/bill-snag/@id, ' [')" />
					<a
						href="{/source/request/@context-path}/reports/54/output/?snag-id={/source/bill-snag/@id}">
						<xsl:value-of select="'view'" />
					</a>
					<xsl:value-of select="']'" />
				</p>
				<br />

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
								href="{/source/request/@context-path}/supplier-contracts/{/source/bill-snag/supplier-contract/@id}/accounts/{/source/bill-snag/bill/account/@id}/bills/{/source/bill-snag/bill/@id}/">
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
				<br />
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