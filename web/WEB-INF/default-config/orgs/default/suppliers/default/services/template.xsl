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
					Chellow &gt; Organizations &gt;
					<xsl:value-of
						select="/source/supplier-services/supplier/org/@name" />
					&gt; Suppliers &gt;
					<xsl:value-of
						select="/source/supplier-services/supplier/@name" />
					&gt; Services
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
					<a href="{/source/request/@context-path}/orgs/">
						<xsl:value-of select="'Organizations'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/supplier-services/supplier/org/@id}/">
						<xsl:value-of
							select="/source/supplier-services/supplier/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/supplier-services/supplier/org/@id}/suppliers/">
						<xsl:value-of select="'Suppliers'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/supplier-services/supplier/org/@id}/suppliers/{/source/supplier-services/supplier/@id}/">
						<xsl:value-of
							select="/source/supplier-services/supplier/@name" />
					</a>
					&gt;
					<xsl:value-of select="'Services ['" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/supplier-services/supplier/org/@id}/reports/37/screen/output/?supplier-id={/source/supplier-services/supplier/@id}">
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
				<xsl:choose>
					<xsl:when
						test="/source/response/@status-code = '201'">
						<p>
							The
							<a
								href="{/source/response/header[@name = 'Location']/@value}">
								<xsl:value-of select="'new service'" />
							</a>
							has been successfully created.
						</p>
					</xsl:when>
					<xsl:otherwise>
						<ul>
							<xsl:for-each
								select="/source/supplier-services/supplier-service">
								<li>
									<a href="{@id}">
										<xsl:value-of select="@name" />
									</a>
								</li>
							</xsl:for-each>
						</ul>
						<br />
						<hr />
						<form action="." method="post">
							<fieldset>
								<legend>Add a service</legend>
								<p>Type: Contract</p>
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
								<fieldset>
									<legend>Finish Date</legend>
									<label>
										Has finished?
										<input type="checkbox"
											name="has-finished" value="true">
											<xsl:if
												test="/source/request/parameter[@name='has-finished']">
												<xsl:attribute
													name="checked">
													<xsl:value-of
														select="'checked'" />
												</xsl:attribute>
											</xsl:if>
										</input>
									</label>
									<br />
									<input name="finish-date-year"
										maxlength="4" size="4">
										<xsl:attribute name="value">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='finish-date-year']">
													<xsl:value-of
														select="/source/request/parameter[@name='finish-date-year']/value" />
												</xsl:when>
												<xsl:otherwise>
													<xsl:value-of
														select="/source/date/@year" />
												</xsl:otherwise>
											</xsl:choose>
										</xsl:attribute>
									</input>
									<xsl:value-of select="' - '" />
									<select name="finish-date-month">
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
									<select name="finish-date-day">
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
								<label>
									<xsl:value-of
										select="'Charge Script'" />
									<br />
									<textarea name="charge-script"
										cols="80" rows="50">
										<xsl:choose>
											<xsl:when
												test="/source/request/parameter[@name='charge-script']">
												<xsl:value-of
													select="translate(/source/request/parameter[@name='charge-script']/value, '&#xD;&#xA;','')" />
											</xsl:when>
											<xsl:otherwise>
												<xsl:value-of
													select="/source/supplier-service/text()" />
											</xsl:otherwise>
										</xsl:choose>
									</textarea>
								</label>
								<br />

								<br />
								<input type="submit" value="Add" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>