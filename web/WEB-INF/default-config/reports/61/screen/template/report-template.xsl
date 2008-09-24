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
					href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/9/stream/output/" />
				<title>
					<xsl:value-of select="/source/org/@name" />
					&gt; Market Roles &gt;
					<xsl:value-of
						select="/source/market-role/@description" />
				</title>
			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/0/screen/output/">
						<xsl:value-of select="/source/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/60/screen/output/">
						<xsl:value-of select="'Market Roles'" />
					</a>
					&gt;
					<xsl:value-of
						select="/source/market-role/@description" />
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
								select="/source/market-role/@id" />
						</td>
					</tr>
					<tr>
						<th>Code</th>
						<td>
							<xsl:value-of
								select="/source/market-role/@code" />
						</td>
					</tr>
					<tr>

						<th>Description</th>
						<td>
							<xsl:value-of
								select="/source/market-role/@description" />
						</td>
					</tr>
				</table>
				<br />
				<xsl:choose>
					<xsl:when test="/source/market-role/@code='R'">
						<table>
							<caption>DSOs</caption>
							<thead>
								<tr>
									<th>Chellow Id</th>
									<th>Code</th>
									<th>Name</th>
								</tr>
							</thead>
							<tbody>
								<xsl:for-each
									select="/source/market-role/dso">
									<tr>
										<td>
											<a
												href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/69/screen/output/?dso-id={@id}">
												<xsl:value-of
													select="@id" />
											</a>
										</td>
										<td>
											<xsl:value-of
												select="@code" />
										</td>
										<td>
											<xsl:value-of
												select="@name" />
										</td>
									</tr>
								</xsl:for-each>
							</tbody>
						</table>
					</xsl:when>
					<xsl:otherwise>
						<table>
							<caption>Providers</caption>
							<thead>
								<tr>
									<th>Chellow Id</th>
									<th>Name</th>
								</tr>
							</thead>
							<tbody>
								<xsl:for-each
									select="/source/market-role/provider">
									<tr>
										<td>
											<a
												href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/23/screen/output/?provider-id={@id}">
												<xsl:value-of
													select="@id" />
											</a>
										</td>
										<td>
											<xsl:value-of
												select="@name" />
										</td>
									</tr>
								</xsl:for-each>
							</tbody>
						</table>

					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>