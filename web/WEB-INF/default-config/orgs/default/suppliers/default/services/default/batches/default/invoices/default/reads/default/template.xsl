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
						select="/source/register-read/invoice/batch/supplier-service/supplier/organization/@name" />
					&gt; Suppliers &gt;
					<xsl:value-of
						select="/source/register-read/invoice/batch/supplier-service/supplier/@name" />
					&gt; Services &gt;
					<xsl:value-of
						select="/source/register-read/invoice/batch/supplier-service/@name" />
					&gt; Batches &gt;
					<xsl:value-of
						select="/source/register-read/invoice/batch/@name" />
					&gt; Invoices &gt;
					<xsl:value-of
						select="/source/register-read/invoice/@id" />
					&gt; Reads &gt;
					<xsl:value-of select="/source/register-read/@id" />
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
						href="{/source/request/@context-path}/orgs/{/source/register-read/invoice/batch/supplier-service/supplier/organization/@id}/">
						<xsl:value-of
							select="/source/register-read/invoice/batch/supplier-service/supplier/organization/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/register-read/invoice/batch/supplier-service/supplier/organization/@id}/suppliers/">
						<xsl:value-of select="'Suppliers'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/register-read/invoice/batch/supplier-service/supplier/organization/@id}/suppliers/{/source/register-read/invoice/batch/supplier-service/supplier/@id}/">
						<xsl:value-of
							select="/source/register-read/invoice/batch/supplier-service/supplier/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/register-read/invoice/batch/supplier-service/supplier/organization/@id}/suppliers/{/source/register-read/invoice/batch/supplier-service/supplier/@id}/services/">
						<xsl:value-of select="'Services'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/register-read/invoice/batch/supplier-service/supplier/organization/@id}/suppliers/{/source/register-read/invoice/batch/supplier-service/supplier/@id}/">
						<xsl:value-of
							select="/source/register-read/invoice/batch/supplier-service/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/register-read/invoice/batch/supplier-service/supplier/organization/@id}/suppliers/{/source/register-read/invoice/batch/supplier-service/supplier/@id}/services/{/source/register-read/invoice/batch/supplier-service/@id}/batches/">
						<xsl:value-of select="'Batches'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/register-read/invoice/batch/supplier-service/supplier/organization/@id}/suppliers/{/source/register-read/invoice/batch/supplier-service/supplier/@id}/services/{/source/register-read/invoice/batch/supplier-service/@id}/batches/{/source/register-read/invoice/batch/@id}/">
						<xsl:value-of
							select="/source/register-read/invoice/batch/@reference" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/register-read/invoice/batch/supplier-service/supplier/organization/@id}/suppliers/{/source/register-read/invoice/batch/supplier-service/supplier/@id}/services/{/source/register-read/invoice/batch/supplier-service/@id}/batches/{/source/register-read/invoice/batch/@id}/invoices/">
						<xsl:value-of select="'Invoices'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/register-read/invoice/batch/supplier-service/supplier/organization/@id}/suppliers/{/source/register-read/invoice/batch/supplier-service/supplier/@id}/services/{/source/register-read/invoice/batch/supplier-service/@id}/batches/{/source/register-read/invoice/batch/@id}/invoices/{/source/register-read/invoice/@id}/">
						<xsl:value-of
							select="/source/register-read/invoice/@id" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/register-read/invoice/batch/supplier-service/supplier/organization/@id}/suppliers/{/source/register-read/invoice/batch/supplier-service/supplier/@id}/services/{/source/register-read/invoice/batch/supplier-service/@id}/batches/{/source/register-read/invoice/batch/@id}/invoices/">
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
				<form action="." method="post">
					<fieldset>
						<legend>Update this read</legend>
						<br />
						<label>
							<xsl:value-of select="'MPAN '" />
							<input name="mpan">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
											test="/source/request/parameters[@name='mpan']">
											<xsl:value-of
												select="/source/request/parameters[@name='mpan']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
												select="/source/register-read/mpan/@mpan" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
							</input>
							<xsl:value-of select="' '" />
							<a
								href="{/source/request/@context-path}/orgs/{/source/register-read/invoice/batch/supplier-service/supplier/organization/@id}/supplies/{/source/register-read/mpan/supply-generation/supply/@id}/generations/{/source/register-read/mpan/supply-generation/@id}/">
								<xsl:value-of
									select="/source/register-read/mpan/@mpan" />
							</a>
						</label>
						<br />
						<br />
						<label>
							<xsl:value-of select="'Coefficient '" />
							<input name="coefficient">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
											test="/source/request/parameters[@name='coefficient']">
											<xsl:value-of
												select="/source/request/parameters[@name='coefficient']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
												select="/source/register-read/@coefficient" />
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
										<xsl:when
											test="/source/request/parameters[@name='units']">
											<xsl:value-of
												select="/source/request/parameters[@name='units']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
												select="/source/register-read/@units" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
							</input>
						</label>
						<br />
						<label>
							<xsl:value-of select="'TPR '" />
							<input name="tpr">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
											test="/source/request/parameters[@name='tpr']">
											<xsl:value-of
												select="/source/request/parameters[@name='tpr']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
												select="/source/register-read/tpr/@code" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
							</input>
							<xsl:value-of select="' '" />
							<a
								href="{/source/request/@context-path}/tprs/{/source/register-read/tpr/@id}/">
								<xsl:value-of
									select="/source/register-read/tpr/@code" />
							</a>
						</label>
						<br />
						<label>
							<xsl:value-of select="'Is import? '" />
							<input name="is-import">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
											test="/source/request/parameters[@name='is-import']">
											<xsl:value-of
												select="/source/request/parameters[@name='is-import']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
												select="/source/register-read/@is-import" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
							</input>
						</label>
						<br />
						<br />
						<fieldset>
							<legend>Previous Read Date</legend>
							<input name="previous-read-date-year"
								size="4" maxlength="4">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
											test="/source/request/parameter[@name='previous-read-date-year']">
											<xsl:value-of
												select="/source/request/parameter[@name='previous-read-date-year']/value/text()" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
												select="/source/register-read/day-finish-date[@label='previous']/@year" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
							</input>
							-
							<select name="previous-read-date-month">
								<xsl:for-each
									select="/source/months/month">
									<option value="{@number}">
										<xsl:choose>
											<xsl:when
												test="/source/request/parameter[@name='previous-read-date-month']">
												<xsl:if
													test="/source/request/parameter[@name='previous-read-date-month']/value/text() = number(@number)">
													<xsl:attribute
														name="selected" />
												</xsl:if>
											</xsl:when>
											<xsl:otherwise>
												<xsl:if
													test="/source/register-read/day-finish-date[@label='previous']/@month = @number">
													<xsl:attribute
														name="selected" />
												</xsl:if>
											</xsl:otherwise>
										</xsl:choose>
										<xsl:value-of select="@number" />
									</option>
								</xsl:for-each>
							</select>
							-
							<select name="previous-read-date-day">
								<xsl:for-each
									select="/source/days/day">
									<option value="{@number}">
										<xsl:choose>
											<xsl:when
												test="/source/request/parameter[@name='previous-read-date-day']">
												<xsl:if
													test="/source/request/parameter[@name='previous-read-date-day']/value/text() = @number">
													<xsl:attribute
														name="selected" />
												</xsl:if>
											</xsl:when>
											<xsl:otherwise>
												<xsl:if
													test="/source/register-read/day-finish-date[@label='previous']/@day = @number">
													<xsl:attribute
														name="selected" />
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
							<xsl:value-of select="'Previous value '" />
							<input name="previous-value">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
											test="/source/request/parameters[@name='previous-value']">
											<xsl:value-of
												select="/source/request/parameters[@name='previous-value']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
												select="concat(/source/register-read/@previous-value)" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
							</input>
						</label>
						<br />
						<label>
							<xsl:value-of select="'Previous type '" />
							<input name="previous-type">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
											test="/source/request/parameters[@name='previous-type']">
											<xsl:value-of
												select="/source/request/parameters[@name='previous-type']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
												select="concat(/source/register-read/@previous-type)" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
							</input>
						</label>
						<br />
						<br />
						<fieldset>
							<legend>Present Read Date</legend>
							<input name="present-read-date-year"
								size="4" maxlength="4">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
											test="/source/request/parameter[@name='present-read-date-year']">
											<xsl:value-of
												select="/source/request/parameter[@name='present-read-date-year']/value/text()" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
												select="/source/register-read/day-finish-date[@label='present']/@year" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
							</input>
							-
							<select name="present-read-date-month">
								<xsl:for-each
									select="/source/months/month">
									<option value="{@number}">
										<xsl:choose>
											<xsl:when
												test="/source/request/parameter[@name='present-read-date-month']">
												<xsl:if
													test="/source/request/parameter[@name='present-read-date-month']/value/text() = number(@number)">
													<xsl:attribute
														name="selected" />
												</xsl:if>
											</xsl:when>
											<xsl:otherwise>
												<xsl:if
													test="/source/register-read/day-finish-date[@label='present']/@month = @number">
													<xsl:attribute
														name="selected" />
												</xsl:if>
											</xsl:otherwise>
										</xsl:choose>
										<xsl:value-of select="@number" />
									</option>
								</xsl:for-each>
							</select>
							-
							<select name="present-read-date-day">
								<xsl:for-each
									select="/source/days/day">
									<option value="{@number}">
										<xsl:choose>
											<xsl:when
												test="/source/request/parameter[@name='present-read-date-day']">
												<xsl:if
													test="/source/request/parameter[@name='present-read-date-day']/value/text() = @number">
													<xsl:attribute
														name="selected" />
												</xsl:if>
											</xsl:when>
											<xsl:otherwise>
												<xsl:if
													test="/source/register-read/day-finish-date[@label='present']/@day = @number">
													<xsl:attribute
														name="selected" />
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
							<xsl:value-of select="'Present value '" />
							<input name="present-value">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
											test="/source/request/parameters[@name='present-value']">
											<xsl:value-of
												select="/source/request/parameters[@name='present-value']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
												select="concat(/source/register-read/@present-value)" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
							</input>
						</label>
						<br />
						<label>
							<xsl:value-of select="'Present type '" />
							<input name="present-type">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
											test="/source/request/parameters[@name='present-type']">
											<xsl:value-of
												select="/source/request/parameters[@name='present-type']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
												select="concat(/source/register-read/@present-type)" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
							</input>
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
						<legend>Delete this read</legend>
						<input type="hidden" name="view"
							value="confirm-delete" />
						<input type="submit" value="Delete" />
					</fieldset>
				</form>
				<br />
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>