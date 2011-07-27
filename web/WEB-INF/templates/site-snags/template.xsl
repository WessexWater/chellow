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
					Chellow &gt; Site Snags &gt; Edit
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
					<a href="{/source/request/@context-path}/reports/1/output/">
						<xsl:value-of select="'Chellow'" />
					</a>
					&gt;
					<a href="{/source/request/@context-path}/reports/39/output/">
						<xsl:value-of select="'Site Snags'" />
					</a>
					&gt; Edit
				</p>
				<br />
				<form method="post" action=".">
					<fieldset>
						<legend>Bulk ignore</legend>
						<p>Ignore all snags before</p>
						<input name="ignore-year" size="4" maxlength="4">
							<xsl:choose>
								<xsl:when test="/source/request/parameter[@name='ignore-year']">
									<xsl:attribute name="value">
										<xsl:value-of
										select="/source/request/parameter[@name='ignore-year']/value/text()" />
									</xsl:attribute>
								</xsl:when>
								<xsl:otherwise>
									<xsl:attribute name="value">
										<xsl:value-of select="/source/date/@year" />
									</xsl:attribute>
								</xsl:otherwise>
							</xsl:choose>
						</input>
						<xsl:value-of select="'-'" />
						<select name="ignore-month">
							<xsl:for-each select="/source/months/month">
								<option value="{@number}">
									<xsl:choose>
										<xsl:when test="/source/request/parameter[@name='ignore-month']">

											<xsl:if
												test="/source/request/parameter[@name='ignore-month']/value/text() = number(@number)">

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
						<xsl:value-of select="'-'" />
						<select name="ignore-day">
							<xsl:for-each select="/source/days/day">
								<option value="{@number}">
									<xsl:choose>
										<xsl:when test="/source/request/parameter[@name='ignore-day']">
											<xsl:if
												test="/source/request/parameter[@name='ignore-day']/value/text() = @number">
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
						<xsl:value-of select="' '" />
						<input type="submit" name="ignore" value="Ignore" />
						<input type="reset" value="Reset" />
					</fieldset>
				</form>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>