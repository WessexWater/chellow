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
					Chellow &gt; HHDC Contracts &gt;
					<xsl:value-of
						select="/source/site-snag/hhdc-contract/@name" />
					&gt; Site Snags &gt;
					<xsl:value-of select="/source/site-snag/@id" />
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
						href="{/source/request/@context-path}/hhdc-contracts/{/source/site-snag/hhdc-contract/@id}/">
						<xsl:value-of
							select="/source/site-snag/hhdc-contract/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/hhdc-contracts/{/source/site-snag/hhdc-contract/@id}/site-snags/">
						Site Snags
					</a>
					&gt;
					<xsl:value-of
						select="concat(/source/site-snag/@id, ' [')" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/site-snag/hhdc-contract/org/@id}/reports/59/screen/output/?snag-id={/source/site-snag/@id}">
						<xsl:value-of select="'view'" />
					</a>
					<xsl:value-of select="']'" />
				</p>
				<br />
				<ul>
					<li>
						Date Created:
						<xsl:value-of
							select="concat(/source/site-snag/date[@label='created']/@year, '-', /source/site-snag/date[@label='created']/@month, '-', /source/site-snag/date[@label='created']/@day)" />
					</li>
					<li>
						Date Resolved:
						<xsl:choose>
							<xsl:when
								test="/source/site-snag/date[@label='resolved']">
								<xsl:value-of
									select="concat(/source/site-snag/date[@label='resolved']/@year, '-', /source/site-snag/date[@label='resolved']/@month, '-', /source/site-snag/date[@label='resolved']/@day)" />
							</xsl:when>
							<xsl:otherwise>Unresolved</xsl:otherwise>
						</xsl:choose>
					</li>
					<li>
						Ignored?:
						<xsl:value-of
							select="/source/site-snag/@is-ignored" />
					</li>
					<li>
						Description:
						<xsl:value-of
							select="/source/site-snag/@description" />
					</li>
					<li>
						Progress:
						<xsl:value-of
							select="/source/site-snag/@progress" />
					</li>

					<li>
						<a
							href="{/source/request/@context-path}/sites/{/source/site-snag/site/@id}/">
							Site
						</a>
					</li>
					<li>
						Start Date:
						<xsl:value-of
							select="concat(/source/site-snag/hh-end-date[@label='start']/@year, '-', /source/site-snag/hh-end-date[@label='start']/@month, '-', /source/site-snag/hh-end-date[@label='start']/@day)" />
					</li>
					<li>
						Finish Date:
						<xsl:value-of
							select="concat(/source/site-snag/hh-end-date[@label='finish']/@year, '-', /source/site-snag/hh-end-date[@label='finish']/@month, '-', /source/site-snag/hh-end-date[@label='finish']/@day)" />
					</li>
				</ul>
				<xsl:if
					test="not(/source/site-snag/date[@label='resolved']) or (/source/site-snag/date[@label='resolved'] and /source/site-snag/@is-ignored='true')">
					<form action="." method="post">
						<fieldset>
							<legend>Update snag</legend>
							<input type="hidden" name="ignore">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
											test="/source/site-snag/@is-ignored='true'">
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
											test="/source/site-snag/@is-ignored='true'">
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