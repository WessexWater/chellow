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
					Chellow &gt; SSCs &gt;
					<xsl:value-of select="/source/ssc/@code" />
				</title>
			</head>

			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img
							src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					<xsl:value-of select="' &gt; '" />
					<a href="{/source/request/@context-path}/sscs/">
						<xsl:value-of select="'SSCs'" />
					</a>
					<xsl:value-of
						select="concat(' &gt; ', /source/ssc/@code)" />
				</p>

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
							<xsl:value-of select="/source/ssc/@id" />
						</td>
					</tr>
					<tr>
						<th>Code</th>
						<td>
							<xsl:value-of select="/source/ssc/@code" />
						</td>
					</tr>
					<tr>
						<th>Description</th>
						<td>
							<xsl:value-of
								select="/source/ssc/@description" />
						</td>
					</tr>
					<tr>
						<th>Is Import?</th>
						<td>
							<xsl:choose>
								<xsl:when
									test="/source/ssc/@is-import='true'">
									Import
								</xsl:when>
								<xsl:otherwise>Export</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
					<tr>
						<th>From</th>
						<td>
							<xsl:value-of
								select="concat(/source/ssc/date[@label='from']/@year, '-', /source/ssc/date[@label='from']/@month, '-', /source/ssc/date[@label='from']/@day, ' ', /source/ssc/date[@label='from']/@hour, ':', /source/ssc/date[@label='from']/@minute)" />
						</td>
					</tr>
					<tr>
						<th>To</th>
						<td>
							<xsl:choose>
								<xsl:when
									test="/source/ssc/date[@label='to']">
									<xsl:value-of
										select="concat(/source/ssc/date[@label='to']/@year, '-', /source/ssc/date[@label='to']/@month, '-', /source/ssc/date[@label='to']/@day, ' ', /source/ssc/date[@label='to']/@hour, ':', /source/ssc/date[@label='to']/@minute)" />
								</xsl:when>
								<xsl:otherwise>Ongoing</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
				</table>

				<h4>TPRs</h4>

				<ul>
					<xsl:for-each select="/source/ssc/measurement-requirement/tpr">
						<li>
							<a
								href="{/source/request/@context-path}/tprs/{@id}/">
								<xsl:value-of select="@code" />
							</a>
							<xsl:if test="position() != last()">
								<xsl:value-of select="', '" />
							</xsl:if>
						</li>
					</xsl:for-each>
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

