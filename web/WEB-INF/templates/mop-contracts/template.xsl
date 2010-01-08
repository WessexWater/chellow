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
				<title>Chellow &gt; MOp Contracts</title>
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					&gt;
					<xsl:value-of select="'MOp Contracts ['" />
					<a href="{/source/request/@context-path}/reports/113/output/">
						<xsl:value-of select="'view'" />
					</a>
					<xsl:value-of select="']'" />
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
				<ul>
					<xsl:for-each select="/source/mop-contracts/mop-contract">
						<li>
							<a href="{@id}/">
								<xsl:value-of select="@name" />
							</a>
						</li>
					</xsl:for-each>
				</ul>
				<br />
				<form action="." method="post">
					<fieldset>
						<legend>Add a contract</legend>
						<br />
						<label>
	MOp
							<select name="participant-id">
								<xsl:for-each select="/source/provider">
									<option value="{participant/@id}">
										<xsl:if
											test="/source/request/parameter[@name='participant-id']/value = @id">
											<xsl:attribute name="selected">
																<xsl:value-of select="'selected'" />
															</xsl:attribute>
										</xsl:if>
										<xsl:value-of
											select="concat(participant/@code, ' : ', participant/@name, ' : ', @name)" />
									</option>
								</xsl:for-each>
							</select>
						</label>
						<br />
						<br />
						<label>
							<xsl:value-of select="'Name '" />
							<input name="name"
								value="{/source/request/parameter[@name = 'name']/value}" />
						</label>
						<br />
						<br />
						<fieldset>
							<legend>Start Date</legend>
							<input name="start-date-year" maxlength="4" size="4">
								<xsl:attribute name="value">
											<xsl:choose>
												<xsl:when
									test="/source/request/parameter[@name='start-date-year']">
													<xsl:value-of
									select="/source/request/parameter[@name='start-date-year']/value" />
												</xsl:when>
												<xsl:otherwise>
													<xsl:value-of select="/source/date/@year" />
												</xsl:otherwise>
											</xsl:choose>
										</xsl:attribute>
							</input>
							<xsl:value-of select="' - '" />
							<select name="start-date-month">
								<xsl:for-each select="/source/months/month">
									<option value="{@number}">
										<xsl:choose>
											<xsl:when
												test="/source/request/parameter[@name='start-date-month']">
												<xsl:if
													test="/source/request/parameter[@name='start-date-month']/value = @number">
													<xsl:attribute name="selected">
																<xsl:value-of select="'selected'" />
															</xsl:attribute>
												</xsl:if>
											</xsl:when>
											<xsl:otherwise>
												<xsl:if test="/source/date/@month = @number">
													<xsl:attribute name="selected">
																<xsl:value-of select="'selected'" />
															</xsl:attribute>
												</xsl:if>
											</xsl:otherwise>
										</xsl:choose>
										<xsl:value-of select="@number" />
									</option>
								</xsl:for-each>
							</select>
							<xsl:value-of select="' - '" />
							<select name="start-date-day">
								<xsl:for-each select="/source/days/day">
									<option value="{@number}">
										<xsl:choose>
											<xsl:when test="/source/request/parameter[@name='start-date-day']">
												<xsl:if
													test="/source/request/parameter[@name='start-date-day']/value = @number">
													<xsl:attribute name="selected">
																<xsl:value-of select="'selected'" />
															</xsl:attribute>
												</xsl:if>
											</xsl:when>
											<xsl:otherwise>
												<xsl:if test="/source/date/@day = @number">
													<xsl:attribute name="selected">
																<xsl:value-of select="'selected'" />
															</xsl:attribute>
												</xsl:if>
											</xsl:otherwise>
										</xsl:choose>
										<xsl:value-of select="@number" />
									</option>
								</xsl:for-each>
							</select>
							<xsl:value-of select="' 00:30 Z'" />
						</fieldset>
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