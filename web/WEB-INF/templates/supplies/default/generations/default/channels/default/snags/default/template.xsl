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
						select="/source/channel-snag/channel/supply-generation/supply/@id" />
					&gt; Supply Generations &gt;
					<xsl:value-of select="/source/channel-snag/channel/supply-generation/@id" />
					&gt; Channels &gt;
					<xsl:value-of select="/source/channel-snag/channel/@id" />
					&gt; Snags &gt;
					<xsl:value-of select="/source/channel-snag/@id" />
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
						href="{/source/request/@context-path}/supplies/{/source/channel-snag/channel/supply-generation/supply/@id}/">
						<xsl:value-of
							select="/source/channel-snag/channel/supply-generation/supply/@id" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/channel-snag/channel/supply-generation/supply/@id}/generations/">
						<xsl:value-of select="'Generations'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/channel-snag/channel/supply-generation/supply/@id}/generations/{/source/channel-snag/channel/supply-generation/@id}/">
						<xsl:value-of select="/source/channel-snag/channel/supply-generation/@id" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/channel-snag/channel/supply-generation/supply/@id}/generations/{/source/channel-snag/channel/supply-generation/@id}/channels/">
						<xsl:value-of select="'Channels'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/channel-snag/channel/supply-generation/supply/@id}/generations/{/source/channel-snag/channel/supply-generation/@id}/channels/{/source/channel-snag/channel/@id}/">
						<xsl:value-of select="/source/channel-snag/channel/@id" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/channel-snag/channel/supply-generation/supply/@id}/generations/{/source/channel-snag/channel/supply-generation/@id}/channels/{/source/channel-snag/channel/@id}/snags/">
						<xsl:value-of select="'Snags'" />
					</a>
					&gt;
					<xsl:value-of select="concat(/source/channel-snag/@id, ' [')" />
					<a
						href="{/source/request/@context-path}/reports/117/output/?snag-id={/source/channel-snag/@id}">
						<xsl:value-of select="'view'" />
					</a>
					<xsl:value-of select="']'" />
				</p>
				<br />
				<table>
					<tr>
						<th>Date Created</th>
						<td>
							<xsl:value-of
								select="concat(/source/channel-snag/date[@label='created']/@year, '-', /source/channel-snag/date[@label='created']/@month, '-', /source/channel-snag/date[@label='created']/@day, 'T', /source/channel-snag/date[@label='created']/@hour, ':', /source/channel-snag/date[@label='created']/@minute, 'Z')" />
						</td>
					</tr>
					<tr>
						<th>Ignored</th>
						<td>
							<xsl:value-of select="/source/channel-snag/@is-ignored" />
						</td>
					</tr>
					<tr>
						<th>Description</th>
						<td>
							<xsl:value-of select="/source/channel-snag/@description" />
						</td>
					</tr>
					<tr>
						<th>Start Date</th>
						<td>
							<xsl:value-of
								select="concat(/source/channel-snag/hh-end-date[@label='start']/@year, '-', /source/channel-snag/hh-end-date[@label='start']/@month, '-', /source/channel-snag/hh-end-date[@label='start']/@day, 'T', /source/channel-snag/hh-end-date[@label='start']/@hour, ':', /source/channel-snag/hh-end-date[@label='start']/@minute, 'Z')" />
						</td>
					</tr>
					<tr>
						<th>Finish Date</th>
						<td>
							<xsl:choose>
							<xsl:when test="source/channel-snag/hh-end-date[@label='finish']">
								<xsl:value-of
									select="concat(/source/channel-snag/hh-end-date[@label='finish']/@year, '-', /source/channel-snag/hh-end-date[@label='finish']/@month, '-', /source/channel-snag/hh-end-date[@label='finish']/@day, 'T', /source/channel-snag/hh-end-date[@label='finish']/@hour, ':', /source/channel-snag/hh-end-date[@label='finish']/@minute, 'Z')" />
									</xsl:when>
							<xsl:otherwise>Ongoing</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
				</table>
				<br />
				<form action="." method="post">
					<fieldset>
						<legend>Update snag</legend>
						<input type="hidden" name="ignore">
							<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when test="/source/channel-snag/@is-ignored='true'">
											<xsl:value-of select="'false'" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of select="'true'" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
						</input>
						<input type="submit">
							<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when test="/source/channel-snag/@is-ignored='true'">
											<xsl:value-of select="'Un-ignore'" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of select="'Ignore'" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
						</input>
					</fieldset>
				</form>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>