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
				</title>
			</head>
			<body>
				<p>
					<xsl:value-of
						select="concat(/source/org/@name, ' [')" />
					<a href="{/source/request/@context-path}/orgs/1/">
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
				<ul>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/1/screen/output/">
							Sites
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/49/screen/output/">
							Supplies
						</a>
					</li>

					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/54/screen/output/">
							DCEs
						</a>
					</li>
					<li>
						<ul>
							<xsl:for-each select="/source/org/dce">
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
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/35/screen/output/">
							Suppliers
						</a>
					</li>
				</ul>

				<h3>Bulk CSV downloads</h3>
				<ul>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/1/reports/16/stream/output/">
							Electricity Supply Details
						</a>
					</li>
				</ul>

				<h3>Industry Info</h3>
				<ul>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/1/reports/22/screen/output/">
							DSOs
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/1/reports/26/screen/output/">
							Profile Classes
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/30/screen/output/">
							Meter Timeswitches
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/47/screen/output/">
							TPRs
						</a>
					</li>
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

