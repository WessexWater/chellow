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
					<xsl:value-of
						select="/source/hh-data/channel/supply-era/supply/@id" />
					&gt; Supply Generations &gt;
					<xsl:value-of select="/source/hh-data/channel/supply-era/@id" />
					&gt; Channels &gt;
					<xsl:value-of select="/source/hh-data/channel/@id" />
					&gt; HH Data
				</title>
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/reports/1/output/">
						<xsl:value-of select="'Chellow'" />
					</a>
					&gt;
					<a href="{/source/request/@context-path}/reports/99/output/">
						<xsl:value-of select="'Supplies'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/reports/7/output/?supply-id={/source/hh-data/channel/supply-era/supply/@id}">
						<xsl:value-of
							select="/source/hh-data/channel/supply-era/supply/@id" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/hh-data/channel/supply-era/supply/@id}/eras/{/source/hh-data/channel/supply-era/@id}/channels/">
						<xsl:value-of select="concat('Generation ', /source/hh-data/channel/supply-era/@id, ' channels')" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/hh-data/channel/supply-era/supply/@id}/eras/{/source/hh-data/channel/supply-era/@id}/channels/{/source/hh-data/channel/@id}/">
						<xsl:value-of select="/source/hh-data/channel/@id" />
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
				<h4>Supply Generation</h4>

				<table>
					<tr>
						<th>Start Date</th>
						<td>
							<xsl:value-of
								select="concat(/source/hh-data/channel/supply-era/hh-start-date[@label='start']/@year, '-', /source/hh-data/channel/supply-era/hh-start-date[@label='start']/@month, '-', /source/hh-data/channel/supply-era/hh-start-date[@label='start']/@day, ' ', /source/hh-data/channel/supply-era/hh-start-date[@label='start']/@hour, ':', /source/hh-data/channel/supply-era/hh-start-date[@label='start']/@minute, ' Z')" />
						</td>
					</tr>
					<tr>
						<th>Finish Date</th>
						<td>
							<xsl:choose>
								<xsl:when
									test="/source/hh-data/channel/supply-era/hh-start-date[@label='finish']">
									<xsl:value-of
										select="concat(/source/hh-data/channel/supply-era/hh-start-date[@label='finish']/@year, '-', /source/hh-data/channel/supply-era/hh-start-date[@label='finish']/@month, '-', /source/hh-data/channel/supply-era/hh-start-date[@label='finish']/@day, ' ', /source/hh-data/channel/supply-era/hh-start-date[@label='finish']/@hour, ':', /source/hh-data/channel/supply-era/hh-start-date[@label='finish']/@minute, ' Z')" />
								</xsl:when>
								<xsl:otherwise>
									Ongoing
								</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
				</table>

				<h4>Channel</h4>
				<ul>
					<li>
						<xsl:choose>
							<xsl:when test="/source/hh-data/channel/@is-import = 'true'">
								Import
							</xsl:when>
							<xsl:otherwise>
								Export
							</xsl:otherwise>
						</xsl:choose>
					</li>
					<li>
						<xsl:choose>
							<xsl:when test="/source/hh-data/channel/@is-kwh = 'true'">
								kWh
							</xsl:when>
							<xsl:otherwise>
								kVArh
							</xsl:otherwise>
						</xsl:choose>
					</li>
				</ul>
				<xsl:choose>
					<xsl:when
						test="/source/request/@method='get' and /source/request/parameter[@name='view']/value='confirm-delete'">
						<form method="post" action=".">
							<input type="hidden" name="delete-from-year"
								value="{/source/request/parameter[@name='delete-from-year']/value}" />
							<input type="hidden" name="delete-from-month"
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
								<input type="submit" name="delete" value="Delete" />
							</fieldset>
						</form>
						<p>
							<a href=".">Cancel</a>
						</p>
					</xsl:when>
					<xsl:otherwise>
						<form action=".">
							<fieldset>
								<legend>Month</legend>
								<input size="4" maxlength="4" name="year">
									<xsl:attribute name="value">
										<xsl:choose>
											<xsl:when test="/source/request/parameter[@name='year']">
												<xsl:value-of
										select="/source/request/parameter[@name='year']/value/text()" />
											</xsl:when>
											<xsl:otherwise>
												<xsl:value-of select="/source/hh-start-date/@year" />
											</xsl:otherwise>
										</xsl:choose>
									</xsl:attribute>
								</input>
								<xsl:value-of select="'-'"/>
								<select name="month">
									<xsl:for-each select="/source/months/month">
										<option value="{@number}">
											<xsl:choose>
												<xsl:when test="/source/request/parameter[@name='month']">
													<xsl:if
														test="/source/request/parameter[@name='month']/value/text() = number(@number)">

														<xsl:attribute name="selected" />
													</xsl:if>
												</xsl:when>
												<xsl:otherwise>
													<xsl:if test="/source/hh-start-date/@month = @number">
														<xsl:attribute name="selected" />
													</xsl:if>
												</xsl:otherwise>
											</xsl:choose>
											<xsl:value-of select="@number" />
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
									<th>Chellow Id</th>
									<th>Time</th>
									<th>
										<xsl:choose>
											<xsl:when test="/source/hh-data/channel/@is-kwh='true'">
												kWh
											</xsl:when>
											<xsl:otherwise>
												kVArh
											</xsl:otherwise>
										</xsl:choose>
										<xsl:choose>
											<xsl:when test="/source/hh-data/channel/@is-import='true'">
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
								<xsl:for-each select="/source/hh-data/hh-datum">
									<tr>
										<td>
											<a
												href="{/source/request/@context-path}/supplies/{/source/hh-data/channel/supply-era/supply/@id}/eras/{/source/hh-data/channel/supply-era/@id}/channels/{/source/hh-data/channel/@id}/hh-data/{@id}/">
												<xsl:value-of select="@id" />
											</a>
										</td>
										<td>
											<xsl:value-of
												select="concat(hh-start-date/@year, '-', hh-start-date/@month, '-', hh-start-date/@day, 'T', hh-start-date/@hour, ':', hh-start-date/@minute)" />
										</td>
										<td>
											<xsl:value-of select="@value" />
										</td>
										<td>
											<xsl:value-of select="@status" />
										</td>
									</tr>
								</xsl:for-each>
							</tbody>
						</table>
						<br />
						<form action=".">
							<fieldset>
								<input type="hidden" name="view" value="confirm-delete" />
								<legend>Delete</legend>
								<fieldset>
									<legend>From</legend>
									<input name="delete-from-year" maxlength="4" size="4">
										<xsl:attribute name="value">
											<xsl:choose>
												<xsl:when
											test="/source/request/parameter[@name='delete-from-year']">
													<xsl:value-of
											select="/source/request/parameter[@name='delete-from-year']/value/text()" />
												</xsl:when>
												<xsl:otherwise>
													<xsl:value-of select="/source/hh-start-date/@year" />
												</xsl:otherwise>
											</xsl:choose>
										</xsl:attribute>
									</input>
									<xsl:value-of select="'-'"/>
									<select name="delete-from-month">
										<xsl:for-each select="/source/months/month">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='delete-from-month']">

														<xsl:if
															test="/source/request/parameter[@name='delete-from-month']/value/text() = number(@number)">

															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if test="/source/hh-start-date/@month = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>

												<xsl:value-of select="@number" />
											</option>
										</xsl:for-each>
									</select>
                                    <xsl:value-of select="'-'"/>
									<select name="delete-from-day">
										<xsl:for-each select="/source/days/day">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='delete-from-day']">

														<xsl:if
															test="/source/request/parameter[@name='delete-from-day']/value/text() = @number">

															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if test="/source/hh-start-date/@day = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>

												<xsl:value-of select="@number" />
											</option>
										</xsl:for-each>
									</select>
									<xsl:value-of select="' 00:00 Z'" />
								</fieldset>
								<br />
								<label>
									<xsl:value-of select="'Number of days '" />
									<input name="days" maxlength="4" size="4">
										<xsl:attribute name="value">
											<xsl:choose>
												<xsl:when test="/source/request/parameter[@name='days']">
													<xsl:value-of select="/source/request/parameter[@name='days']" />
												</xsl:when>
												<xsl:otherwise>
													<xsl:value-of select="'1'" />
												</xsl:otherwise>
											</xsl:choose>
										</xsl:attribute>
									</input>
								</label>
								<br />
								<br />
								<input type="submit" name="delete" value="Delete" />
								<xsl:value-of select="' '" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
						<br />
						<form action="." method="post">
							<fieldset>
								<legend>Insert HH datum</legend>
								<input size="4" maxlength="4" name="end-year">
									<xsl:choose>
										<xsl:when test="/source/request/parameter[@name='end-year']">

											<xsl:attribute name="value">
										<xsl:value-of
												select="/source/request/parameter[@name='end-year']/value/text()" />
									</xsl:attribute>
										</xsl:when>
										<xsl:otherwise>
											<xsl:attribute name="value">
										<xsl:value-of select="/source/hh-start-date/@year" />
									</xsl:attribute>
										</xsl:otherwise>
									</xsl:choose>
								</input>
								<xsl:value-of select="'-'" />
								<select name="end-month">
									<xsl:for-each select="/source/months/month">
										<option value="{@number}">
											<xsl:choose>
												<xsl:when test="/source/request/parameter[@name='end-month']">
													<xsl:if
														test="/source/request/parameter[@name='end-month']/value/text() = number(@number)">
														<xsl:attribute name="selected" />
													</xsl:if>
												</xsl:when>
												<xsl:otherwise>
													<xsl:if test="/source/hh-start-date/@month = @number">
														<xsl:attribute name="selected" />
													</xsl:if>
												</xsl:otherwise>
											</xsl:choose>
											<xsl:value-of select="@number" />
										</option>
									</xsl:for-each>
								</select>
								<xsl:value-of select="'-'" />
								<select name="end-day">
									<xsl:for-each select="/source/days/day">
										<option value="{@number}">
											<xsl:choose>
												<xsl:when test="/source/request/parameter[@name='end-day']">

													<xsl:if
														test="/source/request/parameter[@name='end-day']/value/text() = number(@number)">
														<xsl:attribute name="selected" />
													</xsl:if>
												</xsl:when>
												<xsl:otherwise>
													<xsl:if test="/source/hh-start-date/@day = @number">
														<xsl:attribute name="selected" />
													</xsl:if>
												</xsl:otherwise>
											</xsl:choose>
											<xsl:value-of select="@number" />
										</option>
									</xsl:for-each>
								</select>
								<xsl:value-of select="' '" />
								<select name="end-hour">
									<xsl:for-each select="/source/hours/hour">
										<option value="{@number}">
											<xsl:choose>
												<xsl:when test="/source/request/parameter[@name='end-hour']">

													<xsl:if
														test="/source/request/parameter[@name='end-hour']/value/text() = number(@number)">
														<xsl:attribute name="selected" />
													</xsl:if>
												</xsl:when>
												<xsl:otherwise>
													<xsl:if test="/source/hh-start-date/@hour = @number">
														<xsl:attribute name="selected" />
													</xsl:if>
												</xsl:otherwise>
											</xsl:choose>
											<xsl:value-of select="@number" />
										</option>
									</xsl:for-each>
								</select>
								<xsl:value-of select="':'" />
								<select name="end-minute">
									<option value="00">
										<xsl:choose>
											<xsl:when test="/source/request/parameter[@name='end-minute']">
												<xsl:if
													test="/source/request/parameter[@name='end-minute']/value/text() = '00'">
													<xsl:attribute name="selected" />
												</xsl:if>
											</xsl:when>
											<xsl:otherwise>
												<xsl:if test="/source/hh-start-date/@minute = @number">
													<xsl:attribute name="selected" />
												</xsl:if>
											</xsl:otherwise>
										</xsl:choose>
										<xsl:value-of select="'00'" />
									</option>
									<option value="30">
										<xsl:choose>
											<xsl:when test="/source/request/parameter[@name='end-minute']">
												<xsl:if
													test="/source/request/parameter[@name='end-minute']/value/text() = '30'">
													<xsl:attribute name="selected" />
												</xsl:if>
											</xsl:when>
											<xsl:otherwise>
												<xsl:if test="/source/hh-start-date/@minute = '30'">
													<xsl:attribute name="selected" />
												</xsl:if>
											</xsl:otherwise>
										</xsl:choose>
										<xsl:value-of select="'30'" />
									</option>
								</select>
								<xsl:value-of select="' Z'" />
								<br />
								<br />
								<label>
									<xsl:value-of select="'Value '" />
									<input size="4" maxlength="4" name="value">
										<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when test="/source/request/parameter[@name='value']">
											<xsl:value-of
											select="/source/request/parameter[@name='value']/value/text()" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of select="'0'" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
									</input>
								</label>
								<br />
								<br />
								<label>
									<xsl:value-of select="'Status '" />
									<select name="status">
										<option value="E">
											<xsl:choose>
												<xsl:when test="/source/request/parameter[@name='status']">
													<xsl:if
														test="/source/request/parameter[@name='status']/value/text() = 'E'">
														<xsl:attribute name="selected" />
													</xsl:if>
												</xsl:when>
												<xsl:otherwise>
													<xsl:attribute name="selected" />
												</xsl:otherwise>
											</xsl:choose>
											<xsl:value-of select="'E'" />
										</option>
										<option value="A">
											<xsl:if
												test="/source/request/parameter[@name='status'] and /source/request/parameter[@name='status']/value/text() = 'A'">
												<xsl:attribute name="selected" />
											</xsl:if>
											<xsl:value-of select="'A'" />
										</option>
									</select>
								</label>
								<br />
								<br />
								<xsl:value-of select="' '" />
								<input type="submit" name="insert" value="Insert" />
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