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
					<xsl:value-of select="' &gt; SSCs'" />
				</p>

				<table>
					<thead>
						<tr>
							<th>Code</th>
							<th>Description</th>
							<th>Dso</th>
							<th>Is Unmetered?</th>
							<th>Tprs</th>
						</tr>
					</thead>
					<tbody>

						<xsl:for-each
							select="/source/meter-timeswitch">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/meter-timeswitches/{@id}/">
										<xsl:value-of select="@code" />
									</a>
								</td>
								<td>
									<xsl:value-of select="@description" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when test="dso">
											<a
												href="{/source/request/@context-path}/dsos/{@id}/">
												<xsl:value-of
													select="dso/@code" />
											</a>
										</xsl:when>
										<xsl:otherwise>
											None
										</xsl:otherwise>
									</xsl:choose>
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
								<td>
									<ul>
										<xsl:for-each
											select="register">
											<li>
												<xsl:for-each
													select="tpr">
													<xsl:value-of
														select="@code" />
													<xsl:if
														test="position() != last()">
														<xsl:value-of
															select="', '" />
													</xsl:if>
												</xsl:for-each>
											</li>
										</xsl:for-each>
									</ul>
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

