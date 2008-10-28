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
					href="{/source/request/@context-path}/style/" />
				<title>
					Chellow &gt; HHDC Contracts
					<xsl:value-of
						select="/source/channel-snag/hhdc-contract/@name" />
					&gt; Channel Snags &gt;
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
						<img
							src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/hhdc-contracts/">
						<xsl:value-of select="'HHDC Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/hhdc-contracts/{/source/channel-snag/hhdc-contract/@id}/">
						<xsl:value-of
							select="/source/channel-snag/hhdc-contract/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/hhdc-contracts/{/source/channel-snag/hhdc-contract/@id}/channel-snags/">
						<xsl:value-of select="'Channel Snags'" />
					</a>
					&gt;
					<xsl:value-of
						select="concat(/source/channel-snag/@id, ' [')" />
					<a
						href="{/source/request/@context-path}/reports/59/output/?snag-id={/source/channel-snag/@id}">
						<xsl:value-of select="'view'" />
					</a>
					<xsl:value-of select="']'" />
				</p>
				<br />
				<ul>
					<li>
						Date Created:
						<xsl:value-of
							select="concat(/source/channel-snag/date[@label='created']/@year, '-', /source/channel-snag/date[@label='created']/@month, '-', /source/channel-snag/date[@label='created']/@day, 'T', /source/channel-snag/date[@label='created']/@hour, ':', /source/channel-snag/date[@label='created']/@minute, 'Z')" />
					</li>
					<li>
						Date Resolved:
						<xsl:choose>
							<xsl:when
								test="/source/channel-snag/date[@label='resolved']">
								<xsl:value-of
									select="concat(/source/channel-snag/date[@label='resolved']/@year, '-', /source/channel-snag/date[@label='resolved']/@month, '-', /source/channel-snag/date[@label='resolved']/@day, 'T', /source/channel-snag/date[@label='resolved']/@hour, ':', /source/channel-snag/date[@label='resolved']/@minute, 'Z')" />
							</xsl:when>
							<xsl:otherwise>Unresolved</xsl:otherwise>
						</xsl:choose>
					</li>
					<li>
						Ignored?:
						<xsl:value-of
							select="/source/channel-snag/@is-ignored" />
					</li>
					<li>
						Description:
						<xsl:value-of
							select="/source/channel-snag/@description" />
					</li>
					<li>
						Progress:
						<xsl:value-of
							select="/source/channel-snag/@progress" />
					</li>

					<li>
						<a
							href="{/source/request/@context-path}/supplies/{/source/channel-snag/channel/supply-generation/supply/@id}/generations/{/source/channel-snag/channel/supply-generation/@id}/channels/{/source/channel-snag/channel/@id}/">
							Channel
						</a>
					</li>

					<li>
						Start Date:
						<xsl:value-of
							select="concat(/source/channel-snag/hh-end-date[@label='start']/@year, '-', /source/channel-snag/hh-end-date[@label='start']/@month, '-', /source/channel-snag/hh-end-date[@label='start']/@day, 'T', /source/channel-snag/hh-end-date[@label='start']/@hour, ':', /source/channel-snag/hh-end-date[@label='start']/@minute, 'Z')" />
					</li>
					<li>
						Finish Date:
						<xsl:value-of
							select="concat(/source/channel-snag/hh-end-date[@label='finish']/@year, '-', /source/channel-snag/hh-end-date[@label='finish']/@month, '-', /source/channel-snag/hh-end-date[@label='finish']/@day, 'T', /source/channel-snag/hh-end-date[@label='finish']/@hour, ':', /source/channel-snag/hh-end-date[@label='finish']/@minute, 'Z')" />
					</li>
				</ul>
				<xsl:if
					test="not(/source/channel-snag/date[@label='resolved']) or (/source/channel-snag/date[@label='resolved'] and /source/channel-snag/@is-ignored='true')">
					<form action="." method="post">
						<fieldset>
							<legend>Update snag</legend>
							<input type="hidden" name="ignore">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
											test="/source/channel-snag/@is-ignored='true'">
											<xsl:value-of
												select="'false'" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
												select="'true'" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
							</input>
							<input type="submit">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
											test="/source/channel-snag/@is-ignored='true'">
											<xsl:value-of
												select="'Un-ignore'" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
												select="'Ignore'" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
							</input>
						</fieldset>
					</form>
				</xsl:if>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>