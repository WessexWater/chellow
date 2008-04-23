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

				<title>Chellow &gt; Meter Timeswitches</title>
			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/0/screen/output/">
						<xsl:value-of select="/source/org/@name"/>
					</a>
					&gt; Meter Timeswitches
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
							<th>Id</th>
							<th>Code</th>
							<th>Dso</th>
							<th>Description</th>
							<th>Is Unmetered?</th>
						</tr>
					</thead>
					<tbody>

						<xsl:for-each
							select="/source/mtcs/meter-timeswitch">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/31/screen/output/?mt-id={@id}">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<xsl:value-of select="@code" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when test="dso">
											<a
												href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/23/screen/output/?dso-id={dso/@id}">
												<xsl:value-of
													select="dso/@code" />
											</a>
										</xsl:when>
										<xsl:otherwise>
											All
										</xsl:otherwise>
									</xsl:choose>
								</td>
								<td>
									<xsl:value-of select="@description" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when
											test="@is-unmetered = 'true'">
											Unmetered
										</xsl:when>
										<xsl:otherwise>
											Metered
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