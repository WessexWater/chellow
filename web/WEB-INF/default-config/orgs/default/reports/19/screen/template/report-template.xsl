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
					href="{/source/request/@context-path}/orgs/{/source/site-snags/hhdc-contract/org/@id}/reports/9/stream/output/" />

				<title>
					<xsl:value-of
						select="/source/site-snags/hhdc-contract/org/@name" />
					&gt; HHDC Contracts &gt;
					<xsl:value-of
						select="/source/site-snags/hhdc-contract/@name" />
					&gt; Site Snags
				</title>
			</head>

			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/{/source/site-snags/hhdc-contract/org/@id}/reports/0/screen/output/">
						<xsl:value-of
							select="/source/site-snags/hhdc-contract/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/site-snags/hhdc-contract/org/@id}/reports/56/screen/output/?hhdc-contract-id={/source/site-snags/hhdc-contract/@id}">
						<xsl:value-of select="'HHDC Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/site-snags/hhdc-contract/org/@id}/reports/57/screen/output/?hhdc-contract-id={/source/site-snags/hhdc-contract/@id}">
						<xsl:value-of
							select="/source/site-snags/hhdc-contract/@name" />
					</a>
					&gt;
					<xsl:value-of select="'Site Snags ['" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/site-snags/hhdc-contract/org/@id}/hhdc-contracts/{/source/site-snags/hhdc-contract/@id}/site-snags/">
						<xsl:value-of select="'edit'" />
					</a>
					<xsl:value-of select="']'" />
				</p>
				<p>
					<xsl:value-of
						select="source/site-snags/@snag-count" />
					Snag(s) (older then 5 days) Total over
					<xsl:value-of
						select="source/site-snags/@site-count" />
					Site(s)
					<br />
				</p>

				<table>
					<thead>
						<tr>
							<th>Chellow Id</th>
							<th>Site ID</th>
							<th>Site Name</th>
							<th>Snag Description</th>
							<th>Duration</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each
							select="/source/site-snags/site-snag">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/site-snags/hhdc-contract/org/@id}/reports/59/screen/output/?snag-id={@id}">
										<xsl:value-of select="@id" />
									</a>
									<xsl:value-of select="' ['" />
									<a
										href="{/source/request/@context-path}/orgs/{/source/site-snags/hhdc-contract/org/@id}/hhdc-contracts/{/source/site-snags/hhdc-contract/@id}/site-snags/{@id}/">
										<xsl:value-of select="'edit'" />
									</a>
									<xsl:value-of select="']'" />
								</td>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/site-snags/hhdc-contract/org/@id}/reports/2/screen/output/?site-id={site/@id}">
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

								<td>
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