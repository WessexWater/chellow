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
				<title>Chellow &gt; SSCs</title>
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
					<xsl:value-of select="' &gt; SSCs'" />
				</p>

				<table>
					<thead>
						<tr>
							<th>Chellow Id</th>
							<th>Code</th>
							<th>Description</th>
							<th>Is Import?</th>
							<th>From</th>
							<th>To</th>
							<th>Tprs</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each select="/source/sscs/ssc">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/sscs/{@id}/">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<xsl:value-of select="@code" />
								</td>
								<td>
									<xsl:value-of select="@description" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when
											test="@is-import='true'">
											Import
										</xsl:when>
										<xsl:otherwise>
											Export
										</xsl:otherwise>
									</xsl:choose>
								</td>
								<td>
									<xsl:value-of
										select="concat(date[@label='from']/@year, '-', date[@label='from']/@month, '-', date[@label='from']/@day, ' ', date[@label='from']/@hour, ':', date[@label='from']/@minute)" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when
											test="date[@label='to']">
											<xsl:value-of
												select="concat(date[@label='to']/@year, '-', date[@label='to']/@month, '-', date[@label='to']/@day, ' ', date[@label='to']/@hour, ':', date[@label='to']/@minute)" />
										</xsl:when>
										<xsl:otherwise>
											Ongoing
										</xsl:otherwise>
									</xsl:choose>
								</td>
								<td>
									<xsl:for-each
										select="measurement-requirement">
										<a href="{/source/request/@context-path}/tprs/{tpr/@id}/">
										<xsl:value-of
											select="tpr/@code" /></a>
										<xsl:if
											test="position() != last()">
											<xsl:value-of select="', '" />
										</xsl:if>
									</xsl:for-each>
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

