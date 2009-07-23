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
					href="{/source/request/@context-path}/style/" />
				<title>
					Chellow &gt; Supplies &gt;
					<xsl:value-of
						select="/source/channel-snags/channel/supply-generation/supply/@id" />
					&gt; Supply Generations &gt;
					<xsl:value-of select="/source/channel-snags/channel/supply-generation/@id" />
					&gt; Channels &gt;
					<xsl:value-of select="/source/channel-snags/channel/@id" />
					&gt; Snags
				</title>
			</head>
			<body>
				<xsl:if test="//message">
					<ul>
						<xsl:for-each select="//message">
							<li>
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>
				<p>
					<a href="{/source/request/@context-path}/">
						<img src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					&gt;
					<a href="{/source/request/@context-path}/supplies/">
						<xsl:value-of select="'Supplies'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/channel-snags/channel/supply-generation/supply/@id}/">
						<xsl:value-of
							select="/source/channel-snags/channel/supply-generation/supply/@id" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/channel-snags/channel/supply-generation/supply/@id}/generations/">
						<xsl:value-of select="'Generations'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/channel-snags/channel/supply-generation/supply/@id}/generations/{/source/channel-snags/channel/supply-generation/@id}/">
						<xsl:value-of
							select="/source/channel-snags/channel/supply-generation/@id" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/channel-snags/channel/supply-generation/supply/@id}/generations/{/source/channel-snags/channel/supply-generation/@id}/channels/">
						<xsl:value-of select="'Channels'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/channel-snags/channel/supply-generation/supply/@id}/generations/{/source/channel-snags/channel/supply-generation/@id}/channels/{/source/channel-snags/channel/@id}/">
						<xsl:value-of select="/source/channel-snags/channel/@id" />
					</a>
					&gt;
					<xsl:value-of select="'Snags ['" />
					<a
						href="{/source/request/@context-path}/reports/37/output/?hhdc-contract-id={/source/channel-snags/channel/supply-generation/account/hhdc-contract/@id}">
						<xsl:value-of select="'view'" />
					</a>
					<xsl:value-of select="']'" />
				</p>
				<br />
				<table>
					<caption>Channel</caption>
					<tbody>
						<tr>
							<td>
								<xsl:choose>
									<xsl:when test="/source/channel-snags/channel/@is-import='true'">
										<xsl:value-of select="'import'" />
									</xsl:when>
									<xsl:otherwise>
										<xsl:value-of select="'export'" />
									</xsl:otherwise>
								</xsl:choose>
							</td>
							<td>
								<xsl:choose>
									<xsl:when test="/source/channel-snags/channel/@is-kwh='true'">
										<xsl:value-of select="'kWh'" />
									</xsl:when>
									<xsl:otherwise>
										<xsl:value-of select="'kVArh'" />
									</xsl:otherwise>
								</xsl:choose>
							</td>
						</tr>
					</tbody>
				</table>
				<br />
				<table>
					<caption>Snags</caption>
					<thead>
						<tr>
							<th>Chellow Id</th>
							<th>Snag Type</th>
							<th>Start</th>
							<th>Finish</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each select="/source/channel-snags/channel-snag">
							<tr>
								<td>
									<a href="{@id}/">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<xsl:value-of select="@description" />
								</td>
								<td>
									<xsl:value-of
										select="concat(hh-end-date[@label='start']/@year, '-', hh-end-date[@label='start']/@month, '-', hh-end-date[@label='start']/@day, 'T', hh-end-date[@label='start']/@hour, ':', hh-end-date[@label='start']/@minute, 'Z')" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when test="hh-end-date[@label='finish']">
											<xsl:value-of
												select="concat(hh-end-date[@label='finish']/@year, '-', hh-end-date[@label='finish']/@month, '-', hh-end-date[@label='finish']/@day, 'T', hh-end-date[@label='finish']/@hour, ':', hh-end-date[@label='finish']/@minute, 'Z')" />
										</xsl:when>
										<xsl:otherwise>
											Ongoing
										</xsl:otherwise>
									</xsl:choose>
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>