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
					<caption>Lines</caption>
					<thead>
						<th>Month From</th>
						<th>Month To</th>
						<th>Day Of Week From</th>
						<th>Day Of Week To</th>
						<th>Hour From</th>
						<th>Minute From</th>
						<th>Hour To</th>
						<th>Minute To</th>
						<th>Is Gmt?</th>
					</thead>
					<tbody>
						<xsl:for-each select="/source/tpr/tpr-line">
							<tr>
								<td>
									<xsl:value-of select="@month-from" />
								</td>
								<td>
									<xsl:value-of select="@month-to" />
								</td>
								<td>
									<xsl:value-of
										select="@day-of-week-from" />
								</td>
								<td>
									<xsl:value-of
										select="@day-of-week-to" />
								</td>
								<td>
									<xsl:value-of select="@hour-from" />
								</td>
								<td>
									<xsl:value-of select="@minute-from" />
								</td>
								<td>
									<xsl:value-of select="@hour-to" />
								</td>
								<td>
									<xsl:value-of select="@minute-to" />
								</td>
								<td>
									<xsl:value-of select="@is-gmt" />
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
				<h3>SSCs</h3>
				<xsl:if test="/source/tpr/ssc">
					<ul>
						<xsl:for-each select="/source/tpr/ssc">
							<li>
								<a
									href="{/source/request/@context-path}/sscs/{@id}/">
									<xsl:value-of select="@code" />
								</a>
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>