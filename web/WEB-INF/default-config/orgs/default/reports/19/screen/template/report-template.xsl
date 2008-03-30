<?xml version="1.0" encoding="us-ascii"?>
<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="xml" encoding="US-ASCII"
		doctype-public="-//W3C//DTD XHTML 1.1//EN"
		doctype-system="http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd"
		indent="yes" />

	<xsl:template match="/">
		<html>
			<head>
				<link rel="stylesheet" type="text/css"
					href="{/source/request/@context-path}/orgs/1/reports/9/stream/output/" />

				<title>Chellow &gt; Sites</title>

			</head>

			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/1/reports/0/screen/output/">
						<img src="{/source/request/@context-path}/logo/"
							alt="Logo" />
						<span class="logo">
							<xsl:value-of select="'Chellow'" />
						</span>
					</a>
					&gt; Snags
					<br />
					<br />
					<xsl:value-of select="source/@snag-count" />
					Snag(s) (older then 5 days) Total over
					<xsl:value-of select="source/@site-count" />
					Site(s)
					<br />
				</p>

				<table cellpadding="5" cellspacing="0">
					<thead>
						<tr>
							<th>SnagId</th>
							<th>Site ID</th>
							<th>Site Name</th>
							<th>Snag Description</th>
							<th>Duration</th>
						</tr>
					</thead>
					<tbody align="center">
						<xsl:for-each select="/source/snag-site">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/1/dces/21/services/21/snags-site/{@id}/">
										<xsl:value-of select="@id" />
									</a>
								</td>

								<td align="center">
									<a
										href="{/source/request/@context-path}/chellow/orgs/1/reports/2/screen/output/?site-id={site/@id}">
										<xsl:value-of
											select="site/@code" />
									</a>
								</td>

								<td>
									<xsl:value-of select="site/@name" />
								</td>
								<td>
									<xsl:value-of select="@description" />
								</td>

								<td align="left">
									Start
									<xsl:apply-templates
										select="hh-end-date[@label='start']" />
									<br />
									Finish
									<xsl:apply-templates
										select="hh-end-date[@label='finish']" />
								</td>

							</tr>
						</xsl:for-each>
					</tbody>
				</table>

			</body>
		</html>
	</xsl:template>

	<xsl:template match="hh-end-date">
		<xsl:value-of select="@year" />
		-
		<xsl:value-of select="@month" />
		-
		<xsl:value-of select="@day" />
		<xsl:text></xsl:text>
		<xsl:value-of select="@hour" />
		:
		<xsl:value-of select="@minute" />
		<xsl:text>Z</xsl:text>
	</xsl:template>

</xsl:stylesheet>

