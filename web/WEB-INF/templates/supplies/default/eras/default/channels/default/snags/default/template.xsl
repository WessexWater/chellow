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
				<title>
					Chellow &gt; Supplies &gt;
					<xsl:value-of
						select="/source/channel-snag/channel/supply-era/supply/@id" />
					&gt; Supply Generations &gt;
					<xsl:value-of select="/source/channel-snag/channel/supply-era/@id" />
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
					<a href="{/source/request/@context-path}/reports/1/output/">
						<xsl:value-of select="'Chellow'" />
					</a>
					&gt;
					<a href="{/source/request/@context-path}/reports/99/output/">
						<xsl:value-of select="'Supplies'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/reports/7/output/?supply-id={/source/channel-snag/channel/supply-era/supply/@id}">
						<xsl:value-of
							select="/source/channel-snag/channel/supply-era/supply/@id" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/channel-snag/channel/supply-era/supply/@id}/eras/{/source/channel-snag/channel/supply-era/@id}/channels/">
						<xsl:value-of
							select="concat('Generation ', /source/channel-snag/channel/supply-era/@id, ' channels')" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/channel-snag/channel/supply-era/supply/@id}/eras/{/source/channel-snag/channel/supply-era/@id}/channels/{/source/channel-snag/channel/@id}/">
						<xsl:value-of select="/source/channel-snag/channel/@id" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/channel-snag/channel/supply-era/supply/@id}/eras/{/source/channel-snag/channel/supply-era/@id}/channels/{/source/channel-snag/channel/@id}/snags/">
						<xsl:value-of select="'Snags'" />
					</a>
					&gt;
					<xsl:value-of select="/source/channel-snag/@id" />
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
								select="concat(/source/channel-snag/hh-start-date[@label='start']/@year, '-', /source/channel-snag/hh-start-date[@label='start']/@month, '-', /source/channel-snag/hh-start-date[@label='start']/@day, 'T', /source/channel-snag/hh-start-date[@label='start']/@hour, ':', /source/channel-snag/hh-start-date[@label='start']/@minute, 'Z')" />
						</td>
					</tr>
					<tr>
						<th>Finish Date</th>
						<td>
							<xsl:choose>
								<xsl:when test="source/channel-snag/hh-start-date[@label='finish']">
									<xsl:value-of
										select="concat(/source/channel-snag/hh-start-date[@label='finish']/@year, '-', /source/channel-snag/hh-start-date[@label='finish']/@month, '-', /source/channel-snag/hh-start-date[@label='finish']/@day, 'T', /source/channel-snag/hh-start-date[@label='finish']/@hour, ':', /source/channel-snag/hh-start-date[@label='finish']/@minute, 'Z')" />
								</xsl:when>
								<xsl:otherwise>
									Ongoing
								</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
					<tr>
						<th>Contract</th>
						<td>
							<a
								href="{/source/request/@context-path}/reports/117/output/?snag-id={/source/channel-snag/@id}">View Snag</a>
							&lt;
							<a
								href="{/source/request/@context-path}/reports/37/output/?hhdc-contract-id={/source/channel-snag/channel/supply-era/hhdc-contract/@id}&amp;hidden-days=5">Channel Snags</a>
							&lt;
							<a
								href="{/source/request/@context-path}/reports/115/output/?hhdc-contract-id={/source/channel-snag/channel/supply-era/hhdc-contract/@id}">Contract</a>
							&lt;
							<a
								href="{/source/request/@context-path}/reports/113/output/">HHDC Contracts</a>
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