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
					href="{/source/request/@context-path}/reports/19/output/" />
				<title>Chellow &gt; Supplies</title>
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
						<img src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					&gt;
					<xsl:value-of select="'Supplies ['" />
					<a href="{/source/request/@context-path}/reports/99/output/">
						<xsl:value-of select="'view'" />
					</a>
					<xsl:value-of select="']'" />
				</p>
				<br />
				<form action=".">
					<fieldset>
						<legend>Search for supply generations by MPAN core, account number or meter serial number</legend>
						<input name="search-pattern"
							value="{/source/request/parameter[@name='search-pattern']/value}" />
						<xsl:value-of select="' '" />
						<input type="submit" value="Search" />
					</fieldset>
				</form>
				<xsl:choose>
					<xsl:when test="/source/supply-generation">
						<p>
							Only the first 50 supply generations of the search
							results are shown.
                        </p>
						<table>
							<caption>
								Supplies
                            </caption>
							<tr>
								<th rowspan="3">Supply</th>
								<th rowspan="3">Meter Serial Number</th>
								<th colspan="2">HHDC</th>
								<th colspan="3">Import</th>
								<th colspan="3">Export</th>
							</tr>
							<tr>
								<th rowspan="2">Contract</th>
								<th rowspan="2">Account</th>
								<th rowspan="2">Mpan</th>
								<th colspan="2">Supplier</th>
								<th rowspan="2">Mpan</th>
								<th colspan="2">Supplier</th>
							</tr>
							<tr>
								<th>Contract</th>
								<th>Account</th>
								<th>Contract</th>
								<th>Account</th>
							</tr>
							<xsl:for-each select="/source/supply-generation">
								<tr>
									<td>
										<a
											href="{/source/request/@context-path}/reports/7/output/?supply-id={supply/@id}">
											<xsl:value-of select="'supply'" />
										</a>
									</td>
									<td>
										<xsl:value-of select="@meter-serial-number" />
									</td>
									<td>
										<a
											href="{/source/request/@context-path}/reports/115/output/?hhdc-contract-id={hhdc-contract/@id}">
											<xsl:value-of select="hhdc-contract/@name" />
										</a>
									</td>
									<td>
										<xsl:value-of select="@hhdc-account" />
									</td>
									<td>
										<xsl:if test="mpan/llfc/@is-import='true'">
											<xsl:value-of
												select="concat(pc/@code, ' ', mpan[llfc/@is-import='true']/mtc/@code, ' ', mpan/llfc[@is-import='true']/@code, ' ', mpan[llfc/@is-import='true']/mpan-core/@core)" />
										</xsl:if>
									</td>
									<td>
										<xsl:if test="mpan/llfc/@is-import='true'">
											<a
												href="{/source/request/@context-path}/reports/77/output/?supplier-contract-id={mpan[llfc/@is-import='true']/supplier-contract/@id}">
												<xsl:value-of
													select="mpan[llfc/@is-import='true']/supplier-contract/@name" />
											</a>
										</xsl:if>
									</td>
									<td>
										<xsl:if test="mpan/llfc/@is-import='true'">
											<xsl:value-of
												select="mpan[llfc/@is-import='true']/@supplier-account" />
										</xsl:if>
									</td>
									<td>
										<xsl:if test="mpan/llfc/@is-import='false'">
											<xsl:value-of
												select="concat(pc/@code, ' ', mpan[llfc/@is-import='false']/mtc/@code, ' ', mpan/llfc[@is-import='false']/@code, ' ', mpan[llfc/@is-import='false']/mpan-core/@core)" />
										</xsl:if>
									</td>
									<td>
										<xsl:if test="mpan/llfc/@is-import='false'">
											<a
												href="{/source/request/@context-path}/reports/77/output/?supplier-contract-id={mpan[llfc/@is-import='false']/supplier-contract/@id}">
												<xsl:value-of
													select="mpan[llfc/@is-import='false']/supplier-contract/@name" />
											</a>
										</xsl:if>
									</td>
									<td>
										<xsl:if test="mpan/llfc/@is-import='false'">
											<xsl:value-of
												select="mpan[llfc/@is-import='false']/@supplier-account" />
										</xsl:if>
									</td>
								</tr>
							</xsl:for-each>
						</table>
					</xsl:when>
					<xsl:when test="/source/request/parameter[@name='search-pattern']">
						<p>No supplies matched your search</p>
					</xsl:when>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

