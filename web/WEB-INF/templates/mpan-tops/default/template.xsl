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
					Chellow &gt; MPAN Top Lines &gt;
					<xsl:value-of select="/source/mpan-top/@id" />
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
						href="{/source/request/@context-path}/mpan-tops/">
						<xsl:value-of select="'MPAN tops'" />
					</a>
					&gt;
					<xsl:value-of select="/source/mpan-top/@id" />
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
				<br />
				<table>
					<tbody>
						<tr>
							<th>GSP Group</th>
							<td>
								<a
									href="{/source/request/@context-path}/gsp-groups/{/source/mpan-top/gsp-group/@id}/">
									<xsl:value-of
										select="concat(/source/mpan-top/gsp-group/@code, ' - ', /source/mpan-top/gsp-group/@description)" />
								</a>
							</td>
						</tr>
						<tr>
							<th>DSO</th>
							<td>
								<a
									href="{/source/request/@context-path}/dsos/{/source/mpan-top/llfc/dso/@id}/">
									<xsl:value-of
										select="concat(/source/mpan-top/llfc/dso/@code, ' - ', /source/mpan-top/llfc/dso/@name)" />
								</a>
							</td>
						</tr>
						<tr>
							<th>Profile Class</th>
							<td>
								<a
									href="{/source/request/@context-path}/pcs/{/source/mpan-top/pc/@id}/">
									<xsl:value-of
										select="concat(/source/mpan-top/pc/@code, ' - ', /source/mpan-top/pc/@description)" />
								</a>
							</td>
						</tr>
						<tr>
							<th>Meter Timeswitch Class</th>
							<td>
								<a
									href="{/source/request/@context-path}/mtcs/{/source/mpan-top/mtc/@id}/">
									<xsl:value-of
										select="concat(/source/mpan-top/mtc/@code, ' - ', /source/mpan-top/mtc/@description)" />
								</a>
							</td>
						</tr>
						<tr>
							<th>Line Loss Factor Class</th>
							<td>
								<a
									href="{/source/request/@context-path}/dsos/{/source/mpan-top/llfc/dso/@id}/llfcs/{/source/mpan-top/llfc/@id}/">
									<xsl:value-of
										select="concat(/source/mpan-top/llfc/@code, ' - ', /source/mpan-top/llfc/@description)" />
								</a>
							</td>
						</tr>
						<tr>
							<th>Standard Settlement Configuration</th>
							<td>
								<a
									href="{/source/request/@context-path}/sscs/{/source/mpan-top/ssc/@id}/">
									<xsl:value-of
										select="concat(/source/mpan-top/ssc/@code, ' - ', /source/mpan-top/ssc/@description)" />
								</a>
							</td>
						</tr>
						<tr>
							<th>Valid From</th>
							<td>
								<xsl:value-of
									select="concat(/source/mpan-top/date[@label='from']/@year, '-', /source/mpan-top/date[@label='from']/@month, '-', /source/mpan-top/date[@label='from']/@day, ' ', /source/mpan-top/date[@label='from']/@hour, ':', /source/mpan-top/date[@label='from']/@minute, ' Z')" />
							</td>
						</tr>
						<tr>
							<th>Valid To</th>
							<td>
								<xsl:choose>
									<xsl:when
										test="date[@label='to']">
										<xsl:value-of
											select="concat(/source/mpan-top/date[@label='to']/@year, '-', /source/mpan-top/date[@label='to']/@month, '-', /source/mpan-top/date[@label='to']/@day, ' ', /source/mpan-top/date[@label='to']/@hour, ':', /source/mpan-top/date[@label='to']/@minute, ' Z')" />
									</xsl:when>
									<xsl:otherwise>
										Ongoing
									</xsl:otherwise>
								</xsl:choose>
							</td>
						</tr>
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>