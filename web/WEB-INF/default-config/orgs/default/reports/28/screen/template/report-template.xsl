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
					&gt; Providers &gt;
					<xsl:value-of
						select="/source/mpan-tops/provider/@dso-code" />
					&gt; MPAN top-lines
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
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/22/screen/output/">
						<xsl:value-of select="'Providers'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/23/screen/output/?dso-id={/source/mpan-tops/dso/@id}">
						<xsl:value-of
							select="/source/mpan-tops/provider/@dso-code" />
					</a>
					&gt; MPAN top-lines
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
							<th>PC</th>
							<th>MTC</th>
							<th>LLFC</th>
							<th>SSC</th>
							<th>Valid From</th>
							<th>Valid To</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each
							select="/source/mpan-tops/mpan-top">
							<tr>
								<td>
									<a href="{@id}/">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/27/screen/output/?pc-id={pc/@id}">
										<xsl:value-of select="pc/@code" />
									</a>
									<xsl:value-of
										select="concat(' ', pc/@description)" />
								</td>

								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/31/screen/output/?mtc-id={mtc/@id}">
										<xsl:value-of
											select="mtc/@code" />
									</a>
									<xsl:value-of
										select="concat(' ', mtc/@description)" />
								</td>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/25/screen/output/?llfc-id={llfc/@id}">
										<xsl:value-of
											select="llfc/@code" />
									</a>
									<xsl:value-of
										select="concat(' ', llfc/@description)" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when test="ssc">
											<a
												href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/63/screen/output/?ssc-id={ssc/@id}">
												<xsl:value-of
													select="ssc/@code" />
											</a>
											<xsl:value-of
												select="concat(' ', ssc/@description)" />
										</xsl:when>
										<xsl:otherwise>
											N/A
										</xsl:otherwise>
									</xsl:choose>
								</td>
								<td>
									<xsl:value-of
										select="concat(date[@label='from']/@year, '-', date[@label='from']/@month, '-', date[@label='from']/@day, ' ', date[@label='from']/@hour, ':', date[@label='from']/@minute, ' Z')" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when
											test="date[@label='to']">
											<xsl:value-of
												select="concat(date[@label='to']/@year, '-', date[@label='to']/@month, '-', date[@label='to']/@day, ' ', date[@label='to']/@hour, ':', date[@label='to']/@minute, ' Z')" />
										</xsl:when>
										<xsl:otherwise>
											Ongoing
										</xsl:otherwise>
									</xsl:choose>
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>