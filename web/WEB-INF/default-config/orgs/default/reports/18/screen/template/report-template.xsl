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
					href="{/source/request/@context-path}/style/" />

				<title>Chellow &gt; Sites</title>

			</head>

			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/1/reports/0/screen/output/">
						<img src="{/source/request/@context-path}/logo/"
							alt="Logo" />
						<span class="logo">Chellow</span>
					</a>
					&gt; Snags
					<br />
					<br />
					<xsl:value-of select="source/@snag-count" />
					Snag(s) (older then 5 days) Total over
					<xsl:value-of select="source/@site-count" />
					Site(s)
					<br />
					A further
					<xsl:value-of select="source/@pending-site-count" />
					site(s) have snags not yet older then 5 days
				</p>

				<table cellpadding="5" cellspacing="0">
					<thead>
						<tr>
							<th>SnagId</th>
							<th>MPAN</th>
							<th>Site Name</th>
							<th>Snag Description</th>
							<th>Supply</th>
							<th>Units</th>
							<th>Duration</th>
						</tr>
					</thead>
					<tbody align="center">
						<xsl:for-each select="/source/snag-channel">
							<tr>
								<td>
									<a
										href="https://chellow.meniscus.co.uk/orgs/1/dces/21/services/21/snags-channel/{@id}/">
										<xsl:value-of select="@id" />
									</a>
								</td>

								<td align="center">
									<xsl:apply-templates
										select="channel/supply/supply-generation/mpan" />
								</td>
								<td>
									<xsl:value-of
										select="channel/supply/site/@name" />
								</td>
								<td>
									<xsl:value-of select="@description" />
								</td>

								<td>
									<xsl:choose>
										<xsl:when
											test="channel/@is-import='true'">
											Import
										</xsl:when>
										<xsl:otherwise>
											Export
										</xsl:otherwise>
									</xsl:choose>
								</td>

								<td>
									<xsl:choose>
										<xsl:when
											test="channel/@is-kwh='true'">
											kWh
										</xsl:when>
										<xsl:otherwise>
											kVAr
										</xsl:otherwise>
									</xsl:choose>
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

	<xsl:template match="mpan">
		<xsl:value-of select="mpan-core/dso/@code" />
		<xsl:value-of select="mpan-core/@uniquePart" />
		<xsl:value-of select="mpan-core/@checkDigit" />
		<br />
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

