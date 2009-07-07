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
					&gt; Generations &gt;
					<xsl:value-of select="/source/supply-generation/@id" />
				</title>
				<link rel="stylesheet" type="text/css"
					href="{/source/request/@context-path}/style/" />
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
						href="{/source/request/@context-path}/supplies/{/source/supply-generation/supply/@id}/">
						<xsl:value-of select="/source/supply-generation/supply/@id" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/supply-generation/supply/@id}/generations/">
						<xsl:value-of select="'Generations'" />
					</a>
					&gt;
					<xsl:value-of select="concat(/source/supply-generation/@id, ' [')" />
					<a
						href="{/source/request/@context-path}/reports/31/output/?supply-generation-id={/source/supply-generation/@id}">
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
											<a href="{/source/request/@context-path}/sites/{site/@id}/">
												<xsl:value-of select="site/@code" />
											</a>
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
									<input name="start-date-year">
										<xsl:choose>
											<xsl:when
												test="/source/request/parameter[@name='start-date-year']">
												<xsl:attribute name="value">
													<xsl:value-of
													select="/source/request/parameter[@name='start-date-year']/value/text()" />
												</xsl:attribute>
											</xsl:when>
											<xsl:otherwise>
												<xsl:attribute name="value">
													<xsl:value-of
													select="/source/supply-generation/hh-end-date[@label='start']/@year" />
												</xsl:attribute>
											</xsl:otherwise>
										</xsl:choose>
									</input>
									-
									<select name="start-date-month">
										<xsl:for-each select="/source/months/month">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='start-date-month']">
														<xsl:if
															test="/source/request/parameter[@name='start-date-month']/value/text() = number(@number)">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if
															test="/source/supply-generation/hh-end-date[@label='start']/@month = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of select="@number" />
											</option>
										</xsl:for-each>
									</select>
									-
									<select name="start-date-day">
										<xsl:for-each select="/source/days/day">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='start-date-day']">
														<xsl:if
															test="/source/request/parameter[@name='start-date-day']/value/text() = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if
															test="/source/supply-generation/hh-end-date[@label='start']/@day = @number">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of select="@number" />
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
														test="/source/supply-generation/hh-end-date[@label='finish']">
														<xsl:attribute name="checked">
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
													<xsl:value-of select="/source/date/@year" />
												</xsl:otherwise>
											</xsl:choose>
										</xsl:attribute>
									</input>

									-
									<select name="finish-date-month">
										<xsl:for-each select="/source/months/month">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='finish-date-month']">

														<xsl:if
															test="/source/request/parameter[@name='finish-date-month']/value/text() = number(@number)">

															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:when
														test="/source/supply-generation/hh-end-date[@label='finish']">
														<xsl:if
															test="/source/supply-generation/hh-end-date[@label='finish']/@month = @number">
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
									<select name="finish-date-day">
										<xsl:for-each select="/source/days/day">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='finish-date-day']">

														<xsl:if
															test="/source/request/parameter[@name='finish-date-day']/value/text() = @number">

															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:when
														test="/source/supply-generation/hh-end-date[@label='finish']">
														<xsl:if
															test="/source/supply-generation/hh-end-date[@label='finish']/@day = @number">
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
									<xsl:if
										test="/source/supply-generation/hh-end-date[@label='finish']">
										<xsl:value-of
											select="concat(' ', /source/supply-generation/hh-end-date[@label='finish']/@hour, ':', /source/supply-generation/hh-end-date[@label='finish']/@minute, 'Z')" />
									</xsl:if>
								</fieldset>
								<br />
								<label>
									<xsl:value-of select="'GSP Group '" />
									<select name="gsp-group-id">
										<xsl:for-each select="/source/gsp-group">
											<option value="{@id}">
												<xsl:choose>
													<xsl:when test="/source/request/parameter[@name='gsp-group-id']">
														<xsl:if
															test="@id = /source/request/parameter[@name='gsp-group-id']/value">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if test="@id = /source/supply-generation/gsp-group/@id">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of select="concat(@code, ' ', @description)" />
											</option>
										</xsl:for-each>
									</select>
								</label>
								<br/>
								<label>
									HHDC Contract
									<input name="hhdc-contract-name">
										<xsl:attribute name="value">
												<xsl:choose>
													<xsl:when
											test="/source/request/parameter[@name='hhdc-contract-name']">
														<xsl:value-of
											select="/source/request/parameter[@name='hhdc-contract-name']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
											select="/source/supply-generation/account/hhdc-contract/@name" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
									</input>
								</label>
								<xsl:value-of select="' '" />
								<a
									href="{/source/request/@context-path}/hhdc-contracts/{/source/supply-generation/account/hhdc-contract/@id}/">
									<xsl:value-of
										select="/source/supply-generation/account/hhdc-contract/@name" />
								</a>
								<br />
								<label>
									HHDC Account
									<input name="hhdc-account-reference">
										<xsl:attribute name="value">
												<xsl:choose>
													<xsl:when
											test="/source/request/parameter[@name='hhdc-account-reference']">
														<xsl:value-of
											select="/source/request/parameter[@name='hhdc-account-reference']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
											select="/source/supply-generation/account[hhdc-contract]/@reference" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
									</input>
								</label>
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
										<xsl:value-of select="'Profile Class '" />
										<select name="import-pc-id">
											<xsl:for-each select="/source/pc">
												<option value="{@id}">
													<xsl:choose>
														<xsl:when
															test="/source/request/parameter[@name='import-pc-id']">
															<xsl:if
																test="@id = /source/request/parameter[@name='import-pc-id']/value">
																<xsl:attribute name="selected" />
															</xsl:if>
														</xsl:when>
														<xsl:otherwise>
															<xsl:if
																test="@id = /source/supply-generation/mpan[llfc/@is-import='true']/pc/@id">
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
										<input name="import-mtc-code" size="3" maxlength="3">
											<xsl:attribute name="value">
												<xsl:choose>
													<xsl:when
												test="/source/request/parameter[@name='import-mtc-code']">
														<xsl:value-of
												select="/source/request/parameter[@name='import-mtc-code']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
												select="/source/supply-generation/mpan[llfc/@is-import='true']/mtc/@code" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<xsl:value-of
										select="concat(' ', /source/supply-generation/mpan[llfc/@is-import='true']/mtc/@description)" />

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
										<xsl:value-of select="'SSC '" />
										<input name="import-ssc-code" size="16">
											<xsl:attribute name="value">
													<xsl:choose>
														<xsl:when
												test="/source/request/parameter[@name='import-ssc-code']">
															<xsl:value-of
												select="/source/request/parameter[@name='import-ssc-code']/value">
															</xsl:value-of>
														</xsl:when>
														<xsl:otherwise>
																<xsl:value-of
												select="/source/supply-generation/mpan[llfc/@is-import='true']/ssc/@code" />
														</xsl:otherwise>
														</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<xsl:value-of select="' '" />
									<a
										href="{/source/request/@context-path}/sscs/{/source/supply-generation/mpan[llfc/@is-import='true']/ssc/@id}/">
										<xsl:value-of
											select="concat(/source/supply-generation/mpan[llfc/@is-import='true']/ssc/@code, ' - ', /source/supply-generation/mpan[llfc/@is-import='true']/ssc/@description)" />
									</a>
									<br />
									<br />
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
									<br />
									<label>
										Supplier Contract
										<input name="import-supplier-contract-name">
											<xsl:attribute name="value">
												<xsl:choose>
													<xsl:when
												test="/source/request/parameter[@name='import-supplier-contract-name']">
														<xsl:value-of
												select="/source/request/parameter[@name='import-supplier-contract-name']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
												select="/source/supply-generation/mpan[llfc/@is-import='true']/account/supplier-contract/@name" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<br />
									<label>
										Supplier Account
										<input name="import-supplier-account-reference">
											<xsl:attribute name="value">
												<xsl:choose>
													<xsl:when
												test="/source/request/parameter[@name='import-supplier-account-reference']">
														<xsl:value-of
												select="/source/request/parameter[@name='import-supplier-account-reference']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
												select="/source/supply-generation/mpan[llfc/@is-import='true']/account[supplier-contract]/@reference" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<xsl:value-of select="' '" />
									<a
										href="{/source/request/@context-path}/supplier-contracts/{/source/supply-generation/mpan[llfc/@is-import='true']/account/supplier-contract/@id}/accounts/{/source/supply-generation/mpan[llfc/@is-import='true']/account[supplier-contract]/@id}/">
										<xsl:value-of
											select="/source/supply-generation/mpan[llfc/@is-import='import']/account[supplier-contract]/@reference" />
									</a>
									<br />
									<br />
									<br />
									<table>
										<caption>Invoices</caption>
										<thead>
											<tr>
												<th>Chellow Id</th>
												<th>Reference</th>
												<th>Bill</th>
												<th>From</th>
												<th>To</th>
												<th>Net</th>
												<th>VAT</th>
												<th>MPANs</th>
												<th>Status</th>
											</tr>
										</thead>
										<tbody>
											<xsl:for-each
												select="/source/supply-generation/mpan[llfc/@is-import='true']/invoice-mpan/invoice">
												<tr>
													<td>
														<a
															href="{/source/request/@context-path}/suppliers/{batch/supplier-service/supplier/@id}/services/{batch/supplier-service/@id}/batches/{batch/@id}/invoices/{@id}/">
															<xsl:value-of select="@id" />
														</a>
													</td>
													<td>
														<xsl:value-of select="@reference" />
													</td>
													<td>
														<a
															href="{/source/request/@context-path}/suppliers/{bill/account/supplier/@id}/accounts/{bill/account/@id}/bills/{bill/@id}/">
															<xsl:value-of select="bill/@id" />
														</a>
													</td>
													<td>
														<xsl:value-of
															select="concat(day-start-date/@year, '-', day-start-date/@month, '-', day-start-date/@day)" />
													</td>
													<td>
														<xsl:value-of
															select="concat(day-finish-date/@year, '-', day-finish-date/@month, '-', day-finish-date/@day)" />
													</td>
													<td>
														<xsl:value-of select="@net" />
													</td>
													<td>
														<xsl:value-of select="@vat" />
													</td>
													<td>
														<xsl:for-each select="mpan">
															<a
																href="{/source/request/@context-path}/supplies/{mpan/supply-generation/supplier/@id}/generations/{mpan/supply-generation/@id}/">
																<xsl:value-of select="@core" />
															</a>
															<xsl:value-of select="' '" />
														</xsl:for-each>
													</td>
													<td>
														<xsl:choose>
															<xsl:when test="@status='0'">
																Pending
															</xsl:when>
															<xsl:when test="@status='1'">
																Paid
															</xsl:when>
															<xsl:when test="@status='2'">
																Rejected
															</xsl:when>
														</xsl:choose>
													</td>
												</tr>
											</xsl:for-each>
										</tbody>
									</table>
									<br />
									<table>
										<caption>
											Register Reads
										</caption>
										<thead>
											<tr>
												<th>Chellow Id</th>
												<th>Coefficient</th>
												<th>Units</th>
												<th>TPR</th>
												<th>Is Import?</th>
												<th>Previous Date</th>
												<th>Previous Value</th>
												<th>Previous Type</th>
												<th>Present Date</th>
												<th>Present Value</th>
												<th>Present Type</th>
											</tr>
										</thead>
										<xsl:for-each
											select="/source/supply-generation/mpan[llfc/@is-import='true']/register-read">
											<tr>
												<td>
													<a
														href="{/source/request/@context-path}/suppliers/{invoice/batch/supplier-service/supplier/@id}/services/{invoice/batch/supplier-service/@id}/batches/{invoice/batch/@id}/invoices/{invoice/@id}/reads/{@id}/">
														<xsl:value-of select="@id" />
													</a>
												</td>
												<td>
													<xsl:value-of select="@coefficient" />
												</td>
												<td>
													<xsl:value-of select="@units" />
												</td>
												<td>
													<a href="{/source/request/@context-path}/tprs/{tpr/@id}/">
														<xsl:value-of select="tpr/@code" />
													</a>
												</td>
												<td>
													<xsl:value-of select="@is-import" />
												</td>
												<td>
													<xsl:value-of
														select="concat(day-finish-date[@label='previous']/@year, '-', day-finish-date[@label='previous']/@month, '-', day-finish-date[@label='previous']/@day)" />
												</td>
												<td>
													<xsl:value-of select="@previous-value" />
												</td>
												<td>
													<xsl:value-of select="@previous-type" />
												</td>
												<td>
													<xsl:value-of
														select="concat(day-finish-date[@label='present']/@year, '-', day-finish-date[@label='present']/@month, '-', day-finish-date[@label='present']/@day)" />
												</td>
												<td>
													<xsl:value-of select="@present-value" />
												</td>
												<td>
													<xsl:value-of select="@present-type" />
												</td>
											</tr>
										</xsl:for-each>
									</table>
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
										<xsl:value-of select="'Profile Class '" />
										<select name="export-pc-id">
											<xsl:for-each select="/source/pc">
												<option value="{@id}">
													<xsl:choose>
														<xsl:when
															test="/source/request/parameter[@name='export-pc-id']">
															<xsl:if
																test="@id = /source/request/parameter[@name='export-pc-id']/value">
																<xsl:attribute name="selected" />
															</xsl:if>
														</xsl:when>
														<xsl:otherwise>
															<xsl:if
																test="@id = /source/supply-generation/mpan[llfc/@is-import='false']/pc/@id">
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
										<input name="export-mtc-code" size="3" maxlength="3">
											<xsl:attribute name="value">
												<xsl:choose>
													<xsl:when
												test="/source/request/parameter[@name='export-mtc-code']">
														<xsl:value-of
												select="/source/request/parameter[@name='export-mtc-code']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
												select="/source/supply-generation/mpan[llfc/@is-import='false']/mtc/@code" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<xsl:value-of
										select="concat(' ', /source/supply-generation/mpan[llfc/@is-import='false']/mtc/@description)" />
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
										<xsl:value-of select="'SSC '" />
										<input name="export-ssc-code" size="16">
											<xsl:attribute name="value">
													<xsl:choose>
														<xsl:when
												test="/source/request/parameter[@name='export-ssc-code']">
															<xsl:value-of
												select="/source/request/parameter[@name='export-ssc-code']/value">
															</xsl:value-of>
														</xsl:when>
														<xsl:otherwise>
																<xsl:value-of
												select="/source/supply-generation/mpan[llfc/@is-import='false']/ssc/@code" />
														</xsl:otherwise>
														</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<xsl:value-of
										select="concat(' ', /source/supply-generation/mpan[llfc/@is-import='false']/ssc/@description)" />
									<br />
									<br />
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
									<br />
									<br />
									<label>
										Supplier Contract
										<input name="export-supplier-contract-name">
											<xsl:attribute name="value">
												<xsl:choose>
													<xsl:when
												test="/source/request/parameter[@name='export-supplier-contract-name']">
														<xsl:value-of
												select="/source/request/parameter[@name='export-supplier-contract-name']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
												select="/source/supply-generation/mpan[llfc/@is-import='false']/account/supplier-contract/@name" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<br />
									<label>
										Supplier Account
										<input name="export-supplier-account-reference">
											<xsl:attribute name="value">
												<xsl:choose>
													<xsl:when
												test="/source/request/parameter[@name='export-supplier-account-reference']">
														<xsl:value-of
												select="/source/request/parameter[@name='export-supplier-account-reference']/value" />
													</xsl:when>
													<xsl:otherwise>
														<xsl:value-of
												select="/source/supply-generation/mpan[llfc/@is-import='false']/account[supplier-contract]/@reference" />
													</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
										</input>
									</label>
									<xsl:value-of select="' '" />
									<a
										href="{/source/request/@context-path}/supplier-contracts/{/source/supply-generation/mpan[llfc/@is-import='false']/account/supplier-contract/@id}/accounts/{/source/supply-generation/mpan[llfc/@is-import='true']/account[supplier-contract]/@id}/">
										<xsl:value-of
											select="/source/supply-generation/mpan[llfc/@is-import='false']/account[supplier-contract]/@reference" />
									</a>
									<br />
									<br />
									<table>
										<caption>Invoices</caption>
										<thead>
											<tr>
												<th>Chellow Id</th>
												<th>Reference</th>
												<th>Bill</th>
												<th>From</th>
												<th>To</th>
												<th>Net</th>
												<th>VAT</th>
												<th>MPANs</th>
												<th>Status</th>
											</tr>
										</thead>
										<tbody>
											<xsl:for-each
												select="/source/supply-generation/mpan[llfc/@is-import='false']/invoice-mpan/invoice">
												<tr>
													<td>
														<a
															href="{/source/request/@context-path}/suppliers/{batch/supplier-service/supplier/@id}/services/{batch/supplier-service/@id}/batches/{batch/@id}/invoices/{@id}/">
															<xsl:value-of select="@id" />
														</a>
													</td>
													<td>
														<xsl:value-of select="@reference" />
													</td>
													<td>
														<a
															href="{/source/request/@context-path}/suppliers/{bill/account/supplier/@id}/accounts/{bill/account/@id}/bills/{bill/@id}/">
															<xsl:value-of select="bill/@id" />
														</a>
													</td>
													<td>
														<xsl:value-of
															select="concat(day-start-date/@year, '-', day-start-date/@month, '-', day-start-date/@day)" />
													</td>
													<td>
														<xsl:value-of
															select="concat(day-finish-date/@year, '-', day-finish-date/@month, '-', day-finish-date/@day)" />
													</td>
													<td>
														<xsl:value-of select="@net" />
													</td>
													<td>
														<xsl:value-of select="@vat" />
													</td>
													<td>
														<xsl:for-each select="mpan">
															<a
																href="{/source/request/@context-path}/supplies/{mpan/supply-generation/supplier/@id}/generations/{mpan/supply-generation/@id}/">
																<xsl:value-of select="@core" />
															</a>
															<xsl:value-of select="' '" />
														</xsl:for-each>
													</td>
													<td>
														<xsl:choose>
															<xsl:when test="@status='0'">
																Pending
															</xsl:when>
															<xsl:when test="@status='1'">
																Paid
															</xsl:when>
															<xsl:when test="@status='2'">
																Rejected
															</xsl:when>
														</xsl:choose>
													</td>
												</tr>
											</xsl:for-each>
										</tbody>
									</table>
									<br />
									<table>
										<caption>
											Register Reads
										</caption>
										<thead>
											<tr>
												<th>Chellow Id</th>
												<th>Coefficient</th>
												<th>Units</th>
												<th>TPR</th>
												<th>Is Import?</th>
												<th>Previous Date</th>
												<th>Previous Value</th>
												<th>Previous Type</th>
												<th>Present Date</th>
												<th>Present Value</th>
												<th>Present Type</th>
											</tr>
										</thead>
										<xsl:for-each
											select="/source/supply-generation/mpan[llfc/@is-import='false']/register-read">
											<tr>
												<td>
													<a
														href="{/source/request/@context-path}/suppliers/{invoice/batch/supplier-service/supplier/@id}/services/{invoice/batch/supplier-service/@id}/batches/{invoice/batch/@id}/invoices/{invoice/@id}/reads/{@id}/">
														<xsl:value-of select="@id" />
													</a>
												</td>
												<td>
													<xsl:value-of select="@coefficient" />
												</td>
												<td>
													<xsl:value-of select="@units" />
												</td>
												<td>
													<a href="{/source/request/@context-path}/tprs/{tpr/@id}/">
														<xsl:value-of select="tpr/@code" />
													</a>
												</td>
												<td>
													<xsl:value-of select="@is-import" />
												</td>
												<td>
													<xsl:value-of
														select="concat(day-finish-date[@label='previous']/@year, '-', day-finish-date[@label='previous']/@month, '-', day-finish-date[@label='previous']/@day)" />
												</td>
												<td>
													<xsl:value-of select="@previous-value" />
												</td>
												<td>
													<xsl:value-of select="@previous-type" />
												</td>
												<td>
													<xsl:value-of
														select="concat(day-finish-date[@label='present']/@year, '-', day-finish-date[@label='present']/@month, '-', day-finish-date[@label='present']/@day)" />
												</td>
												<td>
													<xsl:value-of select="@present-value" />
												</td>
												<td>
													<xsl:value-of select="@present-type" />
												</td>
											</tr>
										</xsl:for-each>
									</table>
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
								<input type="hidden" name="view" value="confirm-delete" />
								<input type="submit" value="Delete" />
							</fieldset>
						</form>
						<ul>
							<li>
								<a href="channels/">Channels</a>
							</li>
						</ul>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>