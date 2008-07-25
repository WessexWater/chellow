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
					&gt; Providers &gt;
					<xsl:value-of select="/source/provider/@name" />
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
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/22/screen/output/">
						<xsl:value-of select="'Providers'" />
					</a>
					&gt;
					<xsl:value-of select="/source/provider/@name" />
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
					<tr>
						<th>Chellow Id</th>
						<td>
							<xsl:value-of select="/source/provider/@id" />
						</td>
					</tr>
					<tr>
						<th>Participant</th>
						<td>
							<a
								href="{/source/request/@context-path}/participants/{/source/provider/participant/@id}/">
								<xsl:value-of
									select="/source/provider/participant/@name" />
							</a>
						</td>
					</tr>
					<tr>
						<th>Role</th>
						<td>
							<a
								href="{/source/request/@context-path}/market-roles/{/source/provider/market-role/@id}/">
								<xsl:value-of
									select="/source/provider/market-role/@description" />
							</a>
						</td>
					</tr>
					<xsl:if
						test="/source/provider/market-role/@code='R'">
						<tr>
							<th>DSO Code</th>
							<td>
								<xsl:value-of
									select="/source/provider/@dso-code" />
							</td>
						</tr>
					</xsl:if>
				</table>
				<table>
					<thead>
						<tr>
							<th>Chellow Id</th>
							<th>Name</th>
							<th>Start Date</th>
							<th>Finish Date</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each
							select="/source/provider/hhdc-contract | /source/provider/dso-service | /source/provider/supplier-contract | /source/provider/mop-contract">
							<tr>
								<td>
									<xsl:choose>
										<xsl:when
											test="/source/provider/market-role/@code = 'C'">
											<a
												href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/57/screen/output/?contract-id={@id}">
												<xsl:value-of
													select="@id" />
											</a>
										</xsl:when>
										<xsl:when
											test="/source/provider/market-role/@code = 'R'">
											<a
												href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/57/screen/output/?contract-id={@id}">
												<xsl:value-of
													select="@id" />
											</a>
										</xsl:when>
									</xsl:choose>
								</td>
								<td>
									<xsl:value-of select="@name" />
								</td>
								<td>
									<xsl:value-of
										select="concat(rate-script[@label='start']/hh-end-date[@label='start']/@year, '-', rate-script[@label='start']/hh-end-date[@label='start']/@month, '-', rate-script[@label='start']/hh-end-date[@label='start']/@day)" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when
											test="rate-script[@label='finish']/hh-end-date[@label='finish']">
											<xsl:value-of
												select="concat(rate-script[@label='finish']/hh-end-date[@label='finish']/@year, '-', rate-script[@label='finish']/hh-end-date[@label='finish']/@month, '-', rate-script[@label='finish']/hh-end-date[@label='finish']/@day)" />
										</xsl:when>
										<xsl:otherwise>
											Ongoing
										</xsl:otherwise>
									</xsl:choose>
								</td>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/contracts/org/@id}/reports/23/screen/output/?provider-id={provider/@id}">
										<xsl:value-of
											select="provider/@name" />
									</a>
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
				<xsl:when
					test="/source/provider/market-role/@code = 'R'">
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
					</ul>
				</xsl:when>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

