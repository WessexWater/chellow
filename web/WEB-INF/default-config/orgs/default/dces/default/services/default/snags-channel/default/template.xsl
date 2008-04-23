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
					Chellow &gt; Organizations &gt;
					<xsl:value-of
						select="/source/snag-channel/dce-service/dce/org/@name" />
					&gt; DCEs &gt;
					<xsl:value-of
						select="/source/snag-channel/dce-service/dce/@name" />
					&gt; dce-services
					<xsl:value-of
						select="/source/snag-channel/dce-service/@name" />
					&gt; Snags &gt;
					<xsl:value-of select="/source/snag-channel/@id" />
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
					<a href="{/source/request/@context-path}/orgs/">
						<xsl:value-of select="'Organizations'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/snag-channel/dce-service/dce/org/@id}/">
						<xsl:value-of
							select="/source/snag-channel/dce-service/dce/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/snag-channel/dce-service/dce/org/@id}/dces/">
						<xsl:value-of select="'DCEs'"/>
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/snag-channel/dce-service/dce/org/@id}/dces/{/source/snag-channel/dce-service/dce/@id}/">
						<xsl:value-of
							select="/source/snag-channel/dce-service/dce/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/snag-channel/dce-service/dce/org/@id}/dces/{/source/snag-channel/dce-service/dce/@id}/services/">
						<xsl:value-of select="'Services'"/>
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/snag-channel/dce-service/dce/org/@id}/dces/{/source/snag-channel/dce-service/dce/@id}/services/{/source/snag-channel/dce-service/@id}/">
						<xsl:value-of
							select="/source/snag-channel/dce-service/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/snag-channel/dce-service/dce/org/@id}/dces/{/source/snag-channel/dce-service/dce/@id}/services/{/source/snag-channel/dce-service/@id}/snags-channel/">
						<xsl:value-of select="'Channel Snags'"/>
					</a>
					&gt;
					<xsl:value-of select="/source/snag-channel/@id" />
				</p>
				<br />

				<ul>
					<li>
						Date Created:
						<xsl:value-of
							select="concat(/source/snag-channel/date[@label='created']/@year, '-', /source/snag-channel/date[@label='created']/@month, '-', /source/snag-channel/date[@label='created']/@day, 'T', /source/snag-channel/date[@label='created']/@hour, ':', /source/snag-channel/date[@label='created']/@minute, 'Z')" />
					</li>
					<li>
						Date Resolved:
						<xsl:choose>
							<xsl:when
								test="/source/snag-channel/date[@label='resolved']">
								<xsl:value-of
									select="concat(/source/snag-channel/date[@label='resolved']/@year, '-', /source/snag-channel/date[@label='resolved']/@month, '-', /source/snag-channel/date[@label='resolved']/@day, 'T', /source/snag-channel/date[@label='resolved']/@hour, ':', /source/snag-channel/date[@label='resolved']/@minute, 'Z')" />
							</xsl:when>
							<xsl:otherwise>Unresolved</xsl:otherwise>
						</xsl:choose>
					</li>
					<li>
						Ignored?:
						<xsl:value-of
							select="/source/snag-channel/@is-ignored" />
					</li>
					<li>
						Description:
						<xsl:value-of
							select="/source/snag-channel/@description" />
					</li>
					<li>
						Progress:
						<xsl:value-of
							select="/source/snag-channel/@progress" />
					</li>

					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/snag-channel/dce-service/dce/org/@id}/supplies/{/source/snag-channel/channel/supply/@id}/channels/{/source/snag-channel/channel/@id}/">
							Channel
						</a>
					</li>

					<li>
						Start Date:
						<xsl:value-of
							select="concat(/source/snag-channel/hh-end-date[@label='start']/@year, '-', /source/snag-channel/hh-end-date[@label='start']/@month, '-', /source/snag-channel/hh-end-date[@label='start']/@day, 'T', /source/snag-channel/hh-end-date[@label='start']/@hour, ':', /source/snag-channel/hh-end-date[@label='start']/@minute, 'Z')" />
					</li>
					<li>
						Finish Date:
						<xsl:value-of
							select="concat(/source/snag-channel/hh-end-date[@label='finish']/@year, '-', /source/snag-channel/hh-end-date[@label='finish']/@month, '-', /source/snag-channel/hh-end-date[@label='finish']/@day, 'T', /source/snag-channel/hh-end-date[@label='finish']/@hour, ':', /source/snag-channel/hh-end-date[@label='finish']/@minute, 'Z')" />
					</li>
				</ul>
				<xsl:if
					test="not(/source/snag-channel/date[@label='resolved']) or (/source/snag-channel/date[@label='resolved'] and /source/snag-channel/@is-ignored='true')">
					<form action="." method="post">
						<fieldset>
							<legend>Update snag</legend>
							<input type="hidden" name="ignore">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
											test="/source/snag-channel/@is-ignored='true'">
											<xsl:value-of select="'false'"/>
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of select="'true'"/>
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
							</input>
							<input type="submit">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
											test="/source/snag-channel/@is-ignored='true'">
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