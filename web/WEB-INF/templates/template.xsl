<?xml version="1.0" encoding="us-ascii"?>
<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="html" encoding="US-ASCII"
		doctype-public="-//W3C//DTD HTML 4.01//EN" doctype-system="http://www.w3.org/TR/html4/strict.dtd"
		indent="yes" />
	<xsl:template match="/">
		<html>
			<head>
				<link rel="stylesheet" type="text/css"
					href="{/source/request/@context-path}/reports/19/output/" />
				<title>Chellow</title>
			</head>
			<body>
				<p>
					<img src="{/source/request/@context-path}/logo/" />
					<span class="logo">Chellow</span>
				</p>
				<xsl:if test="//message">
					<ul>
						<xsl:for-each select="//message">
							<li class="error">
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>
					
				<h2>Industry Info</h2>
				
					
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>