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
					 href="{/source/request/@context-path}/style/" />

				<title>
					Chellow &gt; Supplies &gt;
					<xsl:value-of
						select="/source/supply-snag/supply/@id" />
					&gt; Snags &gt;
					<xsl:value-of select="/source/supply-snag/@id" />
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
						<img src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					&gt;
					<a href="{/source/request/@context-path}/supplies/">
						<xsl:value-of select="'Supplies'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/supply-snag/supply/@id}/">
						<xsl:value-of
							select="/source/supply-snag/supply/@id" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/supply-snag/supply/@id}/snags/">
						<xsl:value-of select="'Snags'" />
					</a>
					&gt;
					<xsl:value-of select="concat(/source/supply-snag/@id, ' [')" />
					<a
						href="{/source/request/@context-path}/reports/7/output/?supply-id={/source/supply-snag/supply/@id}">
						<xsl:value-of select="'view'" />
					</a>
					<xsl:value-of select="']'" />
				</p>
				<br />
				<table>
					<tr>
						<th>Chellow Id</th>
						<td>
							<xsl:value-of select="/source/supply-snag/@id" />
						</td>
					</tr>
					<tr>
						<th>Start Date</th>
						<td>
							<xsl:value-of
								select="concat(' ', /source/supply-snag/hh-end-date[@label='start']/@year, '-', /source/supply-snag/hh-end-date[@label='start']/@month, '-', /source/supply-snag/hh-end-date[@label='start']/@day)" />
						</td>
					</tr>
					<tr>
						<th>Finish Date</th>
						<td>
							<xsl:choose>
								<xsl:when test="/source/supply-snag/hh-end-date[@label='finish']">
									<xsl:value-of
										select="concat(' ', /source/supply-snag/hh-end-date[@label='finish']/@year, '-', /source/supply-snag/hh-end-date[@label='finish']/@month, '-', /source/supply-snag/hh-end-date[@label='finish']/@day)" />
								</xsl:when>
								<xsl:otherwise>
									Ongoing
								</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
					<tr>
						<th>Date Created</th>
						<td>
							<xsl:value-of
								select="concat(' ', /source/supply-snag/date[@label='created']/@year, '-', /source/supply-snag/date[@label='created']/@month, '-', /source/supply-snag/date[@label='created']/@day)" />
						</td>
					</tr>
					<tr>
						<th>Is Ignored?</th>
						<td>
							<xsl:choose>
								<xsl:when test="/source/supply-snag/@is-ignored = 'true'">
									Yes
								</xsl:when>
								<xsl:otherwise>
									No
								</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
					<tr>
						<th>Description</th>
						<td>
							<xsl:value-of select="/source/supply-snag/@description" />
						</td>
					</tr>
				</table>
				<br />
				<xsl:if
					test="not(/source/supply-snag/date[@label='resolved']) or (/source/supply-snag/date[@label='resolved'] and /source/supply-snag/@is-ignored='true')">
					<form action="." method="post">
						<fieldset>
							<legend>Update snag</legend>
							<input type="hidden" name="ignore">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when test="/source/supply-snag/@is-ignored='true'">
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
										<xsl:when test="/source/supply-snag/@is-ignored='true'">
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
				</xsl:if>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>