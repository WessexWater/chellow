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
					Chellow &gt;
					Supplier Contracts &gt;
					<xsl:value-of
						select="/source/register-read/bill/batch/supplier-contract/@name" />
					&gt; Batches &gt;
					<xsl:value-of select="/source/register-read/bill/batch/@reference" />
					&gt; Bills &gt;
					<xsl:value-of select="/source/register-read/bill/@id" />
					&gt; Reads &gt;
					<xsl:value-of select="/source/register-read/@id" />
				</title>
			</head>

			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					&gt;
					<a href="{/source/request/@context-path}/supplier-contracts/">
						<xsl:value-of select="'Supplier Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplier-contracts/{/source/register-read/bill/batch/supplier-contract/@id}/">
						<xsl:value-of
							select="/source/register-read/bill/batch/supplier-contract/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplier-contracts/{/source/register-read/bill/batch/supplier-contract/@id}/batches/">
						<xsl:value-of select="'Batches'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplier-contracts/{/source/register-read/bill/batch/supplier-contract/@id}/batches/{/source/register-read/bill/batch/@id}/">
						<xsl:value-of select="/source/register-read/bill/batch/@reference" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplier-contracts/{/source/register-read/bill/batch/supplier-contract/@id}/batches/{/source/register-read/bill/batch/@id}/bills/">
						<xsl:value-of select="'Bills'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplier-contracts/{/source/register-read/bill/batch/supplier-contract/@id}/batches/{/source/register-read/bill/batch/@id}/bills/{/source/register-read/bill/@id}/">
						<xsl:value-of select="/source/register-read/bill/@id" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplier-contracts/{/source/register-read/bill/batch/supplier-contract/@id}/batches/{/source/register-read/bill/batch/@id}/bills/{/source/register-read/bill/@id}/reads/">
						<xsl:value-of select="'Reads'" />
					</a>
					&gt;
					<xsl:value-of select="/source/register-read/@id" />
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
									register read?
								</legend>
								<input type="submit" name="delete" value="Delete" />
							</fieldset>
						</form>
						<p>
							<a href=".">Cancel</a>
						</p>
					</xsl:when>
					<xsl:otherwise>
						<form action="." method="post">
							<fieldset>
								<legend>Update this read</legend>
								<br />
								<label>
									<xsl:value-of select="'MPAN '" />
									<input name="mpan">
										<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when test="/source/request/parameters[@name='mpan']">
											<xsl:value-of
											select="/source/request/parameters[@name='mpan']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of select="/source/register-read/@mpan-str" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
									</input>
								</label>
								<br />
								<label>
									<xsl:value-of select="'Coefficient '" />
									<input name="coefficient">
										<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when test="/source/request/parameters[@name='coefficient']">
											<xsl:value-of
											select="/source/request/parameters[@name='coefficient']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of select="/source/register-read/@coefficient" />
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
											test="/source/request/parameters[@name='meter-serial-number']">
											<xsl:value-of
											select="/source/request/parameters[@name='meter-serial-number']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of select="/source/register-read/@meter-serial-number" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
									</input>

								</label>
								<br />
								<label>
									<xsl:value-of select="'Units '" />
									<input name="units">
										<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when test="/source/request/parameters[@name='units']">
											<xsl:value-of
											select="/source/request/parameters[@name='units']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of select="/source/register-read/@units" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
									</input>
								</label>
								<br />
								<label>
									<xsl:value-of select="'TPR '" />
									<input name="tpr-code">
										<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when test="/source/request/parameters[@name='tpr-code']">
											<xsl:value-of
											select="/source/request/parameters[@name='tpr-code']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of select="/source/register-read/tpr/@code" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
									</input>
									<xsl:value-of select="' '" />
									<a
										href="{/source/request/@context-path}/tprs/{/source/register-read/tpr/@id}/">
										<xsl:value-of select="/source/register-read/tpr/@code" />
									</a>
								</label>
								<br />
								<br />
								<fieldset>
									<legend>Previous Read</legend>
									<fieldset>
										<legend>Date</legend>
										<input name="previous-year" size="4" maxlength="4">
											<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when test="/source/request/parameter[@name='previous-year']">
											<xsl:value-of
												select="/source/request/parameter[@name='previous-year']/value/text()" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
												select="/source/register-read/hh-start-date[@label='previous']/@year" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
										</input>
										-
										<select name="previous-month">
											<xsl:for-each select="/source/months/month">
												<option value="{@number}">
													<xsl:choose>
														<xsl:when
															test="/source/request/parameter[@name='previous-month']">
															<xsl:if
																test="/source/request/parameter[@name='previous-month']/value/text() = number(@number)">
																<xsl:attribute name="selected" />
															</xsl:if>
														</xsl:when>
														<xsl:otherwise>
															<xsl:if
																test="/source/register-read/hh-start-date[@label='previous']/@month = @number">
																<xsl:attribute name="selected" />
															</xsl:if>
														</xsl:otherwise>
													</xsl:choose>
													<xsl:value-of select="@number" />
												</option>
											</xsl:for-each>
										</select>
										-
										<select name="previous-day">
											<xsl:for-each select="/source/days/day">
												<option value="{@number}">
													<xsl:choose>
														<xsl:when
															test="/source/request/parameter[@name='previous-day']">
															<xsl:if
																test="/source/request/parameter[@name='previous-day']/value/text() = @number">
																<xsl:attribute name="selected" />
															</xsl:if>
														</xsl:when>
														<xsl:otherwise>
															<xsl:if
																test="/source/register-read/hh-start-date[@label='previous']/@day = @number">
																<xsl:attribute name="selected" />
															</xsl:if>
														</xsl:otherwise>
													</xsl:choose>
													<xsl:value-of select="@number" />
												</option>
											</xsl:for-each>
										</select>
										<xsl:value-of
											select="concat(' ', /source/register-read/hh-start-date[@label='previous']/@hour, ':', /source/register-read/hh-start-date[@label='previous']/@minute)" />
									</fieldset>
									<br />
									<label>
										<xsl:value-of select="'Value '" />
										<input name="previous-value">
											<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
												test="/source/request/parameters[@name='previous-value']">
											<xsl:value-of
												select="/source/request/parameters[@name='previous-value']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of select="/source/register-read/@previous-value" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
										</input>
									</label>
									<br />
									<label>
										<xsl:value-of select="'Type '" />
										<select name="previous-type-id">
											<xsl:for-each select="/source/read-type">
												<option value="{@id}">
													<xsl:choose>
														<xsl:when
															test="/source/request/parameter[@name='previous-type']">
															<xsl:if
																test="/source/request/parameter[@name='previous-type']/value/text() = number(@id)">
																<xsl:attribute name="selected" />
															</xsl:if>
														</xsl:when>
														<xsl:otherwise>
															<xsl:if
																test="/source/register-read/read-type[@label='previous']/@id = @id">
																<xsl:attribute name="selected" />
															</xsl:if>
														</xsl:otherwise>
													</xsl:choose>
													<xsl:value-of select="concat(@code, ' ', @description)" />
												</option>
											</xsl:for-each>
										</select>
									</label>
								</fieldset>
								<br />
								<br />
								<fieldset>
									<legend>Present Read</legend>
									<fieldset>
										<legend>Date</legend>
										<input name="present-year" size="4" maxlength="4">
											<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when test="/source/request/parameter[@name='present-year']">
											<xsl:value-of
												select="/source/request/parameter[@name='present-year']/value/text()" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
												select="/source/register-read/hh-start-date[@label='present']/@year" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
										</input>
										-
										<select name="present-month">
											<xsl:for-each select="/source/months/month">
												<option value="{@number}">
													<xsl:choose>
														<xsl:when
															test="/source/request/parameter[@name='present-month']">
															<xsl:if
																test="/source/request/parameter[@name='present-month']/value/text() = number(@number)">
																<xsl:attribute name="selected" />
															</xsl:if>
														</xsl:when>
														<xsl:otherwise>
															<xsl:if
																test="/source/register-read/hh-start-date[@label='present']/@month = @number">
																<xsl:attribute name="selected" />
															</xsl:if>
														</xsl:otherwise>
													</xsl:choose>
													<xsl:value-of select="@number" />
												</option>
											</xsl:for-each>
										</select>
										-
										<select name="present-day">
											<xsl:for-each select="/source/days/day">
												<option value="{@number}">
													<xsl:choose>
														<xsl:when test="/source/request/parameter[@name='present-day']">
															<xsl:if
																test="/source/request/parameter[@name='present-day']/value/text() = @number">
																<xsl:attribute name="selected" />
															</xsl:if>
														</xsl:when>
														<xsl:otherwise>
															<xsl:if
																test="/source/register-read/hh-start-date[@label='present']/@day = @number">
																<xsl:attribute name="selected" />
															</xsl:if>
														</xsl:otherwise>
													</xsl:choose>
													<xsl:value-of select="@number" />
												</option>
											</xsl:for-each>
										</select>
										<xsl:value-of
											select="concat(' ', /source/register-read/hh-start-date[@label='present']/@hour, ':', /source/register-read/hh-start-date[@label='present']/@minute)" />
									</fieldset>
									<br />
									<label>
										<xsl:value-of select="'Value '" />
										<input name="present-value">
											<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when test="/source/request/parameters[@name='present-value']">
											<xsl:value-of
												select="/source/request/parameters[@name='present-value']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of select="/source/register-read/@present-value" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
										</input>
									</label>
									<br />
									<label>
										<xsl:value-of select="'Type '" />
										<select name="present-type-id">
											<xsl:for-each select="/source/read-type">
												<option value="{@id}">
													<xsl:choose>
														<xsl:when
															test="/source/request/parameter[@name='present-type']">
															<xsl:if
																test="/source/request/parameter[@name='present-type']/value/text() = number(@id)">
																<xsl:attribute name="selected" />
															</xsl:if>
														</xsl:when>
														<xsl:otherwise>
															<xsl:if
																test="/source/register-read/read-type[@label='present']/@id = @id">
																<xsl:attribute name="selected" />
															</xsl:if>
														</xsl:otherwise>
													</xsl:choose>
													<xsl:value-of select="concat(@code, ' ', @description)" />
												</option>
											</xsl:for-each>
										</select>
									</label>
								</fieldset>
								<br />
								<br />
								<input type="submit" value="Update" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
						<br />
						<form action=".">
							<fieldset>
								<legend>Delete this read</legend>
								<input type="hidden" name="view" value="confirm-delete" />
								<input type="submit" value="Delete" />
							</fieldset>
						</form>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>