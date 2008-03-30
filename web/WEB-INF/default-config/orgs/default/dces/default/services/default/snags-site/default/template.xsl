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
						select="/source/snag-site/dce-service/dce/organization/@name" />
					&gt; DCEs &gt;
					<xsl:value-of
						select="/source/snag-site/dce-service/dce/@name" />
					&gt; Contracts
					<xsl:value-of
						select="/source/snag-site/dce-service/@name" />
					&gt; Snags &gt;
					<xsl:value-of select="/source/snag-site/@id" />
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
						href="{/source/request/@context-path}/orgs/{/source/snag-site/dce-service/dce/organization/@id}/">
						<xsl:value-of
							select="/source/snag-site/dce-service/dce/organization/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/snag-site/dce-service/dce/organization/@id}/dces/">
						<xsl:value-of select="'DCEs'"/>
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/snag-site/dce-service/dce/organization/@id}/dces/{/source/snag-site/dce-service/dce/@id}/">
						<xsl:value-of
							select="/source/snag-site/dce-service/dce/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/snag-site/dce-service/dce/organization/@id}/dces/{/source/snag-site/dce-service/dce/@id}/services/">
						<xsl:value-of select="'Services'"/>
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/snag-site/dce-service/dce/organization/@id}/dces/{/source/snag-site/dce-service/dce/@id}/services/{/source/snag-site/dce-service/@id}/">
						<xsl:value-of
							select="/source/snag-site/dce-service/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/snag-site/dce-service/dce/organization/@id}/dces/{/source/snag-site/dce-service/dce/@id}/services/{/source/snag-site/dce-service/@id}/snags-site/">
						Site Snags
					</a>
					&gt;
					<xsl:value-of select="/source/snag-site/@id" />
				</p>
				<br />

				<ul>
					<li>
						Date Created:
						<xsl:value-of
							select="concat(/source/snag-site/date[@label='created']/@year, '-', /source/snag-site/date[@label='created']/@month, '-', /source/snag-site/date[@label='created']/@day)" />
					</li>
					<li>
						Date Resolved:
						<xsl:choose>
							<xsl:when
								test="/source/snag-site/date[@label='resolved']">
								<xsl:value-of
									select="concat(/source/snag-site/date[@label='resolved']/@year, '-', /source/snag-site/date[@label='resolved']/@month, '-', /source/snag-site/date[@label='resolved']/@day)" />
							</xsl:when>
							<xsl:otherwise>Unresolved</xsl:otherwise>
						</xsl:choose>
					</li>
					<li>
						Ignored?:
						<xsl:value-of
							select="/source/snag-site/@is-ignored" />
					</li>
					<li>
						Description:
						<xsl:value-of
							select="/source/snag-site/@description" />
					</li>
					<li>
						Progress:
						<xsl:value-of
							select="/source/snag-site/@progress" />
					</li>

					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/snag-site/dce-service/dce/organization/@id}/sites/{/source/snag-site/site/@id}/">
							Site
						</a>
					</li>

					<li>
						Start Date:
						<xsl:value-of
							select="concat(/source/snag-site/hh-end-date[@label='start']/@year, '-', /source/snag-site/hh-end-date[@label='start']/@month, '-', /source/snag-site/hh-end-date[@label='start']/@day)" />
					</li>
					<li>
						Finish Date:
						<xsl:value-of
							select="concat(/source/snag-site/hh-end-date[@label='finish']/@year, '-', /source/snag-site/hh-end-date[@label='finish']/@month, '-', /source/snag-site/hh-end-date[@label='finish']/@day)" />
					</li>
				</ul>
				<xsl:if
					test="not(/source/snag-site/date[@label='resolved']) or (/source/snag-site/date[@label='resolved'] and /source/snag-site/@is-ignored='true')">
					<form action="." method="post">
						<fieldset>
							<legend>Update snag</legend>
							<input type="hidden" name="ignore">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
											test="/source/snag-site/@is-ignored='true'">
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
											test="/source/snag-site/@is-ignored='true'">
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