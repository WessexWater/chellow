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
					Chellow &gt; Supplies &gt;
					<xsl:value-of select="/source/supply-generations/supply/@id" />
					&gt; Generations
				</title>
			</head>
			<body>
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
						href="{/source/request/@context-path}/supplies/{/source/supply-generations/supply/@id}/">
						<xsl:value-of select="/source/supply-generations/supply/@id" />
					</a>
					&gt;
					<xsl:value-of select="'Generations ['" />
					<a
						href="{/source/request/@context-path}/reports/7/output/?supply-id={/source/supply-generations/supply/@id}">
						<xsl:value-of select="'view'" />
					</a>
					<xsl:value-of select="']'" />
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
				<table>
					<caption>Generations</caption>
					<thead>
						<tr>
							<th rowspan="2">Chellow Id</th>
							<th rowspan="2">Start date</th>
							<th rowspan="2">End date</th>
							<th colspan="2">Mpan Core</th>
						</tr>
						<tr>
							<th>Import</th>
							<th>Export</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each select="/source/supply-generations/supply-generation">
							<tr>
								<td>
									<a href="{@id}/">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<xsl:value-of
										select="concat(hh-start-date[@label='start']/@year, '-', hh-start-date[@label='start']/@month, '-', hh-start-date[@label='start']/@day, ' ', hh-start-date[@label='start']/@hour, ':', hh-start-date[@label='start']/@minute)" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when test="hh-start-date[@label='finish']">
											<xsl:value-of
												select="concat(hh-start-date[@label='finish']/@year, '-', hh-start-date[@label='finish']/@month, '-', hh-start-date[@label='finish']/@day, ' ', hh-start-date[@label='finish']/@hour, ':', hh-start-date[@label='finish']/@minute)" />
										</xsl:when>
										<xsl:otherwise>
											Ongoing
										</xsl:otherwise>
									</xsl:choose>
								</td>
								<td>
									<xsl:value-of select="mpan[llfc/@is-import='true']/mpan-core/@core" />
								</td>
								<td>
									<xsl:value-of select="mpan[llfc/@is-import='false']/mpan-core/@core" />
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
				<br />
				<form method="post" action=".">
					<fieldset>
						<legend>
							Add new supply generation
								</legend>
						<br />
						<label>
							<xsl:value-of select="'Start date '" />
						</label>
						<input name="start-year" size="4">
							<xsl:choose>
								<xsl:when test="/source/request/parameter[@name='start-year']">
									<xsl:attribute name="value">
												<xsl:value-of
										select="/source/request/parameter[@name='start-year']/value/text()" />
											</xsl:attribute>
								</xsl:when>
								<xsl:otherwise>
									<xsl:attribute name="value">
												<xsl:value-of select="/source/date/@year" />
											</xsl:attribute>
								</xsl:otherwise>
							</xsl:choose>
						</input>
						-
						<select name="start-month">
							<xsl:for-each select="/source/months/month">
								<option value="{@number}">
									<xsl:choose>
										<xsl:when
											test="/source/request/parameter[@name='start-month']">
											<xsl:if
												test="/source/request/parameter[@name='start-month']/value/text() = @number">
												<xsl:attribute name="selected" />
											</xsl:if>
										</xsl:when>
										<xsl:otherwise>
											<xsl:if test="/source/date/@month = @number">
												<xsl:attribute name="selected" />
											</xsl:if>
										</xsl:otherwise>
									</xsl:choose>
									<xsl:value-of select="@number" />
								</option>
							</xsl:for-each>
						</select>
						-
						<select name="start-day">
							<xsl:for-each select="/source/days/day">
								<option value="{@number}">
									<xsl:choose>
										<xsl:when test="/source/request/parameter[@name='start-day']">
											<xsl:if
												test="/source/request/parameter[@name='start-day']/value/text() = @number">
												<xsl:attribute name="selected" />
											</xsl:if>
										</xsl:when>
										<xsl:otherwise>
											<xsl:if test="/source/date/@day = @number">
												<xsl:attribute name="selected" />
											</xsl:if>
										</xsl:otherwise>
									</xsl:choose>
									<xsl:value-of select="@number" />
								</option>
							</xsl:for-each>
						</select>
						<xsl:value-of select="' 00:00 Z'" />
						<br />
						<br />
						<input type="submit" value="Add" />
						<input type="reset" value="Reset" />
					</fieldset>
				</form>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>