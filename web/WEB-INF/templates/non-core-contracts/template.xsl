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

				<title>Chellow &gt; Non-core Contracts</title>
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img
							src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					<xsl:value-of select="' &gt; Non-core Contracts'" />
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
				<xsl:choose>
					<xsl:when
						test="/source/response/@status-code = '201'">
						<p>
							The
							<a
								href="{/source/response/header[@name = 'Location']/@value}">
								<xsl:value-of select="'new contract'" />
							</a>
							has been successfully created.
						</p>
					</xsl:when>
					<xsl:otherwise>
						<table>
							<thead>
								<tr>
									<th>Chellow Id</th>
									<th>Name</th>
								</tr>
							</thead>
							<tbody>
								<xsl:for-each
									select="/source/non-core-contracts/non-core-contract">
									<tr>
										<td>
											<a
												href="{/source/request/@context-path}/non-core-contracts/{@id}/">
												<xsl:value-of
													select="@id" />
											</a>
										</td>
										<td>
											<xsl:value-of
												select="@name" />
										</td>
									</tr>
								</xsl:for-each>
							</tbody>
						</table>
						<br />
						<form action="." method="post">
							<fieldset>
								<legend>Add a contract</legend>
								<br />
								<label>
									Non-core Provider
									<select name="provider-id">
										<xsl:for-each
											select="/source/provider">
											<option value="{@id}">
												<xsl:if
													test="/source/request/parameter[@name='provider-id']/value = @id">
													<xsl:attribute
														name="selected">
																<xsl:value-of
															select="'selected'" />
															</xsl:attribute>
												</xsl:if>
												<xsl:value-of
													select="concat(participant/@code, ' : ', @name)" />
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
									<input name="start-date-year"
										maxlength="4" size="4">
										<xsl:attribute name="value">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='start-date-year']">
													<xsl:value-of
														select="/source/request/parameter[@name='start-date-year']/value" />
												</xsl:when>
												<xsl:otherwise>
													<xsl:value-of
														select="/source/date/@year" />
												</xsl:otherwise>
											</xsl:choose>
										</xsl:attribute>
									</input>
									<xsl:value-of select="' - '" />
									<select name="start-date-month">
										<xsl:for-each
											select="/source/months/month">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='start-date-month']">
														<xsl:if
															test="/source/request/parameter[@name='start-date-month']/value = @number">
															<xsl:attribute
																name="selected">
																<xsl:value-of
																	select="'selected'" />
															</xsl:attribute>
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if
															test="/source/date/@month = @number">
															<xsl:attribute
																name="selected">
																<xsl:value-of
																	select="'selected'" />
															</xsl:attribute>
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of
													select="@number" />
											</option>
										</xsl:for-each>
									</select>
									<xsl:value-of select="' - '" />
									<select name="start-date-day">
										<xsl:for-each
											select="/source/days/day">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='start-date-day']">
														<xsl:if
															test="/source/request/parameter[@name='start-date-day']/value = @number">
															<xsl:attribute
																name="selected">
																<xsl:value-of
																	select="'selected'" />
															</xsl:attribute>
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if
															test="/source/date/@day = @number">
															<xsl:attribute
																name="selected">
																<xsl:value-of
																	select="'selected'" />
															</xsl:attribute>
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of
													select="@number" />
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
												<p>
							<a href="?view=csv">
								Download all contracts in a CSV XML file.
							</a>
						</p>
						
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>