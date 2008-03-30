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

				<title>Chellow</title>

			</head>
			<body>
				<p>
					<img src="{/source/request/@context-path}/logo/" />
					<span class="logo">Chellow</span>
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
						<a
							href="{/source/request/@context-path}/orgs/1/reports/1/screen/output/">
							Sites
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/1/reports/16/stream/output/">
							Electricity Suppy Details
						</a>
						(save file, add extension .csv and open)
					</li>
					<li>
						DCEs
						<ul>
							<xsl:for-each
								select="/source/organization/dce">
								<li>
									<xsl:value-of select="@name" />
									<ul>
										<li>
											<a
												href="{/source/request/@context-path}/orgs/1/reports/18/screen/output/?dce-id={@id}">
												Channel Level Snags
											</a>
										</li>
										<li>
											<a
												href="{/source/request/@context-path}/orgs/1/reports/19/screen/output/?dce-id={@id}">
												Site Level Snags
											</a>
										</li>

										<!--
											<xsl:for-each select="dce-service">
											<li><a href="{/source/request/@context-path}/orgs/1/reports/17/screen/output/?dce-service-id={@id}"><xsl:value-of select="@name"/></a></li>
											</xsl:for-each>
										-->
									</ul>
								</li>
							</xsl:for-each>
						</ul>
					</li>
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

