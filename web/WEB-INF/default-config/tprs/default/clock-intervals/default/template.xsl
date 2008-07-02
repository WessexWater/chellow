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
						select="/source/clock-interval/tpr/@id" />
					&gt; Clock Intervals &gt;
					<xsl:value-of select="/source/clock-interval/@id" />
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
						href="{/source/request/@context-path}/tprs/{/source/clock-interval/tpr/@id}/">
						<xsl:value-of
							select="/source/clock-interval/tpr/@code" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/tprs/{/source/clock-interval/tpr/@id}/clock-intervals/">
						<xsl:value-of select="'Clock Intervals'" />
					</a>
					&gt;
					<xsl:value-of select="/source/clock-interval/@id" />
				</p>

				<table>
					<tr>
						<th>Chellow Id</th>
						<td>
							<xsl:value-of
								select="/source/clock-interval/@id" />
						</td>
					</tr>
					<tr>
						<th>Day Of Week</th>
						<td>
							<xsl:value-of
								select="/source/clock-interval/@day-of-week" />
						</td>

					</tr>
					<tr>
						<th>Start Day</th>
						<td>
							<xsl:value-of
								select="/source/clock-interval/@start-day" />
						</td>

					</tr>
					<tr>
						<th>Start Month</th>
						<td>
							<xsl:value-of
								select="/source/clock-interval/@start-month" />
						</td>
					</tr>
					<tr>
						<th>End Day</th>
						<td>
							<xsl:value-of
								select="/source/clock-interval/@end-day" />
						</td>
					</tr>
					<tr>
						<th>End Month</th>
						<td>
							<xsl:value-of
								select="/source/clock-interval/@end-month" />
						</td>

					</tr>
					<tr>
						<th>Start Hour</th>
						<td>
							<xsl:value-of
								select="/source/clock-interval/@start-hour" />
						</td>
					</tr>
					<tr>
						<th>Start Minute</th>
						<td>
							<xsl:value-of
								select="/source/clock-interval/@start-minute" />
						</td>
					</tr>
					<tr>
						<th>End Hour</th>
						<td>
							<xsl:value-of
								select="/source/clock-interval/@end-hour" />
						</td>
					</tr>
					<tr>
						<th>End Minute</th>
						<td>
							<xsl:value-of
								select="/source/clock-interval/@end-minute" />
						</td>
					</tr>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>