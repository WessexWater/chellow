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
				</title>
			</head>
			<body>
				<p>
					<xsl:value-of
						select="concat(/source/org/@name, ' [')" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/">
						<xsl:value-of select="'edit'" />
					</a>
					<xsl:value-of select="']'" />
				</p>
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
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/56/screen/output/">
							HHDC Contracts
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/37/screen/output/">
							Supplier Contracts
						</a>
					</li>
				</ul>

				<h3>Bulk CSV downloads</h3>
				<ul>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/16/stream/output/">
							Electricity Supply Details
						</a>
					</li>
				</ul>

				<h3>Industry Info</h3>
				<ul>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/35/screen/output/">
							Market Participants
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/60/screen/output/">
							Market Roles
						</a>
					</li>

					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/22/screen/output/">
							Providers
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/26/screen/output/">
							Profile Classes
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/30/screen/output/">
							Meter Timeswitch Classes
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/64/screen/output/">
							Meter Types
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/66/screen/output/">
							Meter Payment Types
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/47/screen/output/">
							TPRs
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/62/screen/output/">
							SSCs
						</a>
					</li>

				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

