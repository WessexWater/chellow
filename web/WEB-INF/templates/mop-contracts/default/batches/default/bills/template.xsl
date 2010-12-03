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
					Chellow &gt; MOP Contracts &gt;
					<xsl:value-of select="/source/bills/batch/mop-contract/@name" />
					&gt; Batches &gt;
					<xsl:value-of select="/source/bills/batch/@reference" />
					&gt; Bills
				</title>
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					&gt;
					<a href="{/source/request/@context-path}/mop-contracts/">
						<xsl:value-of select="'MOP Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/mop-contracts/{/source/bills/batch/mop-contract/@id}/">
						<xsl:value-of select="/source/bills/batch/mop-contract/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/mop-contracts/{/source/bills/batch/mop-contract/@id}/batches/">
						<xsl:value-of select="'Batches'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/mop-contracts/{/source/bills/batch/mop-contract/@id}/batches/{/source/bills/batch/@id}/">
						<xsl:value-of select="/source/bills/batch/@reference" />
					</a>
					&gt;
					<xsl:value-of select="'Bills ['" />
					<a
						href="{/source/request/@context-path}/reports/91/output/?batch-id={/source/bills/batch/@id}">
						<xsl:value-of select="'view'" />
					</a>
					<xsl:value-of select="']'" />

					<xsl:if test="//message">
						<ul>
							<xsl:for-each select="//message">
								<li>
									<xsl:value-of select="@description" />
								</li>
							</xsl:for-each>
						</ul>
					</xsl:if>

				</p>
				<br />
				<table>
					<caption>Bills</caption>
					<thead>
						<tr>
							<th>Chellow Id</th>
							<th>Reference</th>
							<th>From</th>
							<th>To</th>
							<th>kWh</th>
							<th>Net</th>
							<th>VAT</th>
							<th>Gross</th>
							<th>Type</th>
							<th>Breakdown</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each select="/source/bills/bill">
							<tr>
								<td>
									<a href="{@id}/">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<xsl:value-of select="@reference" />
								</td>
								<td>
									<xsl:value-of
										select="concat(hh-start-date[@label='start']/@year, '-', hh-start-date[@label='start']/@month, '-', hh-start-date[@label='start']/@day)" />
								</td>
								<td>
									<xsl:value-of
										select="concat(hh-start-date[@label='finish']/@year, '-', hh-start-date[@label='finish']/@month, '-', hh-start-date[@label='finish']/@day)" />
								</td>
								<td>
									<xsl:value-of select="@kwh" />
								</td>
								<td>
									<xsl:value-of select="@net" />
								</td>
								<td>
									<xsl:value-of select="@vat" />
								</td>
								<td>
									<xsl:value-of select="@gross" />
								</td>
								<td>
									<xsl:value-of select="bill-type/@code" />
								</td>
								<td>
									<xsl:value-of select="@breakdown" />
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
				<br />
				<form action="." method="post">
					<fieldset>
						<legend>Add a bill</legend>

						<br />
						<label>
							<xsl:value-of select="'MPAN Core '" />
							<input name="mpan-core">
								<xsl:attribute name="value">
										<xsl:if test="/source/request/parameter[@name='mpan-core']">
											<xsl:value-of
									select="/source/request/parameter[@name='mpan-core']/value/text()" />
										</xsl:if>
								</xsl:attribute>
							</input>
						</label>
						<br />
						<label>
							<xsl:value-of select="'Reference '" />
							<input name="reference">
								<xsl:attribute name="value">
										<xsl:if test="/source/request/parameter[@name='reference']">
											<xsl:value-of
									select="/source/request/parameter[@name='reference']/value" />
										</xsl:if>
								</xsl:attribute>
							</input>
						</label>
						<br />
						<br />
						<fieldset>
							<legend>Issue Date</legend>
							<input name="issue-year" size="4" maxlength="4">
								<xsl:attribute name="value">
								    <xsl:choose>
									<xsl:when test="/source/request/parameter[@name='issue-year']">
											<xsl:value-of
									select="/source/request/parameter[@name='issue-year']/value/text()" />
									</xsl:when>
									<xsl:otherwise>
										<xsl:attribute name="value">
											<xsl:value-of select="/source/date/@year" />
										</xsl:attribute>
									</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
							</input>
							-
							<select name="issue-month">
								<xsl:for-each select="/source/months/month">
									<option value="{@number}">
										<xsl:choose>
											<xsl:when test="/source/request/parameter[@name='issue-month']">
												<xsl:if
													test="/source/request/parameter[@name='issue-month']/value/text() = number(@number)">
													<xsl:attribute name="selected" />
												</xsl:if>
											</xsl:when>
											<xsl:otherwise>
												<xsl:if test="/source/date/@month = number(@number)">
													<xsl:attribute name="selected" />
												</xsl:if>
											</xsl:otherwise>
										</xsl:choose>
										<xsl:value-of select="@number" />
									</option>
								</xsl:for-each>
							</select>
							-
							<select name="issue-day">
								<xsl:for-each select="/source/days/day">
									<option value="{@number}">
										<xsl:choose>
											<xsl:when test="/source/request/parameter[@name='issue-day']">
												<xsl:if
													test="/source/request/parameter[@name='issue-day']/value/text() = @number">
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
						<fieldset>
							<legend>Start Date</legend>
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
											<xsl:value-of select="/source/date/@year" />
										</xsl:attribute>
									</xsl:otherwise>
								</xsl:choose>
							</input>
							-
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
						<fieldset>
							<legend>Finish Date</legend>
							<input name="finish-year" size="4" maxlength="4">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when test="/source/request/parameter[@name='finish-year']">
											<xsl:value-of
									select="/source/request/parameter[@name='finish-year']/value/text()" />
										</xsl:when>
										<xsl:when test="/source/bill/hh-start-date[@label='finish']">
											<xsl:value-of
									select="/source/bill/hh-start-date[@label='finish']/@year" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of select="/source/date/@year" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
							</input>
							-
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
											<xsl:when test="/source/bill/hh-start-date[@label='finish']">
												<xsl:if
													test="/source/bill/hh-start-date[@label='finish']/@month = @number">
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
											<xsl:when test="/source/bill/hh-start-date[@label='finish']">
												<xsl:if
													test="/source/bill/hh-start-date[@label='finish']/@day = @number">
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
							<xsl:value-of select="'kWh '" />
							<input name="kwh">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when test="/source/request/parameters[@name='kwh']">
											<xsl:value-of
									select="/source/request/parameters[@name='kwh']/value" />
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
							<xsl:value-of select="'Net '" />
							<input name="net">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when test="/source/request/parameters[@name='net']">
											<xsl:value-of
									select="/source/request/parameters[@name='net']/value" />
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
							<xsl:value-of select="'VAT '" />
							<input name="vat">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when test="/source/request/parameters[@name='vat']">
											<xsl:value-of
									select="/source/request/parameters[@name='vat']/value" />
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
							<xsl:value-of select="'Gross '" />
							<input name="gross">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when test="/source/request/parameters[@name='gross']">
											<xsl:value-of
									select="/source/request/parameters[@name='gross']/value" />
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
							<xsl:value-of select="'Account '" />
							<input name="account">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when test="/source/request/parameters[@name='account']">
											<xsl:value-of
									select="/source/request/parameters[@name='account']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of select="''" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
							</input>
						</label>
						<br />
						<label>
							<xsl:value-of select="'Type '" />
							<select name="bill-type-id">
								<xsl:for-each select="/source/bill-type">
									<option value="{@id}">
										<xsl:choose>
											<xsl:when test="/source/request/parameter[@name='bill-type-id']">
												<xsl:if
													test="@id = /source/request/parameter[@name='bill-type-id']/value">
													<xsl:attribute name="selected" />
												</xsl:if>
											</xsl:when>
											<xsl:otherwise>
												<xsl:if test="@id = /source/supply/bill-type/@id">
													<xsl:attribute name="selected" />
												</xsl:if>
											</xsl:otherwise>
										</xsl:choose>
										<xsl:value-of select="concat(@code, ' ', @description)" />
									</option>
								</xsl:for-each>
							</select>
						</label>
						<br />
						<label>
							<xsl:value-of select="'Breakdown '" />
							<input name="breakdown">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when test="/source/request/parameters[@name='breakdown']">
											<xsl:value-of
									select="/source/request/parameters[@name='breakdown']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of select="''" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
							</input>
						</label>
						<br />
						<label>
							<xsl:value-of select="'Status '" />
							<select name="status">
								<option value="0">
									<xsl:choose>
										<xsl:when test="/source/request/parameter[@name='status']">
											<xsl:if
												test="/source/request/parameter[@name='status']/value/text() = 0">
												<xsl:attribute name="selected" />
											</xsl:if>
										</xsl:when>
										<xsl:otherwise>
										</xsl:otherwise>
									</xsl:choose>
									<xsl:value-of select="'Pending'" />
								</option>
								<option value="1">
									<xsl:choose>
										<xsl:when test="/source/request/parameter[@name='status']">
											<xsl:if
												test="/source/request/parameter[@name='status']/value/text() = 1">
												<xsl:attribute name="selected" />
											</xsl:if>
										</xsl:when>
										<xsl:otherwise>
										</xsl:otherwise>
									</xsl:choose>
									<xsl:value-of select="'Paid'" />
								</option>
								<option value="2">
									<xsl:choose>
										<xsl:when test="/source/request/parameter[@name='status']">
											<xsl:if
												test="/source/request/parameter[@name='status']/value/text() = 2">
												<xsl:attribute name="selected" />
											</xsl:if>
										</xsl:when>
										<xsl:otherwise>
										</xsl:otherwise>
									</xsl:choose>
									<xsl:value-of select="'Rejected'" />
								</option>
							</select>
						</label>
						<br />
						<br />
						<input type="submit" value="Add" />
						<input type="reset" value="Reset" />
					</fieldset>
				</form>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>