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
					Chellow &gt; DSOs &gt;
					<xsl:value-of
						select="concat(/source/dso-contracts/dso/@code, ' &gt; Contracts')" />
				</title>
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					<xsl:value-of select="' &gt; '" />
					<a href="{/source/request/@context-path}/dsos/">
						<xsl:value-of select="'DSOs'" />
					</a>
					<xsl:value-of select="' &gt; '" />
					<a
						href="{/source/request/@context-path}/dsos/{/source/dso-contracts/dso/@id}/">
						<xsl:value-of select="/source/dso-contracts/dso/@code" />
					</a>
					<xsl:value-of select="' &gt; Contracts '" />
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
					<thead>
						<tr>
							<th>Chellow Id</th>
							<th>Name</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each select="/source/dso-contracts/dso-contract">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/dsos/{/source/dso-contracts/dso/@id}/contracts/{@id}/">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<xsl:value-of select="@name" />
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
				<br />
				<br />
				<form action="." method="post">
					<fieldset>
						<legend>Add a contract</legend>
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
							<input name="start-year" maxlength="4" size="4">
								<xsl:attribute name="value">
											<xsl:choose>
												<xsl:when test="/source/request/parameter[@name='start-year']">
													<xsl:value-of
									select="/source/request/parameter[@name='start-year']/value" />
												</xsl:when>
												<xsl:otherwise>
													<xsl:value-of select="/source/date/@year" />
												</xsl:otherwise>
											</xsl:choose>
										</xsl:attribute>
							</input>
							<xsl:value-of select="' - '" />
							<select name="start-month">
								<xsl:for-each select="/source/months/month">
									<option value="{@number}">
										<xsl:choose>
											<xsl:when test="/source/request/parameter[@name='start-month']">
												<xsl:if
													test="/source/request/parameter[@name='start-month']/value = @number">
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
							<select name="start-day">
								<xsl:for-each select="/source/days/day">
									<option value="{@number}">
										<xsl:choose>
											<xsl:when test="/source/request/parameter[@name='start-day']">
												<xsl:if
													test="/source/request/parameter[@name='start-day']/value = @number">
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