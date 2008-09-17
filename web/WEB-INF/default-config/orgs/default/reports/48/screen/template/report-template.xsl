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
					&gt; TPRs &gt;
					<xsl:value-of select="/source/tpr/@code" />
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
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/47/screen/output/">
						<xsl:value-of select="'TPRs'" />
					</a>
					&gt;
					<xsl:value-of select="/source/tpr/@code" />
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
							<xsl:value-of select="/source/tpr/@id" />
						</td>
					</tr>
					<tr>
						<th>Code</th>
						<td>
							<xsl:value-of select="/source/tpr/@code" />
						</td>
					</tr>
					<tr>
						<th>Teleswitch or Clock</th>
						<td>
							<xsl:choose>
								<xsl:when
									test="/source/tpr/@is-teleswitch='true'">
									Teleswitch
								</xsl:when>
								<xsl:otherwise>Clock</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
					<tr>
						<th>GMT or Clock Time</th>
						<td>
							<xsl:choose>
								<xsl:when test="@is-gmt='true'">
									GMT
								</xsl:when>
								<xsl:otherwise>
									Clock Time
								</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
				</table>
				<br />
				<table>
					<caption>Clock Intervals</caption>
					<thead>
						<th>Day Of Week</th>
						<th>Start Day</th>
						<th>Start Month</th>
						<th>End Day</th>
						<th>End Month</th>
						<th>Start Hour</th>
						<th>Start Minute</th>
						<th>End Hour</th>
						<th>End Minute</th>
					</thead>
					<tbody>
						<xsl:for-each
							select="/source/tpr/clock-interval">
							<tr>
								<td>
									<xsl:value-of select="@day-of-week" />
								</td>
								<td>
									<xsl:value-of select="@start-day" />
								</td>
								<td>
									<xsl:value-of select="@start-month" />
								</td>
								<td>
									<xsl:value-of select="@end-day" />
								</td>
								<td>
									<xsl:value-of select="@end-month" />
								</td>
								<td>
									<xsl:value-of select="@start-hour" />
								</td>
								<td>
									<xsl:value-of
										select="@start-minute" />
								</td>
								<td>
									<xsl:value-of select="@end-hour" />
								</td>
								<td>
									<xsl:value-of select="@end-minute" />
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>

				<h3>SSCs</h3>

				<ul>
					<xsl:for-each
						select="/source/tpr/measurement-requirement/ssc">
						<li>
							<a
								href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/63/screen/output/?ssc-id={@id}">
								<xsl:value-of select="@code"></xsl:value-of>
							</a>
						</li>
					</xsl:for-each>
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>