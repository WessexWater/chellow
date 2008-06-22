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
					href="{/source/request/@context-path}/orgs/{/source/site-snag/dce-service/dce/org/@id}/reports/9/stream/output/" />

				<title>
					<xsl:value-of
						select="/source/site-snag/dce-service/dce/org/@name" />
					&gt; DCEs &gt;
					<xsl:value-of
						select="/source/site-snag/dce-service/dce/@name" />
					&gt; Services &gt;
					<xsl:value-of
						select="/source/site-snag/dce-service/@name" />
					&gt; Site Snags &gt;
					<xsl:value-of select="/source/site-snag/@id" />
				</title>
			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/{/source/site-snag/dce-service/dce/org/@id}/reports/0/screen/output/">
						<xsl:value-of
							select="/source/site-snag/dce-service/dce/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/site-snag/dce-service/dce/org/@id}/reports/54/screen/output/">
						<xsl:value-of select="'DCEs'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/site-snag/dce-service/dce/org/@id}/reports/55/screen/output/?dce-id={/source/site-snag/dce-service/dce/@id}">
						<xsl:value-of
							select="/source/site-snag/dce-service/dce/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/site-snag/dce-service/dce/org/@id}/reports/56/screen/output/?dce-id={/source/site-snag/dce-service/dce/@id}">
						<xsl:value-of select="'Services'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/site-snag/dce-service/dce/org/@id}/reports/57/screen/output/?service-id={/source/site-snag/dce-service/@id}">
						<xsl:value-of
							select="/source/site-snag/dce-service/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/site-snag/dce-service/dce/org/@id}/reports/18/screen/output/?service-id={/source/site-snag/dce-service/@id}">
						<xsl:value-of select="'Site Snags'" />
					</a>
					&gt;
					<xsl:value-of
						select="concat(/source/site-snag/@id, ' [')" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/site-snag/dce-service/dce/org/@id}/dces/{/source/site-snag/dce-service/dce/@id}/services/{/source/site-snag/dce-service/@id}/site-snags/{/source/site-snag/@id}/">
						<xsl:value-of select="'edit'" />
					</a>
					<xsl:value-of select="']'" />

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
					<tbody>
						<tr>
							<th>Chellow Id</th>
							<td>
								<xsl:value-of
									select="/source/site-snag/@id" />
							</td>
						</tr>
						<tr>
							<th>Date Created</th>
							<td>
								<xsl:value-of
									select="concat(/source/site-snag/date[@label='created']/@year, '-', /source/site-snag/date[@label='created']/@month, '-', /source/site-snag/date[@label='created']/@day, 'T', /source/site-snag/date[@label='created']/@hour, ':', /source/site-snag/date[@label='created']/@minute, 'Z')" />
							</td>
						</tr>
						<tr>
							<th>Date Resolved</th>
							<td>
								<xsl:choose>
									<xsl:when
										test="/source/site-snag/date[@label='resolved']">
										<xsl:value-of
											select="concat(/source/site-snag/date[@label='resolved']/@year, '-', /source/site-snag/date[@label='resolved']/@month, '-', /source/site-snag/date[@label='resolved']/@day, 'T', /source/site-snag/date[@label='resolved']/@hour, ':', /source/site-snag/date[@label='resolved']/@minute, 'Z')" />
									</xsl:when>
									<xsl:otherwise>
										Unresolved
									</xsl:otherwise>
								</xsl:choose>
							</td>
						</tr>
						<tr>
							<th>Ignored?</th>
							<td>
								<xsl:choose>
									<xsl:when
										test="/source/site-snag/@is-ignored='true'">
										Ignored
									</xsl:when>
									<xsl:otherwise>
										Not ignored
									</xsl:otherwise>
								</xsl:choose>
							</td>
						</tr>
						<tr>
							<th>Description</th>
							<td>
								<xsl:value-of
									select="/source/site-snag/@description" />
							</td>
						</tr>
						<tr>
							<th>Progress</th>
							<td>
								<xsl:value-of
									select="/source/site-snag/@progress" />
							</td>
						</tr>
						<tr>
							<th>Site</th>
							<td>
								<a
									href="{/source/request/@context-path}/orgs/{/source/site-snag/dce-service/dce/org/@id}/reports/2/screen/output/?site-id={/source/site-snag/site/@id}">
									<xsl:value-of
										select="/source/site-snag/site/@id" />
								</a>
							</td>
						</tr>
						<tr>
							<th>Start Date</th>
							<td>
								<xsl:value-of
									select="concat(/source/site-snag/hh-end-date[@label='start']/@year, '-', /source/site-snag/hh-end-date[@label='start']/@month, '-', /source/site-snag/hh-end-date[@label='start']/@day, 'T', /source/site-snag/hh-end-date[@label='start']/@hour, ':', /source/site-snag/hh-end-date[@label='start']/@minute, 'Z')" />
							</td>
						</tr>
						<tr>
							<th>Finish Date:</th>
							<td>
								<xsl:value-of
									select="concat(/source/site-snag/hh-end-date[@label='finish']/@year, '-', /source/site-snag/hh-end-date[@label='finish']/@month, '-', /source/site-snag/hh-end-date[@label='finish']/@day, 'T', /source/site-snag/hh-end-date[@label='finish']/@hour, ':', /source/site-snag/hh-end-date[@label='finish']/@minute, 'Z')" />
							</td>
						</tr>
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>