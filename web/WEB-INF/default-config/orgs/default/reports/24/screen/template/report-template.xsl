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
					<xsl:value-of select="/source/organization/@name" /> &gt; DSOs &gt;
					<xsl:value-of select="/source/llfs/dso/@code" />
					&gt; Line Loss Factors
				</title>
			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/1/reports/0/screen/output/">
						<xsl:value-of select="/source/organization/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/1/reports/22/screen/output/">
						DSOs
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/1/reports/23/screen/output/?dso-id={/source/llfs/dso/@id}">
						<xsl:value-of select="/source/llfs/dso/@code" />
					</a>
					&gt; Line Loss Factors
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
							<th>Code</th>
							<th>Description</th>
							<th>Voltage Level</th>
							<th>Is Substation?</th>
							<th>Is Import?</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each
							select="/source/llfs/llf">
							<tr>
								<td>
									<a href="{/source/request/@context-path}/orgs/1/reports/25/screen/output/?llf-id={@id}">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<xsl:value-of select="@code" />
								</td>
								<td>
									<xsl:value-of select="@description" />
								</td>
								<td>
									<xsl:value-of
										select="concat(voltage-level/@code, ' - ', voltage-level/@name)" />
								</td>
								<td>
									<xsl:value-of
										select="@is-substation" />
								</td>
								<td>
									<xsl:value-of select="@is-import" />
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

