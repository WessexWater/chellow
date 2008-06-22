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
						select="/source/invoice/batch/supplier-service/supplier/org/@name" />
					&gt; Suppliers &gt;
					<xsl:value-of
						select="/source/invoice/batch/supplier-service/supplier/@name" />
					&gt; Services &gt;
					<xsl:value-of
						select="/source/invoice/batch/supplier-service/@name" />
					&gt; Batches &gt;
					<xsl:value-of select="/source/invoice/batch/@name" />
					&gt; Invoices &gt;
					<xsl:value-of select="/source/invoice/@id" />
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
						href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-service/supplier/org/@id}/">
						<xsl:value-of
							select="/source/invoice/batch/supplier-service/supplier/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-service/supplier/org/@id}/suppliers/">
						<xsl:value-of select="'Suppliers'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-service/supplier/org/@id}/suppliers/{/source/invoice/batch/supplier-service/supplier/@id}/">
						<xsl:value-of
							select="/source/invoice/batch/supplier-service/supplier/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-service/supplier/org/@id}/suppliers/{/source/invoice/batch/supplier-service/supplier/@id}/services/">
						<xsl:value-of select="'Services'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-service/supplier/org/@id}/suppliers/{/source/invoice/batch/supplier-service/supplier/@id}/">
						<xsl:value-of
							select="/source/invoice/batch/supplier-service/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-service/supplier/org/@id}/suppliers/{/source/invoice/batch/supplier-service/supplier/@id}/services/{/source/invoice/batch/supplier-service/@id}/batches/">
						<xsl:value-of select="'Batches'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-service/supplier/org/@id}/suppliers/{/source/invoice/batch/supplier-service/supplier/@id}/services/{/source/invoice/batch/supplier-service/@id}/batches/{/source/invoice/batch/@id}/">
						<xsl:value-of
							select="/source/invoice/batch/@reference" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-service/supplier/org/@id}/suppliers/{/source/invoice/batch/supplier-service/supplier/@id}/services/{/source/invoice/batch/supplier-service/@id}/batches/{/source/invoice/batch/@id}/invoices/">
						<xsl:value-of select="'Invoices'" />
					</a>
					&gt;
					<xsl:value-of
						select="concat(/source/invoice/@id, ' [')" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-service/supplier/org/@id}/reports/46/screen/output/?invoice-id={/source/invoice/@id}">
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
				<xsl:choose>
					<xsl:when
						test="/source/request/@method='get' and /source/request/parameter[@name='view']/value='confirm-delete'">
						<form method="post" action=".">
							<fieldset>
								<legend>
									Are you sure you want to delete this
									invoice?
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

						<form action="." method="post">
							<fieldset>
								<legend>Update this invoice</legend>
								<br />
								<label>
									<xsl:value-of select="'Reference '" />
									<input name="reference">
										<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
													test="/source/request/parameters[@name='reference']">
											<xsl:value-of
														select="/source/request/parameters[@name='reference']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
														select="/source/invoice/@reference" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
									</input>
								</label>
								<br />
								<label>
									<xsl:value-of
										select="'Account Reference '" />
									<input name="account-reference">
										<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
													test="/source/request/parameters[@name='account-reference']">
											<xsl:value-of
														select="/source/request/parameters[@name='account-reference']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
														select="/source/invoice/bill/account/@reference" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
									</input>
									<xsl:value-of select="' '" />
									<a
										href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-service/supplier/org/@id}/suppliers/{/source/invoice/batch/supplier-service/supplier/@id}/accounts/{/source/invoice/bill/account/@id}/bills/{/source/invoice/bill/@id}/">
										<xsl:value-of select="'Bill'" />
									</a>
									<xsl:value-of select="' &gt; '" />
									<a
										href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-service/supplier/org/@id}/suppliers/{/source/invoice/batch/supplier-service/supplier/@id}/accounts/{/source/invoice/bill/account/@id}/">
										<xsl:value-of
											select="'Account'" />
									</a>
								</label>
								<br />
								<br />
								<fieldset>
									<legend>Issue Date</legend>
									<input name="issue-date-year"
										size="4" maxlength="4">
										<xsl:choose>
											<xsl:when
												test="/source/request/parameter[@name='issue-date-year']">
												<xsl:attribute
													name="value">
											<xsl:value-of
														select="/source/request/parameter[@name='issue-date-year']/value/text()" />
										</xsl:attribute>
											</xsl:when>
											<xsl:otherwise>
												<xsl:attribute
													name="value">
											<xsl:value-of
														select="/source/invoice/day-start-date[@label='issue']/@year" />
										</xsl:attribute>
											</xsl:otherwise>
										</xsl:choose>
									</input>
									-
									<select name="issue-date-month">
										<xsl:for-each
											select="/source/months/month">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='issue-date-month']">
														<xsl:if
															test="/source/request/parameter[@name='issue-date-month']/value/text() = number(@number)">
															<xsl:attribute
																name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if
															test="/source/invoice/day-start-date[@label='issue']/@month = @number">
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
									<select name="issue-date-day">
										<xsl:for-each
											select="/source/days/day">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='issue-date-day']">
														<xsl:if
															test="/source/request/parameter[@name='issue-date-day']/value/text() = @number">
															<xsl:attribute
																name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if
															test="/source/invoice/day-start-date[@label='issue']/@day = @number">
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
								<fieldset>
									<legend>Start Date</legend>
									<input name="start-date-year"
										size="4" maxlength="4">
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
														select="/source/invoice/day-start-date/@year" />
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
															test="/source/invoice/day-start-date/@month = @number">
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
															test="/source/invoice/day-start-date/@day = @number">
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
								<fieldset>
									<legend>Finish Date</legend>
									<input name="finish-date-year"
										size="4" maxlength="4">
										<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
													test="/source/request/parameter[@name='finish-date-year']">
											<xsl:value-of
														select="/source/request/parameter[@name='finish-date-year']/value/text()" />
										</xsl:when>
										<xsl:when
													test="/source/invoice/day-finish-date">
											<xsl:value-of
														select="/source/invoice/day-finish-date/@year" />
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
														test="/source/invoice/day-finish-date">
														<xsl:if
															test="/source/invoice/day-finish-date/@month = @number">
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
														test="/source/invoice/day-finish-date">
														<xsl:if
															test="/source/invoice/day-finish-date/@day = @number">
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
									<xsl:value-of select="'Net '" />
									<input name="net">
										<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
													test="/source/request/parameters[@name='net']">
											<xsl:value-of
														select="/source/request/parameters[@name='net']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
														select="/source/invoice/@net" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
									</input>
								</label>
								<br />
								<label>
									<xsl:value-of select="'VAT '" />
									<input name="vat">
										<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
													test="/source/request/parameters[@name='vat']">
											<xsl:value-of
														select="/source/request/parameters[@name='vat']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
														select="/source/invoice/@vat" />
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
										<option value="0">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='status']">
													<xsl:if
														test="/source/request/parameter[@name='status']/value/text() = 0">
														<xsl:attribute
															name="selected" />
													</xsl:if>
												</xsl:when>
												<xsl:otherwise>
													<xsl:if
														test="/source/invoice/@status = 0">
														<xsl:attribute
															name="selected" />
													</xsl:if>
												</xsl:otherwise>
											</xsl:choose>
											<xsl:value-of
												select="'Pending'" />
										</option>
										<option value="1">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='status']">
													<xsl:if
														test="/source/request/parameter[@name='status']/value/text() = 1">
														<xsl:attribute
															name="selected" />
													</xsl:if>
												</xsl:when>
												<xsl:otherwise>
													<xsl:if
														test="/source/invoice/@status = 1">
														<xsl:attribute
															name="selected" />
													</xsl:if>
												</xsl:otherwise>
											</xsl:choose>
											<xsl:value-of
												select="'Paid'" />
										</option>
										<option value="2">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='status']">
													<xsl:if
														test="/source/request/parameter[@name='status']/value/text() = 2">
														<xsl:attribute
															name="selected" />
													</xsl:if>
												</xsl:when>
												<xsl:otherwise>
													<xsl:if
														test="/source/invoice/@status = 2">
														<xsl:attribute
															name="selected" />
													</xsl:if>
												</xsl:otherwise>
											</xsl:choose>
											<xsl:value-of
												select="'Rejected'" />
										</option>
									</select>
								</label>
								<br />
								<br />
								<input type="submit" value="Update" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
						<br />
						<form action=".">
							<fieldset>
								<legend>Delete this invoice</legend>
								<input type="hidden" name="view"
									value="confirm-delete" />
								<input type="submit" value="Delete" />
							</fieldset>
						</form>
						<br />
						<h4>
							<a href="reads/">Register Reads</a>
						</h4>
						<h4>MPANs</h4>
						<xsl:if test="/source/invoice/invoice-mpan">
							<ul>
								<xsl:for-each
									select="/source/invoice/invoice-mpan">
									<li>
										<a
											href="{/source/request/@context-path}/orgs/{/source/invoice/batch/supplier-service/supplier/org/@id}/supplies/{mpan/supply-generation/supply/@id}/generations/{mpan/supply-generation/@id}/">
											<xsl:value-of
												select="mpan/@mpan" />
										</a>
									</li>
								</xsl:for-each>
							</ul>
						</xsl:if>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>