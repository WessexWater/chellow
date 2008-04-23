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
					<xsl:value-of select="/source/org/@name" />
					&gt; DSOs &gt;
					<xsl:value-of select="/source/dso/@code" />
				</title>
			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/1/reports/0/screen/output/">
						<xsl:value-of select="/source/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/1/reports/22/screen/output/">
						<xsl:value-of select="'DSOs'"/>
					</a>
					&gt;
					<xsl:value-of select="/source/dso/@code" />
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
				<ul>
					<li>
						Code:
						<xsl:value-of select="/source/dso/@code" />
					</li>
					<li>
						Name:
						<xsl:value-of select="/source/dso/@name" />
					</li>
				</ul>
				<ul>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/24/screen/output/?dso-id={/source/dso/@id}">
							Line Loss Factors
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/28/screen/output/?dso-id={/source/dso/@id}">
							MPAN top lines
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/32/screen/output/?dso-id={/source/dso/@id}">
							Services
						</a>
					</li>
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

