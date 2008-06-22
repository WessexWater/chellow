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
					&gt; DCEs &gt;
					<xsl:value-of select="/source/dce/@name" />
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
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/54/screen/output/">
						<xsl:value-of select="'DCEs'" />
					</a>
					&gt;
					<xsl:value-of
						select="concat(/source/dce/@name , ' [')" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/dces/{/source/dce/@id}/">
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
									select="/source/dce/@id" />
							</td>
						</tr>
						<tr>
							<th>Name</th>
							<td>
								<xsl:value-of
									select="/source/dce/@name" />
							</td>
						</tr>
					</tbody>
				</table>
				<ul>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/56/screen/output/?dce-id={/source/dce/@id}">
							Services
						</a>
					</li>
					<!--
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/57/screen/output/?dce-id={/source/dce/@id}">
							Accounts
						</a>
					</li>
					-->
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>