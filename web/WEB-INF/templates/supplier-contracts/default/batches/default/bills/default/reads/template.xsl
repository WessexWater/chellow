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
					Chellow
					&gt; Supplier Contracts &gt;
					<xsl:value-of
						select="/source/register-reads/bill/batch/supplier-contract/@name" />
					&gt; Batches &gt;
					<xsl:value-of select="/source/register-reads/bill/batch/@reference" />
					&gt; Bills &gt;
					<xsl:value-of select="/source/register-reads/bill/@id" />
					&gt; Reads
				</title>
			</head>

			<body>
				<p>
					<a href="{/source/request/@context-path}/reports/1/output/">
						<xsl:value-of select="'Chellow'" />
					</a>
					&gt;
					<a href="{/source/request/@context-path}/reports/75/output/">
						<xsl:value-of select="'Supplier Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/reports/77/output/?supplier-contract-id={/source/register-reads/bill/batch/supplier-contract/@id}">
						<xsl:value-of
							select="/source/register-reads/bill/batch/supplier-contract/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/reports/89/output/?supplier-contract-id={/source/register-reads/bill/batch/supplier-contract/@id}">
						<xsl:value-of select="'Batches'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/reports/91/output/?batch-id={/source/register-reads/bill/batch/@id}">
						<xsl:value-of select="/source/register-reads/bill/batch/@reference" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/reports/105/output/?bill-id={/source/register-reads/bill/@id}">
						<xsl:value-of select="concat('Bill ', /source/register-reads/bill/@id)" />
					</a>
					&gt;
					<xsl:value-of select="'Reads'" />
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
				<form action="." method="post">
					<fieldset>
						<legend>Add new register read</legend>
						<br />
						<label>
							<xsl:value-of select="'MPAN '" />
							<input name="mpan">
								<xsl:attribute name="value">
										<xsl:if test="/source/request/parameters[@name='mpan']">
											<xsl:value-of
									select="/source/request/parameters[@name='mpan']/value" />
										</xsl:if>
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
											<xsl:value-of select="'1'" />
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
										<xsl:if
									test="/source/request/parameters[@name='meter-serial-number']">
											<xsl:value-of
									select="/source/request/parameters[@name='meter-serial-number']/value" />
										</xsl:if>
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
											<xsl:value-of select="'kWh'" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
							</input>
						</label>
						<br />
						<label>
							<xsl:value-of select="'TPR '" />
							<input name="tpr-code">
								<xsl:attribute name="value" size="5" maxlength="5">
									<xsl:choose>
										<xsl:when test="/source/request/parameters[@name='tpr-code']">
											<xsl:value-of
									select="/source/request/parameters[@name='tpr-code']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of select="'00001'" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
							</input>
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
											<xsl:value-of select="/source/date/@year" />
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
								<select name="previous-day">
									<xsl:for-each select="/source/days/day">
										<option value="{@number}">
											<xsl:choose>
												<xsl:when test="/source/request/parameter[@name='previous-day']">
													<xsl:if
														test="/source/request/parameter[@name='previous-day']/value/text() = @number">
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
											<xsl:value-of select="'0'" />
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
												<xsl:when test="/source/request/parameter[@name='previous-type']">
													<xsl:if
														test="/source/request/parameter[@name='previous-type']/value/text() = number(@id)">
														<xsl:attribute name="selected" />
													</xsl:if>
												</xsl:when>
												<xsl:otherwise>
													<xsl:if test="@code = 'N'">
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
											<xsl:value-of select="/source/date/@year" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
								</input>
								-
								<select name="present-month">
									<xsl:for-each select="/source/months/month">
										<option value="{@number}">
											<xsl:choose>
												<xsl:when test="/source/request/parameter[@name='present-month']">
													<xsl:if
														test="/source/request/parameter[@name='present-month']/value/text() = number(@number)">
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
													<xsl:if test="/source/date/@day = @number">
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
											<xsl:value-of select="'0'" />
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
												<xsl:when test="/source/request/parameter[@name='present-type']">
													<xsl:if
														test="/source/request/parameter[@name='present-type']/value/text() = number(@id)">
														<xsl:attribute name="selected" />
													</xsl:if>
												</xsl:when>
												<xsl:otherwise>
													<xsl:if test="@code = 'N'">
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
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>