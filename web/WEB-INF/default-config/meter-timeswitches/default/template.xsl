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
					Chellow &gt; Meter Timeswitches &gt;
					<xsl:value-of
						select="/source/meter-timeswitch/@code" />
				</title>
			</head>

			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img
							src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					<xsl:value-of select="' &gt; '" />
					<a
						href="{/source/request/@context-path}/meter-timeswitches/">
						<xsl:value-of select="'Meter Timeswitches'" />
					</a>
					<xsl:value-of
						select="concat(' &gt; ', /source/meter-timeswitch/@code)" />
				</p>

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
					<caption>Properties</caption>
					<thead>
						<tr>
							<th>Name</th>
							<th>Value</th>
						</tr>
					</thead>
					<tbody>
						<tr>
							<td>Code</td>
							<td>
								<xsl:value-of
									select="/source/meter-timeswitch/@code" />
							</td>
						</tr>
						<tr>
							<td>Description</td>
							<td>
								<xsl:value-of
									select="/source/meter-timeswitch/@description" />
							</td>
						</tr>
						<tr>
							<td>DSO</td>
							<td>
								<xsl:choose>
									<xsl:when
										test="/source/meter-timeswitch/dso">
										<a
											href="{/source/request/@context-path}/dsos/{/source/meter-timeswitch/dso/@id}">
											<xsl:value-of
												select="/source/meter-timeswitch/dso/@code" />
										</a>
									</xsl:when>
									<xsl:otherwise>All</xsl:otherwise>
								</xsl:choose>
							</td>
						</tr>
						<tr>
							<td>Is Unmetered?</td>
							<td>
								<xsl:value-of
									select="/source/meter-timeswitch/@is-unmetered" />
							</td>
						</tr>
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

