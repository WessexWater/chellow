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
					href="{/source/request/@context-path}/reports/19/output/" />

				<title>
					Chellow &gt; HHDC Contracts &gt;
					<xsl:value-of
						select="/source/hh-data-import/hhdc-contract/@name" />
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
					<a
						href="{/source/request/@context-path}/hhdc-contracts/">
						<xsl:value-of select="'HHDC Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/hhdc-contracts/{/source/hh-data-import/hhdc-contract/@id}/">
						<xsl:value-of
							select="/source/hh-data-import/hhdc-contract/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/hhdc-contracts/{/source/hh-data-import/hhdc-contract/@id}/hh-data-imports/">
						<xsl:value-of select="'HH Data Imports'" />
					</a>
					&gt;
					<xsl:value-of
						select="/source/hh-data-import/@uri-id" />
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