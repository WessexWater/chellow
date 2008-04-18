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
					<xsl:value-of select="/source/organization/@name" />
					&gt; DSOs &gt;
					<xsl:value-of select="/source/services/dso/@code" />
					&gt; Services
				</title>
			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/1/reports/0/screen/output/">
						<xsl:value-of
							select="/source/organization/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/1/reports/22/screen/output/">
						<xsl:value-of select="'DSOs'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/1/reports/23/screen/output/?dso-id={/source/mpan-tops/dso/@id}">
						<xsl:value-of
							select="/source/services/dso/@code" />
					</a>
					&gt; Services
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
							<th>Name</th>
							<th>Start Date</th>
							<th>Finish Date</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each
							select="/source/services/dso-service">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/1/reports/33/screen/output/?service-id={@id}">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<xsl:value-of select="@name" />
								</td>
								<td>
									<xsl:value-of
										select="concat(rate-script[@label='start']/hh-end-date[@label='start']/@year, '-', rate-script[@label='start']/hh-end-date[@label='start']/@month, '-', rate-script[@label='start']/hh-end-date[@label='start']/@day)" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when
											test="rate-script[@label='finish']/hh-end-date[@label='finish']">
											<xsl:value-of
												select="concat(rate-script[@label='finish']/hh-end-date[@label='finish']/@year, '-', rate-script[@label='finish']/hh-end-date[@label='finish']/@month, '-', rate-script[@label='finish']/hh-end-date[@label='finish']/@day)" />
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