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
					href="{/source/request/@context-path}/style/" />
				<title>
					Chellow &gt; TPRs &gt;
					<xsl:value-of
						select="/source/clock-intervals/tpr/@id" />
					&gt; Clock Intervals
				</title>
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
					<xsl:value-of select="' &gt; '" />
					<a href="{/source/request/@context-path}/tprs/">
						<xsl:value-of select="'TPRs'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/tprs/{/source/clock-intervals/tpr/@id}/">
						<xsl:value-of
							select="/source/clock-intervals/tpr/@code" />
					</a>
					&gt; Clock Intervals
				</p>

				<table>
					<thead>
						<th>Chellow Id</th>
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
							select="/source/clock-intervals/clock-interval">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/tprs/{/source/clock-intervals/tpr/@id}/clock-intervals/{@id}/">
										<xsl:value-of select="@id" />
									</a>
								</td>
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
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

