<?xml version="1.0" encoding="iso-8859-1"?>
<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="html" encoding="US-ASCII"
		doctype-public="-//W3C//DTD HTML 4.01//EN" doctype-system="http://www.w3.org/TR/html4/strict.dtd"
		indent="yes" />
	<xsl:template match="/">
		<html>
			<head>
				<title>
					Chellow &gt; Supplies &gt;
					<xsl:value-of select="/source/supply-generation/supply/@id" />
					&gt; Generation
					<xsl:value-of select="/source/supply-generation/@id" />
				</title>
				<link rel="stylesheet" type="text/css"
					href="{/source/request/@context-path}/reports/19/output/" />
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
						href="{/source/request/@context-path}/reports/7/output/?supply-id={/source/supply-generation/supply/@id}">
						<xsl:value-of select="/source/supply-generation/supply/@id" />
					</a>
					&gt;
					<xsl:value-of
						select="concat('Generation ', /source/supply-generation/@id)" />
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
						test="/source/request/@method='get' and /source/request/parameter[@name='view']/value='confirm-delete'">
						<form method="post" action=".">
							<fieldset>
								<legend>
									Are you sure you want to delete this
									supply generation?
								</legend>
								<input type="submit" name="delete" value="Delete" />
							</fieldset>
						</form>
						<p>
							<a href=".">Cancel</a>
						</p>
					</xsl:when>
					<xsl:otherwise>
						<table>
							<caption>Sites</caption>
							<thead>
								<tr>
									<th>Code</th>
									<th>Name</th>
									<xsl:if
										test="count(/source/supply-generation/site-supply-generation) > 1">
										<th></th>
										<th></th>
										<th></th>
									</xsl:if>
								</tr>
							</thead>
							<tbody>
								<xsl:for-each select="/source/supply-generation/site-supply-generation">
									<tr>
										<td>
											<xsl:value-of select="site/@code" />
										</td>
										<td>
											<xsl:value-of select="site/@name" />
										</td>
										<xsl:if
											test="count(/source/supply-generation/site-supply-generation) > 1">
											<td>
												<xsl:if test="@is-physical = 'true'">
													Located here
												</xsl:if>
											</td>
											<td>
												<xsl:if test="@is-physical = 'false'">
													<form method="post" action=".">
														<fieldset>
															<legend>
																Set
																location
															</legend>
															<input type="hidden" name="site-id" value="{site/@id}" />
															<input type="submit" name="set-location" value="Set Location" />
														</fieldset>
													</form>
												</xsl:if>
											</td>
											<td>
												<form method="post" action=".">
													<fieldset>
														<legend>
															Detach from
															site
														</legend>
														<input type="hidden" name="site-id" value="{site/@id}" />
														<input type="submit" name="detach" value="Detach" />
													</fieldset>
												</form>
											</td>
										</xsl:if>
									</tr>
								</xsl:for-each>
							</tbody>
						</table>
						<br />
						<form method="post" action=".">
							<fieldset>
								<legend>Attach to another site</legend>
								<label>
									<xsl:value-of select="'Site Code '" />
									<input name="site-code"
										value="{/source/request/parameter[@name='site-code']/value}" />
								</label>
								<xsl:value-of select="' '" />
								<input type="submit" name="attach" value="Attach" />
								<input type="reset" />
							</fieldset>
						</form>
						<br />
						<form action="." method="post">
							<fieldset>
								<legend>
									Update this supply generation
								</legend>
								<fieldset>
									<legend>Start date</legend>
									<input name="start-year" size="4" maxlength="4">
										<xsl:choose>
											<xsl:when test="/source/request/parameter[@name='start-year']">
												<xsl:attribute name="value">
													<xsl:value-of
													select="/source/request/parameter[@name='start-year']/value/text()" />
												</xsl:attribute>
											</xsl:when>
											<xsl:otherwise>
												<xsl:attribute name="value">
													<xsl:value-of
													select="/source/supply-generation/hh-start-date[@label='start']/@year" />
												</xsl:attribute>
											</xsl:otherwise>
										</xsl:choose>
									</input>
									<xsl:value-of select="'-'" />
									<select name="start-month">
										<xsl:for-each select="/source/months/month">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when test="/source/request/parameter[@name='start-month']">
														<xsl:if
															test="/source/request/parameter[@name='start-month']/value/text() = number(@number)">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if
															test="/source/supply-generation/hh-start-date[@label='start']/@month = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of select="@number" />
											</option>
										</xsl:for-each>
									</select>
									<xsl:value-of select="'-'" />
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
														<xsl:if
															test="/source/supply-generation/hh-start-date[@label='start']/@day = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of select="@number" />
											</option>
										</xsl:for-each>
									</select>
									<xsl:value-of select="' '" />
									<select name="start-hour">
										<xsl:for-each select="/source/hours/hour">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when test="/source/request/parameter[@name='start-hour']">
														<xsl:if
															test="/source/request/parameter[@name='start-hour']/value/text() = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if
															test="/source/supply-generation/hh-start-date[@label='start']/@hour = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of select="@number" />
											</option>
										</xsl:for-each>
									</select>
									<xsl:value-of select="':'" />
									<select name="start-minute">
										<xsl:for-each select="/source/hh-minutes/minute">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when test="/source/request/parameter[@name='start-minute']">
														<xsl:if
															test="/source/request/parameter[@name='start-minute']/value/text() = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if
															test="/source/supply-generation/hh-start-date[@label='start']/@minute = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of select="@number" />
											</option>
										</xsl:for-each>
									</select>
								</fieldset>
								<br />
								<fieldset>
									<legend>End Date</legend>
									<label>
										Ended?
										<input type="checkbox" name="is-ended" value="true">
											<xsl:choose>
												<xsl:when test="/source/request/@method='post'">
													<xsl:if test="/source/request/parameter[@name='is-ended']">
														<xsl:attribute name="checked">
															checked
														</xsl:attribute>
													</xsl:if>
												</xsl:when>
												<xsl:otherwise>
													<xsl:if
														test="/source/supply-generation/hh-start-date[@label='finish']">
														<xsl:attribute name="checked">
															checked
														</xsl:attribute>
													</xsl:if>
												</xsl:otherwise>
											</xsl:choose>
										</input>
									</label>
									<xsl:value-of select="' '" />
									<input name="finish-year" size="4" maxlength="4">
										<xsl:attribute name="value">
											<xsl:choose>
												<xsl:when test="/source/request/parameter[@name='finish-year']">
													<xsl:value-of
											select="/source/request/parameter[@name='finish-year']/value/text()" />
												</xsl:when>
												<xsl:when
											test="/source/supply-generation/hh-start-date[@label='finish']">
													<xsl:value-of
											select="/source/supply-generation/hh-start-date[@label='finish']/@year" />
												</xsl:when>
												<xsl:otherwise>
													<xsl:value-of select="/source/date/@year" />
												</xsl:otherwise>
											</xsl:choose>
										</xsl:attribute>
									</input>
									<xsl:value-of select="'-'" />
									<select name="finish-month">
										<xsl:for-each select="/source/months/month">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when test="/source/request/parameter[@name='finish-month']">

														<xsl:if
															test="/source/request/parameter[@name='finish-month']/value/text() = number(@number)">

															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:when
														test="/source/supply-generation/hh-start-date[@label='finish']">
														<xsl:if
															test="/source/supply-generation/hh-start-date[@label='finish']/@month = @number">
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
									<select name="finish-day">
										<xsl:for-each select="/source/days/day">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when test="/source/request/parameter[@name='finish-day']">
														<xsl:if
															test="/source/request/parameter[@name='finish-day']/value/text() = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:when
														test="/source/supply-generation/hh-start-date[@label='finish']">
														<xsl:if
															test="/source/supply-generation/hh-start-date[@label='finish']/@day = @number">
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
									<select name="finish-hour">
										<xsl:for-each select="/source/hours/hour">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when test="/source/request/parameter[@name='finish-hour']">
														<xsl:if
															test="/source/request/parameter[@name='finish-hour']/value/text() = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:when
														test="/source/supply-generation/hh-start-date[@label='finish']">
														<xsl:if
															test="/source/supply-generation/hh-start-date[@label='finish']/@hour = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if test="/source/date/@hour = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of select="@number" />
											</option>
										</xsl:for-each>
									</select>
									<xsl:value-of select="':'" />
									<select name="finish-minute">
										<xsl:for-each select="/source/hh-minutes/minute">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='finish-minute']">
														<xsl:if
															test="/source/request/parameter[@name='finish-minute']/value/text() = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:when
														test="/source/supply-generation/hh-start-date[@label='finish']">
														<xsl:if
															test="/source/supply-generation/hh-start-date[@label='finish']/@minute = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if test="/source/date/@minute = @number">
															<xsl:attribute name="selected" />
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
								<label>
									<xsl:value-of select="'MOP Contract '" />
									<select name="mop-contract-id">
										<xsl:for-each select="/source/mop-contract">
											<option value="{@id}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='mop-contract-id']">
														<xsl:if
															test="@id = /source/request/parameter[@name='mop-contract-id']/value">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if test="@id = /source/supply-generation/mop-contract/@id">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of select="@name" />
											</option>
										</xsl:for-each>
									</select>
								</label>
								<br />
								<label>
									MOP Account
									<input name="mop-account">
										<xsl:attribute name="value">
												<xsl:choose>
													<xsl:when test="/source/request/parameter[@name='mop-account']">
														<xsl:value-of
											select="/source/request/parameter[@name='mop-account']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of select="/source/supply-generation/@mop-account" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
									</input>
								</label>
								<xsl:value-of select="' '" />
								<br />

								<label>
									<xsl:value-of select="'HHDC Contract '" />
									<select name="hhdc-contract-id">
										<xsl:for-each select="/source/hhdc-contract">
											<option value="{@id}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='hhdc-contract-id']">
														<xsl:if
															test="@id = /source/request/parameter[@name='hhdc-contract-id']/value">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if
															test="@id = /source/supply-generation/hhdc-contract/@id">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of select="@name" />
											</option>
										</xsl:for-each>
									</select>
								</label>
								<xsl:if test="/source/supply-generation/hhdc-contract">
									<xsl:value-of select="' '" />
									<xsl:value-of select="/source/supply-generation/hhdc-contract/@name" />
								</xsl:if>
								<br />
								<label>
									HHDC Account
									<input name="hhdc-account">
										<xsl:attribute name="value">
												<xsl:choose>
													<xsl:when
											test="/source/request/parameter[@name='hhdc-account']">
														<xsl:value-of
											select="/source/request/parameter[@name='hhdc-account']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of select="/source/supply-generation/@hhdc-account" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
									</input>
								</label>
								<xsl:value-of select="' '" />
								<br />
								<label>
									<xsl:value-of select="'Meter Serial Number '" />
									<input name="meter-serial-number">
										<xsl:attribute name="value">
											<xsl:choose>
												<xsl:when
											test="/source/request/parameter[@name='meter-serial-number']">
													<xsl:value-of
											select="/source/request/parameter[@name='meter-serial-number']/value" />
												</xsl:when>
												<xsl:otherwise>
													<xsl:value-of
											select="/source/supply-generation/@meter-serial-number" />
												</xsl:otherwise>
											</xsl:choose>
										</xsl:attribute>
									</input>
								</label>
								<br />
								<label>
									<xsl:value-of select="'Profile Class '" />
									<select name="pc-id">
										<xsl:for-each select="/source/pc">
											<option value="{@id}">
												<xsl:choose>
													<xsl:when test="/source/request/parameter[@name='pc-id']">
														<xsl:if
															test="@id = /source/request/parameter[@name='pc-id']/value">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if test="@id = /source/supply-generation/pc/@id">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of select="concat(@code, ' - ', @description)" />
											</option>
										</xsl:for-each>
									</select>
								</label>
								<br />
								<label>
									<xsl:value-of select="'Meter Timeswitch Class '" />
									<input name="mtc-code" size="3" maxlength="3">
										<xsl:attribute name="value">
												<xsl:choose>
													<xsl:when test="/source/request/parameter[@name='mtc-code']">
														<xsl:value-of
											select="/source/request/parameter[@name='mtc-code']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of select="/source/supply-generation/mtc/@code" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
									</input>
								</label>
								<xsl:value-of
									select="concat(' ', /source/supply-generation/mtc/@description)" />

								<br />
								<label>
									<xsl:value-of select="'CoP '" />
									<select name="cop-id">
										<xsl:for-each select="/source/cop">
											<option value="{@id}">
												<xsl:choose>
													<xsl:when test="/source/request/parameter[@name='cop-id']">
														<xsl:if
															test="@id = /source/request/parameter[@name='cop-id']/value">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if test="@id = /source/supply-generation/cop/@id">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of select="concat(@code, ' - ', @description)" />
											</option>
										</xsl:for-each>
									</select>
								</label>
								<br />
								<label>
									<xsl:value-of select="'Standard Settlement Configuration '" />
									<input name="ssc-code" size="4" maxlength="4">
										<xsl:attribute name="value">
												<xsl:choose>
													<xsl:when test="/source/request/parameter[@name='ssc-code']">
														<xsl:value-of
											select="/source/request/parameter[@name='ssc-code']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of select="/source/supply-generation/ssc/@code" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
									</input>
								</label>
								<xsl:value-of
									select="concat(' ', /source/supply-generation/ssc/@description)" />

								<br />
								<br />
								<fieldset>
									<legend>Import MPAN</legend>
									<label>
										Has an import MPAN?
										<input type="checkbox" name="has-import-mpan" value="true">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='has-import-mpan']/value">
													<xsl:attribute name="checked">
														<xsl:value-of select="'checked'" />
													</xsl:attribute>
												</xsl:when>
												<xsl:when
													test="/source/supply-generation/mpan[llfc/@is-import='true']">
													<xsl:attribute name="checked">
														<xsl:value-of select="'checked'" />
													</xsl:attribute>
												</xsl:when>
											</xsl:choose>
										</input>
									</label>
									<br />
									<br />
									<label>
										<xsl:value-of select="'Line Loss Factor Class '" />
										<input name="import-llfc-code" size="3" maxlength="3">
											<xsl:attribute name="value">
												<xsl:choose>
													<xsl:when
												test="/source/request/parameter[@name='import-llfc-code']">
														<xsl:value-of
												select="/source/request/parameter[@name='import-llfc-code']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
												select="/source/supply-generation/mpan[llfc/@is-import='true']/llfc/@code" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<xsl:value-of
										select="concat(' ', /source/supply-generation/mpan[llfc/@is-import='true']/llfc/@description)" />
									<br />
									<label>
										<xsl:value-of select="'MPAN Core '" />
										<input name="import-mpan-core" size="16">
											<xsl:attribute name="value">
													<xsl:choose>
														<xsl:when
												test="/source/request/parameter[@name='import-mpan-core']">
															<xsl:value-of
												select="/source/request/parameter[@name='import-mpan-core']/value">
															</xsl:value-of>
														</xsl:when>
														<xsl:otherwise>
																<xsl:value-of
												select="/source/supply-generation/mpan[llfc/@is-import='true']/mpan-core/@core" />
														</xsl:otherwise>
														</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<br />
									<label>
										Agreed Supply Capacity
										<input name="import-agreed-supply-capacity" size="9"
											maxlength="9">
											<xsl:attribute name="value">
												<xsl:choose>
													<xsl:when
												test="/source/request/parameter[@name='import-agreed-supply-capacity']">
														<xsl:value-of
												select="/source/request/parameter[@name='import-agreed-supply-capacity']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
												select="/source/supply-generation/mpan[llfc/@is-import='true']/@agreed-supply-capacity" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
										<xsl:value-of select="' kVA'" />
									</label>
									<br />
									<label>
										<xsl:value-of select="'Supplier Contract '" />
										<select name="import-supplier-contract-id">
											<xsl:for-each select="/source/supplier-contract">
												<option value="{@id}">
													<xsl:choose>
														<xsl:when
															test="/source/request/parameter[@name='import-supplier-contract-id']">
															<xsl:if
																test="@id = /source/request/parameter[@name='import-supplier-contract-id']/value">
																<xsl:attribute name="selected" />
															</xsl:if>
														</xsl:when>
														<xsl:otherwise>
															<xsl:if
																test="@id = /source/supply-generation/mpan[llfc/@is-import='true']/supplier-contract/@id">
																<xsl:attribute name="selected" />
															</xsl:if>
														</xsl:otherwise>
													</xsl:choose>
													<xsl:value-of select="@name" />
												</option>
											</xsl:for-each>
										</select>
									</label>
									<br />
									<label>
										Supplier Account
										<input name="import-supplier-account">
											<xsl:attribute name="value">
												<xsl:choose>
													<xsl:when
												test="/source/request/parameter[@name='import-supplier-account']">
														<xsl:value-of
												select="/source/request/parameter[@name='import-supplier-account']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
												select="/source/supply-generation/mpan[llfc/@is-import='true']/@supplier-account" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<br />
								</fieldset>
								<br />
								<fieldset>
									<legend>Export MPAN</legend>
									<label>
										Has an export MPAN?
										<input type="checkbox" name="has-export-mpan" value="true">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='has-export-mpan']/value">
													<xsl:attribute name="checked">
														<xsl:value-of select="'checked'" />
													</xsl:attribute>
												</xsl:when>
												<xsl:when
													test="/source/supply-generation/mpan[llfc/@is-import='false']">
													<xsl:attribute name="checked">
														<xsl:value-of select="'checked'" />
													</xsl:attribute>
												</xsl:when>
											</xsl:choose>
										</input>
									</label>
									<br />
									<br />
									<label>
										<xsl:value-of select="'Line Loss Factor Class '" />
										<input name="export-llfc-code" size="3" maxlength="3">
											<xsl:attribute name="value">
												<xsl:choose>
													<xsl:when
												test="/source/request/parameter[@name='export-llfc-code']">
														<xsl:value-of
												select="/source/request/parameter[@name='export-llfc-code']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
												select="/source/supply-generation/mpan[llfc/@is-import='false']/llfc/@code" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<xsl:value-of
										select="concat(' ', /source/supply-generation/mpan[llfc/@is-import='false']/llfc/@description)" />
									<br />
									<label>
										<xsl:value-of select="'MPAN Core '" />
										<input name="export-mpan-core" size="16">
											<xsl:attribute name="value">
													<xsl:choose>
														<xsl:when
												test="/source/request/parameter[@name='export-mpan-core']">
															<xsl:value-of
												select="/source/request/parameter[@name='export-mpan-core']/value">
															</xsl:value-of>
														</xsl:when>
														<xsl:otherwise>
																<xsl:value-of
												select="/source/supply-generation/mpan[llfc/@is-import='false']/mpan-core/@core" />
														</xsl:otherwise>
														</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<br />
									<label>
										Agreed Supply Capacity
										<input name="export-agreed-supply-capacity" size="9"
											maxlength="9">
											<xsl:attribute name="value">
												<xsl:choose>
													<xsl:when
												test="/source/request/parameter[@name='export-agreed-supply-capacity']">
														<xsl:value-of
												select="/source/request/parameter[@name='export-agreed-supply-capacity']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
												select="/source/supply-generation/mpan[llfc/@is-import='false']/@agreed-supply-capacity" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
										<xsl:value-of select="' kVA'" />
									</label>
									<br />
									<label>
										<xsl:value-of select="'Supplier Contract '" />
										<select name="export-supplier-contract-id">
											<xsl:for-each select="/source/supplier-contract">
												<option value="{@id}">
													<xsl:choose>
														<xsl:when
															test="/source/request/parameter[@name='export-supplier-contract-id']">
															<xsl:if
																test="@id = /source/request/parameter[@name='export-supplier-contract-id']/value">
																<xsl:attribute name="selected" />
															</xsl:if>
														</xsl:when>
														<xsl:otherwise>
															<xsl:if
																test="@id = /source/supply-generation/mpan[llfc/@is-import='false']/supplier-contract/@id">
																<xsl:attribute name="selected" />
															</xsl:if>
														</xsl:otherwise>
													</xsl:choose>
													<xsl:value-of select="@name" />
												</option>
											</xsl:for-each>
										</select>
									</label>
									<xsl:value-of select="' '" />
									<a
										href="{/source/request/@context-path}/supplier-contracts/{/source/supply-generation/mpan[llfc/@is-import='false']/account/supplier-contract/@id}">
										<xsl:value-of
											select="/source/supply-generation/mpan[llfc/@is-import='false']/account/supplier-contract/@name" />
									</a>
									<br />
									<label>
										Supplier Account
										<input name="export-supplier-account">
											<xsl:attribute name="value">
												<xsl:choose>
													<xsl:when
												test="/source/request/parameter[@name='export-supplier-account']">
														<xsl:value-of
												select="/source/request/parameter[@name='export-supplier-account']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
												select="/source/supply-generation/mpan[llfc/@is-import='false']/@supplier-account" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<br />
								</fieldset>
								<br />
								<input type="submit" value="Update" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
						<br />
						<xsl:if test="not(/source/@num-generations='1')">
							<form action=".">
								<fieldset>
									<legend>
										Delete this supply generation
									</legend>
									<input type="hidden" name="view" value="confirm-delete" />
									<input type="submit" value="Delete" />
								</fieldset>
							</form>
						</xsl:if>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>