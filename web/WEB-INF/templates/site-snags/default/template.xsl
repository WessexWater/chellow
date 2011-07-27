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
					href="{/source/request/@context-path}/reports/19/output/" />

				<title>
					Chellow &gt; Site Snags &gt;
					<xsl:value-of select="/source/site-snag/@id" />
				</title>
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/reports/1/output/">
						<xsl:value-of select="'Chellow'" />
					</a>
					&gt;
					<a href="{/source/request/@context-path}/reports/39/output/">
						<xsl:value-of select="'Site Snags'" />
					</a>
					&gt;
					<xsl:value-of select="concat('Snag ', /source/site-snag/@id)" />
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
					<tr>
						<th>Date Created</th>
						<td>
							<xsl:value-of
								select="concat(/source/site-snag/date[@label='created']/@year, '-', /source/site-snag/date[@label='created']/@month, '-', /source/site-snag/date[@label='created']/@day, ' ', /source/site-snag/date[@label='created']/@hour, ':', /source/site-snag/date[@label='created']/@minute)" />
						</td>
					</tr>
					<tr>
						<th>Ignored?</th>
						<td>
							<xsl:value-of select="/source/site-snag/@is-ignored" />
						</td>
					</tr>
					<tr>
						<th>Description</th>
						<td>
							<xsl:value-of select="/source/site-snag/@description" />
						</td>
					</tr>
					<tr>
						<th>Site Code</th>
						<td>
							<xsl:value-of select="/source/site-snag/site/@code" />
						</td>
					</tr>
					<tr>
						<th>Site Name</th>
						<td>
							<xsl:value-of select="/source/site-snag/site/@name" />
						</td>
					</tr>
					<tr>
						<th>Start Date</th>
						<td>
							<xsl:value-of
								select="concat(/source/site-snag/hh-start-date[@label='start']/@year, '-', /source/site-snag/hh-start-date[@label='start']/@month, '-', /source/site-snag/hh-start-date[@label='start']/@day, ' ', /source/site-snag/hh-start-date[@label='start']/@hour, ':', /source/site-snag/hh-start-date[@label='start']/@minute)" />
						</td>
					</tr>
					<tr>
						<th>Finish Date</th>
						<td>
							<xsl:value-of
								select="concat(/source/site-snag/hh-start-date[@label='finish']/@year, '-', /source/site-snag/hh-start-date[@label='finish']/@month, '-', /source/site-snag/hh-start-date[@label='finish']/@day, ' ', /source/site-snag/hh-start-date[@label='finish']/@hour, ':', /source/site-snag/hh-start-date[@label='finish']/@minute)" />
						</td>
					</tr>
				</table>
				<br />
				<form action="." method="post">
					<fieldset>
						<legend>Update snag</legend>
						<input type="hidden" name="ignore">
							<xsl:attribute name="value">
							<xsl:choose>
								<xsl:when test="/source/site-snag/@is-ignored='true'">
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
										<xsl:when test="/source/site-snag/@is-ignored='true'">
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
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>