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
						select="/source/hh-data/channel/supply-generation/supply/org/@name" />
					&gt; Supplies &gt;
					<xsl:value-of
						select="/source/hh-data/channel/supply-generation/supply/@id" />
					&gt; Supply Generations &gt;
					<xsl:value-of
						select="/source/hh-data/channel/supply-generation/@id" />
					&gt; Channels &gt;
					<xsl:value-of select="/source/hh-data/channel/@id" />
					&gt; HH Data
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
						href="{/source/request/@context-path}/orgs/{/source/hh-data/channel/supply-generation/supply/org/@id}/">
						<xsl:value-of
							select="/source/hh-data/channel/supply-generation/supply/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/hh-data/channel/supply-generation/supply/org/@id}/supplies/">
						<xsl:value-of select="'Supplies'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/hh-data/channel/supply-generation/supply/org/@id}/supplies/{/source/hh-data/channel/supply-generation/supply/@id}/">
						<xsl:value-of
							select="/source/hh-data/channel/supply-generation/supply/@id" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/hh-data/channel/supply-generation/supply/org/@id}/supplies/{/source/hh-data/channel/supply-generation/supply/@id}/generations/">
						<xsl:value-of select="'Generations'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/hh-data/channel/supply-generation/supply/org/@id}/supplies/{/source/hh-data/channel/supply-generation/supply/@id}/generations/{/source/hh-data/channel/supply-generation/@id}/">
						<xsl:value-of
							select="/source/hh-data/channel/supply-generation/@id" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/hh-data/channel/supply-generation/supply/org/@id}/supplies/{/source/hh-data/channel/supply-generation/supply/@id}/generations/{/source/hh-data/channel/supply-generation/@id}/channels/">
						<xsl:value-of select="'Channels'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/hh-data/channel/supply-generation/supply/org/@id}/supplies/{/source/hh-data/channel/supply-generation/supply/@id}/generations/{/source/hh-data/channel/supply-generation/@id}/channels/{/source/hh-data/channel/@id}/">
						<xsl:value-of
							select="/source/hh-data/channel/@id" />
					</a>
					&gt; HH Data
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
				<h4>Channel</h4>
				<ul>
					<li>
						<xsl:choose>
							<xsl:when
								test="/source/hh-data/channel/@is-import = 'true'">
								Import
							</xsl:when>
							<xsl:otherwise>Export</xsl:otherwise>
						</xsl:choose>
					</li>
					<li>
						<xsl:choose>
							<xsl:when
								test="/source/hh-data/channel/@is-kwh = 'true'">
								kWh
							</xsl:when>
							<xsl:otherwise>kVArh</xsl:otherwise>
						</xsl:choose>
					</li>
				</ul>
				<xsl:choose>
					<xsl:when
						test="/source/request/@method='get' and /source/request/parameter[@name='view']/value='confirm-delete'">
						<form method="post" action=".">
							<input type="hidden" name="delete-from-year"
								value="{/source/request/parameter[@name='delete-from-year']/value}" />
							<input type="hidden"
								name="delete-from-month"
								value="{/source/request/parameter[@name='delete-from-month']/value}" />
							<input type="hidden" name="delete-from-day"
								value="{/source/request/parameter[@name='delete-from-day']/value}" />
							<input type="hidden" name="days"
								value="{/source/request/parameter[@name='days']/value}" />

							<fieldset>
								<legend>Confirm Delete</legend>
								<p>
									<xsl:value-of
										select="concat('Are you sure you want to delete the HH data on this channel from ', /source/request/parameter[@name='delete-from-year'], '-', /source/request/parameter[@name='delete-from-month'], '-', /source/request/parameter[@name='delete-from-day'], ' for ', /source/request/parameter[@name='days'], ' days?')" />
								</p>
								<input type="submit" name="delete"
									value="Delete" />
							</fieldset>
						</form>
						<p>
							<a href=".">Cancel</a>
						</p>
					</xsl:when>
					<xsl:otherwise>
						<form action=".">
							<fieldset>
								<legend>End day</legend>
								<input size="4" maxlength="4"
									name="hh-finish-date-year">
									<xsl:choose>
										<xsl:when
											test="/source/request/parameter[@name='hh-finish-date-year']">

											<xsl:attribute
												name="value">
												<xsl:value-of
													select="/source/request/parameter[@name='hh-finish-date-year']/value/text()" />
											</xsl:attribute>
										</xsl:when>

										<xsl:otherwise>
											<xsl:attribute
												name="value">
												<xsl:value-of
													select="/source/date/@year" />
											</xsl:attribute>
										</xsl:otherwise>
									</xsl:choose>
								</input>

								-
								<select name="hh-finish-date-month">
									<xsl:for-each
										select="/source/months/month">
										<option value="{@number}">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='hh-finish-date-month']">

													<xsl:if
														test="/source/request/parameter[@name='hh-finish-date-month']/value/text() = number(@number)">

														<xsl:attribute
															name="selected" />
													</xsl:if>
												</xsl:when>
												<xsl:otherwise>
													<xsl:if
														test="/source/date/@month = @number">
														<xsl:attribute
															name="selected" />
													</xsl:if>
												</xsl:otherwise>
											</xsl:choose>

											<xsl:value-of
												select="@number" />
										</option>
									</xsl:for-each>
								</select>

								-
								<select name="hh-finish-date-day">
									<xsl:for-each
										select="/source/days/day">
										<option value="{@number}">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='hh-finish-date-day']">

													<xsl:if
														test="/source/request/parameter[@name='hh-finish-date-day']/value/text() = @number">

														<xsl:attribute
															name="selected" />
													</xsl:if>
												</xsl:when>
												<xsl:otherwise>
													<xsl:if
														test="/source/date/@day = @number">
														<xsl:attribute
															name="selected" />
													</xsl:if>
												</xsl:otherwise>
											</xsl:choose>

											<xsl:value-of
												select="@number" />
										</option>
									</xsl:for-each>
								</select>
								<xsl:value-of select="' '" />
								<input type="submit" value="Show" />
								<xsl:value-of select="' '" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
						<br />
						<table>
							<caption>HH Data</caption>
							<thead>
								<tr>
									<th>Time</th>
									<th>
										<xsl:choose>
											<xsl:when
												test="/source/hh-data/channel/@is-kwh='true'">
												kWh
											</xsl:when>
											<xsl:otherwise>
												kVArh
											</xsl:otherwise>
										</xsl:choose>
										<xsl:choose>
											<xsl:when
												test="/source/hh-data/channel/@is-import='true'">
												Import
											</xsl:when>
											<xsl:otherwise>
												Export
											</xsl:otherwise>
										</xsl:choose>
									</th>
									<th>Status</th>
								</tr>
							</thead>
							<tbody>
								<xsl:for-each
									select="/source/hh-data/hh-datum">
									<tr>
										<td>
											<xsl:value-of
												select="concat(hh-end-date/@year, '-', hh-end-date/@month, '-', hh-end-date/@day, 'T', hh-end-date/@hour, ':', hh-end-date/@minute, 'Z')" />
										</td>
										<td>
											<xsl:value-of
												select="@value" />
										</td>
										<td>
											<xsl:value-of
												select="@status" />
										</td>
									</tr>
								</xsl:for-each>
							</tbody>
						</table>
						<br />
						<form action=".">
							<fieldset>
								<input type="hidden" name="view"
									value="confirm-delete" />
								<legend>Delete</legend>
								<fieldset>
									<legend>From</legend>
									<input name="delete-from-year"
										maxlength="4" size="4">
										<xsl:choose>
											<xsl:when
												test="/source/request/parameter[@name='delete-from-year']">

												<xsl:attribute
													name="value">
													<xsl:value-of
														select="/source/request/parameter[@name='delete-from-year']/value/text()" />
												</xsl:attribute>
											</xsl:when>
											<xsl:otherwise>
												<xsl:attribute
													name="value">
													<xsl:value-of
														select="/source/date/@year" />
												</xsl:attribute>
											</xsl:otherwise>
										</xsl:choose>
									</input>

									-
									<select name="delete-from-month">
										<xsl:for-each
											select="/source/months/month">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='delete-from-month']">

														<xsl:if
															test="/source/request/parameter[@name='delete-from-month']/value/text() = number(@number)">

															<xsl:attribute
																name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if
															test="/source/date/@month = @number">
															<xsl:attribute
																name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>

												<xsl:value-of
													select="@number" />
											</option>
										</xsl:for-each>
									</select>

									-
									<select name="delete-from-day">
										<xsl:for-each
											select="/source/days/day">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='delete-from-day']">

														<xsl:if
															test="/source/request/parameter[@name='delete-from-day']/value/text() = @number">

															<xsl:attribute
																name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if
															test="/source/date/@day = @number">
															<xsl:attribute
																name="selected" />
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
								<label>
									<xsl:value-of
										select="'Number of days '" />
									<input name="days" maxlength="4"
										size="4">
										<xsl:attribute name="value">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='days']">
													<xsl:value-of
														select="/source/request/parameter[@name='days']" />
												</xsl:when>
												<xsl:otherwise>
													<xsl:value-of
														select="'1'" />
												</xsl:otherwise>
											</xsl:choose>
										</xsl:attribute>
									</input>
								</label>
								<br />
								<br />
								<input type="submit" value="Delete" />
								<xsl:value-of select="' '" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>