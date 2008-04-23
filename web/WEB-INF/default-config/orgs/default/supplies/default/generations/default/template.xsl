<?xml version="1.0" encoding="iso-8859-1"?>
<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="html" encoding="US-ASCII"
		doctype-public="-//W3C//DTD HTML 4.01//EN"
		doctype-system="http://www.w3.org/TR/html4/strict.dtd" indent="yes" />

	<xsl:template match="/">
		<html>
			<head>
				<title>
					Chellow &gt; Organizations &gt;
					<xsl:value-of
						select="/source/supply-generation/site-supply-generation/site/org/@name" />
					&gt; Supplies &gt;
					<xsl:value-of
						select="/source/supply-generation/supply/@id" />
					&gt; Generations &gt;
					<xsl:value-of
						select="/source/supply-generation/@id" />
				</title>

				<link rel="stylesheet" type="text/css"
					href="{/source/request/@context-path}/style/" />
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
						href="{/source/request/@context-path}/orgs/{/source/supply-generation/site-supply-generation/site/org/@id}/">
						<xsl:value-of
							select="/source/supply-generation/site-supply-generation/site/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/supply-generation/site-supply-generation/site/org/@id}/supplies/">
						<xsl:value-of select="'Supplies'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/supply-generation/site-supply-generation/site/org/@id}/supplies/{/source/supply-generation/supply/@id}/">
						<xsl:value-of
							select="/source/supply-generation/supply/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/supply-generation/site-supply-generation/site/org/@id}/supplies/{/source/supply-generation/supply/@id}/generations/">
						<xsl:value-of select="'Generations'" />
					</a>
					&gt;
					<xsl:value-of
						select="/source/supply-generation/@id" />
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
								<input type="submit" name="delete"
									value="Delete" />
							</fieldset>
						</form>
						<p>
							<a href=".">Cancel</a>
						</p>
					</xsl:when>
					<xsl:otherwise>
						<br />
						<table>
							<caption>Sites</caption>
							<thead>
								<tr>
									<th>Code</th>
									<th>Name</th>
									<th></th>
									<th></th>
									<xsl:if
										test="count(/source/supply-generation/site-supply-generation) > 1">
										<th></th>
									</xsl:if>
								</tr>
							</thead>
							<tbody>
								<xsl:for-each
									select="/source/supply-generation/site-supply-generation">
									<tr>
										<td>
											<a
												href="{/source/request/@context-path}/orgs/{site/org/@id}/sites/{site/@id}/">
												<xsl:value-of
													select="site/@code" />
											</a>
										</td>
										<td>
											<xsl:value-of
												select="site/@name" />
										</td>
										<td>
											<xsl:if
												test="@is-physical = 'true' and count(/source/supply-generation/site-supply-generation) > 1">
												Located here
											</xsl:if>
										</td>
										<td>
											<xsl:if
												test="@is-physical = 'false'">
												<form method="post"
													action=".">
													<fieldset>
														<legend>
															Set location
														</legend>
														<input
															type="hidden" name="site-id" value="{site/@id}" />
														<input
															type="submit" name="set-location" value="Set Location" />
													</fieldset>
												</form>
											</xsl:if>
										</td>
										<xsl:if
											test="count(/source/supply-generation/site-supply-generation) > 1">
											<td>
												<form method="post"
													action=".">
													<fieldset>
														<legend>
															Detach from
															site
														</legend>
														<input
															type="hidden" name="site-id" value="{site/@id}" />
														<input
															type="submit" name="detach" value="Detach" />
													</fieldset>
												</form>
											</td>
										</xsl:if>
									</tr>
								</xsl:for-each>
							</tbody>
						</table>
						<form method="post" action=".">
							<fieldset>
								<legend>Attach to another site</legend>
								<label>
									<xsl:value-of select="'Site Code '" />
									<input name="site-code"
										value="{/source/request/parameter[@name='site-code']/value}" />
								</label>
								<xsl:value-of select="' '" />
								<input type="submit" name="attach"
									value="Attach" />
								<input type="reset" />
							</fieldset>
						</form>

						<form action="." method="post">
							<fieldset>
								<legend>
									Update this supply generation
								</legend>
								<fieldset>
									<legend>Start date</legend>
									<input name="start-date-year">
										<xsl:choose>
											<xsl:when
												test="/source/request/parameter[@name='start-date-year']">
												<xsl:attribute
													name="value">
													<xsl:value-of
														select="/source/request/parameter[@name='start-date-year']/value/text()" />
												</xsl:attribute>
											</xsl:when>
											<xsl:otherwise>
												<xsl:attribute
													name="value">
													<xsl:value-of
														select="/source/supply-generation/hh-end-date[@label='start']/@year" />
												</xsl:attribute>
											</xsl:otherwise>
										</xsl:choose>
									</input>
									-
									<select name="start-date-month">
										<xsl:for-each
											select="/source/months/month">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='start-date-month']">
														<xsl:if
															test="/source/request/parameter[@name='start-date-month']/value/text() = number(@number)">
															<xsl:attribute
																name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if
															test="/source/supply-generation/hh-end-date[@label='start']/@month = @number">
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
									<select name="start-date-day">
										<xsl:for-each
											select="/source/days/day">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='start-date-day']">
														<xsl:if
															test="/source/request/parameter[@name='start-date-day']/value/text() = @number">
															<xsl:attribute
																name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if
															test="/source/supply-generation/hh-end-date[@label='start']/@day = @number">
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
									<xsl:value-of
										select="concat(' ', /source/supply-generation/hh-end-date[@label='start']/@hour, ':', /source/supply-generation/hh-end-date[@label='start']/@minute, 'Z')" />
								</fieldset>
								<br />
								<fieldset>
									<legend>End Date</legend>
									<label>
										Ended?
										<input type="checkbox"
											name="is-ended" value="true">
											<xsl:choose>
												<xsl:when
													test="/source/request/@method='post'">
													<xsl:if
														test="/source/request/parameter[@name='is-ended']">
														<xsl:attribute
															name="checked">
															checked
														</xsl:attribute>
													</xsl:if>
												</xsl:when>
												<xsl:otherwise>
													<xsl:if
														test="/source/supply-generation/hh-end-date[@label='finish']">
														<xsl:attribute
															name="checked">
															checked
														</xsl:attribute>
													</xsl:if>
												</xsl:otherwise>
											</xsl:choose>
										</input>
									</label>
									<xsl:value-of select="' '" />
									<input name="finish-date-year">
										<xsl:attribute name="value">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='finish-date-year']">
													<xsl:value-of
														select="/source/request/parameter[@name='finish-date-year']/value/text()" />
												</xsl:when>
												<xsl:when
													test="/source/supply-generation/hh-end-date[@label='finish']">
													<xsl:value-of
														select="/source/supply-generation/hh-end-date[@label='finish']/@year" />
												</xsl:when>
												<xsl:otherwise>
													<xsl:value-of
														select="/source/date/@year" />
												</xsl:otherwise>
											</xsl:choose>
										</xsl:attribute>
									</input>

									-
									<select name="finish-date-month">
										<xsl:for-each
											select="/source/months/month">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='finish-date-month']">

														<xsl:if
															test="/source/request/parameter[@name='finish-date-month']/value/text() = number(@number)">

															<xsl:attribute
																name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:when
														test="/source/supply-generation/hh-end-date[@label='finish']">
														<xsl:if
															test="/source/supply-generation/hh-end-date[@label='finish']/@month = @number">
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
									<select name="finish-date-day">
										<xsl:for-each
											select="/source/days/day">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='finish-date-day']">

														<xsl:if
															test="/source/request/parameter[@name='finish-date-day']/value/text() = @number">

															<xsl:attribute
																name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:when
														test="/source/supply-generation/hh-end-date[@label='finish']">
														<xsl:if
															test="/source/supply-generation/hh-end-date[@label='finish']/@day = @number">
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
									<xsl:if
										test="/source/supply-generation/hh-end-date[@label='finish']">
										<xsl:value-of
											select="concat(' ', /source/supply-generation/hh-end-date[@label='finish']/@hour, ':', /source/supply-generation/hh-end-date[@label='finish']/@minute, 'Z')" />
									</xsl:if>
								</fieldset>
								<br />
								<label>
									<xsl:value-of
										select="'Meter Serial Number '" />
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
														select="/source/supply-generation/meter/@serial-number" />
												</xsl:otherwise>
											</xsl:choose>
										</xsl:attribute>
									</input>
								</label>
								<br />
								<br />
								<fieldset>
									<legend>Import MPAN</legend>
									<label>
										Has an import MPAN?
										<input type="checkbox"
											name="has-import-mpan" value="true">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='has-import-mpan']/value">
													<xsl:attribute
														name="checked">
														<xsl:value-of
															select="'checked'" />
													</xsl:attribute>
												</xsl:when>
												<xsl:when
													test="/source/request/@method='get' and /source/supply-generation/mpan[@label='import']">
													<xsl:attribute
														name="checked">
														<xsl:value-of
															select="'checked'" />
													</xsl:attribute>
												</xsl:when>
											</xsl:choose>
										</input>
									</label>
									<br />
									<br />
									<label>
										<xsl:value-of
											select="'Profile Class '" />
										<select
											name="import-profile-class-id">
											<xsl:for-each
												select="/source/profile-class">
												<option value="{@id}">
													<xsl:value-of
														select="concat(@code, ' - ', @description)" />
													<xsl:choose>
														<xsl:when
															test="/source/request/parameter[@name='import-profile-class-id']">
															<xsl:if
																test="@id = /source/request/parameter[@name='import-profile-class-id']/value">
																<xsl:attribute
																	name="selected" />
															</xsl:if>
														</xsl:when>
														<xsl:otherwise>
															<xsl:if
																test="@id = /source/supply-generation/mpan[@label='import']/profile-class/@id">
																<xsl:attribute
																	name="selected" />
															</xsl:if>
														</xsl:otherwise>
													</xsl:choose>
												</option>
											</xsl:for-each>
										</select>

									</label>
									<br />
									<label>
										<xsl:value-of
											select="'Meter Timeswitch '" />
										<input
											name="import-meter-timeswitch-code" size="3" maxlength="3">
											<xsl:attribute
												name="value">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='import-meter-timeswitch-code']">
														<xsl:value-of
															select="/source/request/parameter[@name='import-meter-timeswitch-code']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
															select="/source/supply-generation/mpan[@label='import']/mpan-top/meter-timeswitch/@code" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<xsl:value-of
										select="concat(' ', /source/supply-generation/mpan[@label='import']/mpan-top/meter-timeswitch/@description)" />

									<br />
									<label>
										<xsl:value-of
											select="'Line Loss Factor '" />
										<input
											name="import-line-loss-factor-code" size="3" maxlength="3">
											<xsl:attribute
												name="value">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='import-line-loss-factor-code']">
														<xsl:value-of
															select="/source/request/parameter[@name='import-line-loss-factor-code']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
															select="/source/supply-generation/mpan[@label='import']/mpan-top/line-loss-factor/@code" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<xsl:value-of
										select="concat(' ', /source/supply-generation/mpan[@label='import']/mpan-top/line-loss-factor/@description)" />
									<br />
									<label>
										<xsl:value-of
											select="'MPAN Core '" />
										<select
											name="import-mpan-core-id">
											<xsl:for-each
												select="/source/supply-generation/supply/mpan-core">
												<option value="{@id}">
													<xsl:choose>
														<xsl:when
															test="/source/request/parameter[@name='import-mpan-core-id']">
															<xsl:if
																test="/source/request/parameter[@name='import-mpan-core-id']/value = @id">
																<xsl:attribute
																	name="selected" />
															</xsl:if>
														</xsl:when>
														<xsl:otherwise>
															<xsl:if
																test="/source/supply-generation/mpan[@label='import']/mpan-core/@id = @id">
																<xsl:attribute
																	name="selected" />
															</xsl:if>
														</xsl:otherwise>
													</xsl:choose>
													<xsl:value-of
														select="@core" />
												</option>
											</xsl:for-each>
										</select>
									</label>
									<br />
									<br />
									<label>
										Agreed Supply Capacity
										<input
											name="import-agreed-supply-capacity" size="9"
											maxlength="9">
											<xsl:attribute
												name="value">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='import-agreed-supply-capacity']">
														<xsl:value-of
															select="/source/request/parameter[@name='import-agreed-supply-capacity']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
															select="/source/supply-generation/mpan[@label='import']/@agreed-supply-capacity" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
										<xsl:value-of select="' kVA'" />
									</label>
									<br />
									<br />
									<label>
										Has import kWh?
										<input type="checkbox"
											name="import-has-import-kwh" value="true">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='import-has-import-kwh']/value">
													<xsl:attribute
														name="checked">
														<xsl:value-of
															select="'checked'" />
													</xsl:attribute>
												</xsl:when>
												<xsl:when
													test="/source/request/@method='get' and /source/supply-generation/mpan[@label='import']/@has-import-kwh='true'">
													<xsl:attribute
														name="checked">
														<xsl:value-of
															select="'checked'" />
													</xsl:attribute>
												</xsl:when>
											</xsl:choose>
										</input>
									</label>
									<br />
									<label>
										Has import kVArh?
										<input type="checkbox"
											name="import-has-import-kvarh" value="true">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='import-has-import-kvarh']/value">
													<xsl:attribute
														name="checked">
														<xsl:value-of
															select="'checked'" />
													</xsl:attribute>
												</xsl:when>
												<xsl:when
													test="/source/request/@method='get' and /source/supply-generation/mpan[@label='import']/@has-import-kvarh='true'">
													<xsl:attribute
														name="checked">
														<xsl:value-of
															select="'checked'" />
													</xsl:attribute>
												</xsl:when>
											</xsl:choose>

										</input>
									</label>
									<br />
									<label>
										Has export kWh?
										<input type="checkbox"
											name="import-has-export-kwh" value="true">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='import-has-export-kwh']/value">
													<xsl:attribute
														name="checked">
														<xsl:value-of
															select="'checked'" />
													</xsl:attribute>
												</xsl:when>
												<xsl:when
													test="/source/request/@method='get' and /source/supply-generation/mpan[@label='import']/@has-export-kwh='true'">
													<xsl:attribute
														name="checked">
														<xsl:value-of
															select="'checked'" />
													</xsl:attribute>
												</xsl:when>
											</xsl:choose>

										</input>
									</label>
									<br />
									<label>
										Has export kVArh?
										<input type="checkbox"
											name="import-has-export-kvarh" value="true">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='import-has-export-kvarh']/value">
													<xsl:attribute
														name="checked">
														<xsl:value-of
															select="'checked'" />
													</xsl:attribute>
												</xsl:when>
												<xsl:when
													test="/source/request/@method='get' and /source/supply-generation/mpan[@label='import']/@has-export-kvarh='true'">
													<xsl:attribute
														name="checked">
														<xsl:value-of
															select="'checked'" />
													</xsl:attribute>
												</xsl:when>
											</xsl:choose>
										</input>
									</label>
									<br />
									<br />
									<label>
										DCE Service
										<select
											name="import-dce-service-id">
											<option value="null">
												None
											</option>
											<xsl:for-each
												select="/source/dce">
												<optgroup
													label="{@name}">
													<xsl:for-each
														select="dce-service">
														<option
															value="{@id}">
															<xsl:choose>
																<xsl:when
																	test="/source/request/parameter[@name='import-dce-service-id']">
																	<xsl:if
																		test="/source/request/parameter[@name='import-dce-service-id']/value = @id">
																		<xsl:attribute
																			name="selected" />
																	</xsl:if>
																</xsl:when>
																<xsl:otherwise>
																	<xsl:if
																		test="/source/supply-generation/mpan[@label='import']/dce-service/@id = @id">
																		<xsl:attribute
																			name="selected" />
																	</xsl:if>
																</xsl:otherwise>
															</xsl:choose>
															<xsl:value-of
																select="concat(../@name, ': ', @name)" />
														</option>
													</xsl:for-each>
												</optgroup>
											</xsl:for-each>
										</select>
									</label>
									<br />
									<label>
										Supplier Name
										<input
											name="import-supplier-name">
											<xsl:attribute
												name="value">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='import-supplier-name']">
														<xsl:value-of
															select="/source/request/parameter[@name='import-supplier-name']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
															select="/source/supply-generation/mpan[@label='import']/supplier-service/supplier/@name" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<br />
									<label>
										Supplier Account
										<input
											name="import-supplier-account-reference">
											<xsl:attribute
												name="value">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='import-supplier-account-reference']">
														<xsl:value-of
															select="/source/request/parameter[@name='import-supplier-account-reference']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
															select="/source/supply-generation/mpan[@label='import']/account/@reference" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<xsl:value-of select="' '" />
									<a
										href="{/source/request/@context-path}/orgs/{/source/supply-generation/supply/org/@id}/suppliers/{/source/supply-generation/mpan[@label='import']/account/supplier/@id}/accounts/{/source/supply-generation/mpan[@label='import']/account[supplier]/@id}/">
										<xsl:value-of
											select="/source/supply-generation/mpan[@label='import']/account[supplier]/@reference" />
									</a>
									<br />
									<label>
										Supplier Service
										<input
											name="import-supplier-service-name">
											<xsl:attribute
												name="value">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='import-supplier-service-name']">
														<xsl:value-of
															select="/source/request/parameter[@name='import-supplier-service-name']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
															select="/source/supply-generation/mpan[@label='import']/supplier-service/@name" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<xsl:value-of select="' '" />
									<a
										href="{/source/request/@context-path}/orgs/{/source/supply-generation/supply/org/@id}/suppliers/{/source/supply-generation/mpan[@label='import']/account/supplier/@id}/services/{/source/supply-generation/mpan[@label='import']/supplier-service/@id}/">
										<xsl:value-of
											select="/source/supply-generation/mpan[@label='import']/supplier-service/@name" />
									</a>
									<br />
								</fieldset>
								<br />
								<fieldset>
									<legend>Export MPAN</legend>
									<label>
										Has an export MPAN?
										<input type="checkbox"
											name="has-export-mpan" value="true">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='has-export-mpan']/value">
													<xsl:attribute
														name="checked">
														<xsl:value-of
															select="'checked'" />
													</xsl:attribute>
												</xsl:when>
												<xsl:when
													test="/source/request/@method='get' and /source/supply-generation/mpan[@label='export']">
													<xsl:attribute
														name="checked">
														<xsl:value-of
															select="'checked'" />
													</xsl:attribute>
												</xsl:when>
											</xsl:choose>
										</input>
									</label>
									<br />
									<br />
									<label>
										<xsl:value-of
											select="'Profile Class '" />
										<select
											name="export-profile-class-id">
											<xsl:for-each
												select="/source/profile-class">
												<option value="{@id}">
													<xsl:value-of
														select="concat(@code, ' - ', @description)" />
													<xsl:choose>
														<xsl:when
															test="/source/request/parameter[@name='export-profile-class-id']">
															<xsl:if
																test="@id = /source/request/parameter[@name='export-profile-class-id']/value">
																<xsl:attribute
																	name="selected" />
															</xsl:if>
														</xsl:when>
														<xsl:otherwise>
															<xsl:if
																test="@id = /source/supply-generation/mpan[@label='export']/profile-class/@id">
																<xsl:attribute
																	name="selected" />
															</xsl:if>
														</xsl:otherwise>
													</xsl:choose>
												</option>
											</xsl:for-each>
										</select>

									</label>
									<br />
									<label>
										<xsl:value-of
											select="'Meter Timeswitch '" />
										<input
											name="export-meter-timeswitch-code" size="3" maxlength="3">
											<xsl:attribute
												name="value">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='export-meter-timeswitch-code']">
														<xsl:value-of
															select="/source/request/parameter[@name='export-meter-timeswitch-code']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
															select="/source/supply-generation/mpan[@label='export']/mpan-top/meter-timeswitch/@code" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<xsl:value-of
										select="concat(' ', /source/supply-generation/mpan[@label='export']/mpan-top/meter-timeswitch/@description)" />

									<br />
									<label>
										<xsl:value-of
											select="'Line Loss Factor '" />
										<input
											name="export-line-loss-factor-code" size="3" maxlength="3">
											<xsl:attribute
												name="value">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='export-line-loss-factor-code']">
														<xsl:value-of
															select="/source/request/parameter[@name='export-line-loss-factor-code']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
															select="/source/supply-generation/mpan[@label='export']/mpan-top/line-loss-factor/@code" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<xsl:value-of
										select="concat(' ', /source/supply-generation/mpan[@label='export']/mpan-top/line-loss-factor/@description)" />
									<br />
									<label>
										<xsl:value-of
											select="'MPAN Core '" />
										<select
											name="export-mpan-core-id">
											<xsl:for-each
												select="/source/supply-generation/supply/mpan-core">
												<option value="{@id}">
													<xsl:choose>
														<xsl:when
															test="/source/request/parameter[@name='export-mpan-core-id']">
															<xsl:if
																test="/source/request/parameter[@name='export-mpan-core-id']/value = @id">
																<xsl:attribute
																	name="selected" />
															</xsl:if>
														</xsl:when>
														<xsl:otherwise>
															<xsl:if
																test="/source/supply-generation/mpan[@label='export']/mpan-core/@id = @id">
																<xsl:attribute
																	name="selected" />
															</xsl:if>
														</xsl:otherwise>
													</xsl:choose>
													<xsl:value-of
														select="@core" />
												</option>
											</xsl:for-each>
										</select>
									</label>
									<br />
									<br />
									<label>
										Agreed Supply Capacity
										<input
											name="export-agreed-supply-capacity" size="9"
											maxlength="9">
											<xsl:attribute
												name="value">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='export-agreed-supply-capacity']">
														<xsl:value-of
															select="/source/request/parameter[@name='export-agreed-supply-capacity']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
															select="/source/supply-generation/mpan[@label='export']/@agreed-supply-capacity" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
										<xsl:value-of select="' kVA'" />
									</label>
									<br />
									<br />
									<label>
										Has import kWh?
										<input type="checkbox"
											name="export-has-import-kwh" value="true">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='export-has-import-kwh']/value">
													<xsl:attribute
														name="checked">
														<xsl:value-of
															select="'checked'" />
													</xsl:attribute>
												</xsl:when>
												<xsl:when
													test="/source/request/@method='get' and /source/supply-generation/mpan[@label='export']/@has-import-kwh='true'">
													<xsl:attribute
														name="checked">
														<xsl:value-of
															select="'checked'" />
													</xsl:attribute>
												</xsl:when>
											</xsl:choose>
										</input>
									</label>
									<br />
									<label>
										Has import kVArh?
										<input type="checkbox"
											name="export-has-import-kvarh" value="true">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='export-has-import-kvarh']/value">
													<xsl:attribute
														name="checked">
														<xsl:value-of
															select="'checked'" />
													</xsl:attribute>
												</xsl:when>
												<xsl:when
													test="/source/request/@method='get' and /source/supply-generation/mpan[@label='export']/@has-import-kvarh='true'">
													<xsl:attribute
														name="checked">
														<xsl:value-of
															select="'checked'" />
													</xsl:attribute>
												</xsl:when>
											</xsl:choose>

										</input>
									</label>
									<br />
									<label>
										Has export kWh?
										<input type="checkbox"
											name="export-has-export-kwh" value="true">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='export-has-export-kwh']/value">
													<xsl:attribute
														name="checked">
														<xsl:value-of
															select="'checked'" />
													</xsl:attribute>
												</xsl:when>
												<xsl:when
													test="/source/request/@method='get' and /source/supply-generation/mpan[@label='export']/@has-export-kwh='true'">
													<xsl:attribute
														name="checked">
														<xsl:value-of
															select="'checked'" />
													</xsl:attribute>
												</xsl:when>
											</xsl:choose>

										</input>
									</label>
									<br />
									<label>
										Has export kVArh?
										<input type="checkbox"
											name="export-has-export-kvarh" value="true">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='export-has-export-kvarh']/value">
													<xsl:attribute
														name="checked">
														<xsl:value-of
															select="'checked'" />
													</xsl:attribute>
												</xsl:when>
												<xsl:when
													test="/source/request/@method='get' and /source/supply-generation/mpan[@label='export']/@has-export-kvarh='true'">
													<xsl:attribute
														name="checked">
														<xsl:value-of
															select="'checked'" />
													</xsl:attribute>
												</xsl:when>
											</xsl:choose>
										</input>
									</label>
									<br />
									<br />
									<label>
										DCE Service
										<select
											name="export-dce-service-id">
											<option value="null">
												None
											</option>
											<xsl:for-each
												select="/source/dce">
												<optgroup
													label="{@name}">
													<xsl:for-each
														select="dce-service">
														<option
															value="{@id}">
															<xsl:choose>
																<xsl:when
																	test="/source/request/parameter[@name='export-dce-service-id']">
																	<xsl:if
																		test="/source/request/parameter[@name='export-dce-service-id']/value = @id">
																		<xsl:attribute
																			name="selected" />
																	</xsl:if>
																</xsl:when>
																<xsl:otherwise>
																	<xsl:if
																		test="/source/supply-generation/mpan[@label='export']/dce-service/@id = @id">
																		<xsl:attribute
																			name="selected" />
																	</xsl:if>
																</xsl:otherwise>
															</xsl:choose>
															<xsl:value-of
																select="concat(../@name, ': ', @name)" />
														</option>
													</xsl:for-each>
												</optgroup>
											</xsl:for-each>
										</select>
									</label>
									<br />
									<label>
										Supplier Name
										<input
											name="export-supplier-name">
											<xsl:attribute
												name="value">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='export-supplier-name']">
														<xsl:value-of
															select="/source/request/parameter[@name='export-supplier-name']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
															select="/source/supply-generation/mpan[@label='export']/supplier-service/supplier/@name" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<br />
									<label>
										Supplier Account
										<input
											name="export-supplier-account-reference">
											<xsl:attribute
												name="value">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='export-supplier-account-reference']">
														<xsl:value-of
															select="/source/request/parameter[@name='export-supplier-account-reference']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
															select="/source/supply-generation/mpan[@label='export']/account[supplier]/@reference" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<xsl:value-of select="' '" />
									<a
										href="{/source/request/@context-path}/orgs/{/source/supply-generation/supply/org/@id}/suppliers/{/source/supply-generation/mpan[@label='export']/account/supplier/@id}/accounts/{/source/supply-generation/mpan[@label='export']/account[supplier]/@id}">
										<xsl:value-of
											select="/source/supply-generation/mpan[@label='export']/account[supplier]/@reference" />
									</a>
									<br />
									<label>
										Supplier Service
										<input
											name="export-supplier-service-name">
											<xsl:attribute
												name="value">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='export-supplier-service-name']">
														<xsl:value-of
															select="/source/request/parameter[@name='export-supplier-service-name']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
															select="/source/supply-generation/mpan[@label='export']/supplier-service/@name" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<xsl:value-of select="' '" />
									<a
										href="{/source/request/@context-path}/orgs/{/source/supply-generation/supply/org/@id}/suppliers/{/source/supply-generation/mpan[@label='export']/account/supplier/@id}/services/{/source/supply-generation/mpan[@label='import']/supplier-service/@id}/">
										<xsl:value-of
											select="/source/supply-generation/mpan[@label='export']/supplier-service/@name" />
									</a>
									<br />
								</fieldset>
								<br />
								<input type="submit" value="Update" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
						<br />
						<form action=".">
							<fieldset>
								<legend>
									Delete this supply generation
								</legend>
								<input type="hidden" name="view"
									value="confirm-delete" />
								<input type="submit" value="Delete" />
							</fieldset>
						</form>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>