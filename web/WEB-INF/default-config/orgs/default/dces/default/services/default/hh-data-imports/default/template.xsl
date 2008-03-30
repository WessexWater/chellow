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
						select="/source/hh-data-import/dce-service/dce/organization/@name" />
					&gt; DCEs &gt;
					<xsl:value-of
						select="/source/hh-data-import/dce-service/dce/@name" />
					&gt; Services &gt;
					<xsl:value-of
						select="/source/hh-data-import/dce-service/@name" />
					&gt; HH Data Imports &gt;
					<xsl:value-of
						select="/source/hh-data-import/@uri-id" />
				</title>
			</head>

			<body>

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
						href="{/source/request/@context-path}/orgs/{/source/hh-data-import/dce-service/dce/organization/@id}/">
						<xsl:value-of
							select="/source/hh-data-import/dce-service/dce/organization/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/hh-data-import/dce-service/dce/organization/@id}/dces/">
						DCEs
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/hh-data-import/dce-service/dce/organization/@id}/dces/{/source/hh-data-import/dce-service/dce/@id}">
						<xsl:value-of
							select="/source/hh-data-import/dce-service/dce/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/hh-data-import/dce-service/dce/organization/@id}/dces/{/source/hh-data-import/dce-service/dce/@id}/services/">
						<xsl:value-of select="'Services'"/>
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/hh-data-import/dce-service/dce/organization/@id}/dces/{/source/hh-data-import/dce-service/dce/@id}/services/{/source/hh-data-import/dce-service/@id}/">
					<xsl:value-of
						select="/source/hh-data-import/dce-service/@name" />
						</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/hh-data-import/dce-service/dce/organization/@id}/dces/{/source/hh-data-import/dce-service/dce/@id}/services/{/source/hh-data-import/dce-service/@id}/hh-data-imports/">
						<xsl:value-of select="'HH Data Imports'"/>
					</a>
					&gt;
						<xsl:value-of select="/source/hh-data-import/@uri-id"/>
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
				<p>
					<xsl:choose>
						<xsl:when
							test="/source/hh-data-import/@successful">

							<xsl:choose>
								<xsl:when
									test="/source/hh-data-import/@successful = 'true'">

									The import has completed
									successfully.
								</xsl:when>
								<xsl:otherwise>
									The import didn't complete
									successfully.
								</xsl:otherwise>
							</xsl:choose>
						</xsl:when>
						<xsl:otherwise>
							<xsl:value-of
								select="/source/hh-data-import/@progress" />
						</xsl:otherwise>
					</xsl:choose>
				</p>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>