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
					<xsl:value-of select="/source/org/@name"/> &gt; Meter Timeswitches &gt;
					<xsl:value-of
						select="/source/meter-timeswitch/@code" />
				</title>
			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/0/screen/output/">
						<xsl:value-of select="/source/org/@name"/>
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/30/screen/output/">
						<xsl:value-of select="'Meter Timeswitches'" />
					</a>
					&gt;
					<xsl:value-of
						select="/source/meter-timeswitch/@code" />
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
					<caption>Properties</caption>
					<thead>
						<tr>
							<th>Name</th>
							<th>Value</th>
						</tr>
					</thead>
					<tbody>
						<tr>
							<td>Id</td>
							<td>
								<xsl:value-of
									select="/source/meter-timeswitch/@id" />
							</td>
						</tr>
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
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>