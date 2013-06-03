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
					Chellow &gt; Sites &gt;
					<xsl:value-of select="concat(/source/site/@code, ' ', /source/site/@name)" />
				</title>

				<link rel="stylesheet" type="text/css"
					href="{/source/request/@context-path}/reports/19/output/" />
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/reports/1/output/">
						<xsl:value-of select="'Home'" />
					</a>
					&gt;
					<a href="{/source/request/@context-path}/reports/3/output/">
						<xsl:value-of select="'Sites'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/reports/5/output/?site-id={/source/site/@id}">
						<xsl:value-of
							select="concat(/source/site/@code, ' ', /source/site/@name)" />
					</a>
					&gt; Edit
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
									site and any
									associated snags?
								</legend>
								<input type="submit" name="delete" value="Delete" />
							</fieldset>
						</form>
						<p>
							<a href=".">Cancel</a>
						</p>
					</xsl:when>
					<xsl:otherwise>
						<br />
						<form action="." method="post">
							<fieldset>
								<legend>Update this site</legend>
								<label>
									Name
									<xsl:value-of select="' '" />
									<input size="40" name="name" value="{/source/site/@name}" />
								</label>
								<br />
								<label>
									Code
									<xsl:value-of select="' '" />
									<input name="code" value="{/source/site/@code}" />
								</label>
								<br />
								<br />
								<input name="update" type="submit" value="Update" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>

						<br />
						<form action=".">
							<fieldset>
								<input type="hidden" name="view" value="confirm-delete" />
								<legend>Delete this site</legend>
								<input type="submit" value="Delete" />
							</fieldset>
						</form>
						<br />
						<table>
							<caption>Eras</caption>
							<tr>
								<th>Chellow Id</th>
								<th>Supply</th>
								<th>Supply Source</th>
								<th>Import MPAN core</th>
								<th>Export MPAN core</th>
								<th>From</th>
								<th>To</th>
							</tr>
							<xsl:for-each select="/source/site/era">
								<tr>
									<td>
										<a
											href="{/source/request/@context-path}/supplies/{supply/@id}/eras/{@id}/">
											<xsl:value-of select="@id" />
										</a>
									</td>
									<td>
										<a href="{/source/request/@context-path}/supplies/{supply/@id}/">
											<xsl:value-of select="supply/@id" />
										</a>
									</td>
									<td>
										<xsl:value-of select="supply/source/@code" />
									</td>
									<td>
										<xsl:value-of select="@imp-mpan-core" />

									</td>
									<td>
										<xsl:value-of select="@exp-mpan-core" />
									</td>
									<td>
										<xsl:value-of
											select="concat(hh-start-date[@label='start']/@year, '-', hh-start-date[@label='start']/@month, '-', hh-start-date[@label='start']/@day, ' ', hh-start-date[@label='start']/@hour, ':', hh-start-date[@label='start']/@minute, 'Z')" />
									</td>
									<td>
										<xsl:choose>
											<xsl:when test="hh-start-date[@label='finish']">
												<xsl:value-of
													select="concat(hh-start-date[@label='finish']/@year, '-', hh-start-date[@label='finish']/@month, '-', hh-start-date[@label='finish']/@day, ' ', hh-start-date[@label='finish']/@hour, ':', hh-start-date[@label='finish']/@minute, 'Z')" />
											</xsl:when>
											<xsl:otherwise>
												Ongoing
											</xsl:otherwise>
										</xsl:choose>
									</td>
								</tr>
							</xsl:for-each>
						</table>
						<br />
						<form action="." method="post">
							<fieldset>
								<legend>Insert a supply</legend>
								<br />
								<label>
									Source
									<select name="source-id">
										<xsl:for-each select="/source/source">
											<option value="{@id}">
												<xsl:if
													test="/source/request/parameter[@name='source-id']/value = @id">
													<xsl:attribute name="selected">
																<xsl:value-of select="'selected'" />
															</xsl:attribute>
												</xsl:if>
												<xsl:value-of select="concat(@code, ' : ', @name)" />
											</option>
										</xsl:for-each>
									</select>
								</label>
								<xsl:value-of select="' '" />
								<label>
									Generator Type (if source is 'gen' or 'gen-net')
									<select name="generator-type-id">
										<xsl:for-each select="/source/generator-type">
											<option value="{@id}">
												<xsl:if
													test="/source/request/parameter[@name='generator-type-id']/value = @id">
													<xsl:attribute name="selected">
																<xsl:value-of select="'selected'" />
															</xsl:attribute>
												</xsl:if>
												<xsl:value-of select="concat(@code, ' : ', @description)" />
											</option>
										</xsl:for-each>
									</select>
								</label>
								<br />
								<br />
								<label>
									<xsl:value-of select="'Name '" />
									<input name="name"
										value="{/source/request/parameter[@name = 'name']/value}" />
								</label>
								<br />
								<br />
								<fieldset>
									<legend>Start Date</legend>
									<input name="start-year" maxlength="4" size="4">
										<xsl:attribute name="value">
											<xsl:choose>
												<xsl:when test="/source/request/parameter[@name='start-year']">
													<xsl:value-of
											select="/source/request/parameter[@name='start-year']/value" />
												</xsl:when>
												<xsl:otherwise>
													<xsl:value-of select="/source/date/@year" />
												</xsl:otherwise>
											</xsl:choose>
										</xsl:attribute>
									</input>
									<xsl:value-of select="'-'" />
									<select name="start-month">
										<xsl:for-each select="/source/months/month">
											<option value="{@number}">
												<xsl:choose>
													<xsl:when test="/source/request/parameter[@name='start-month']">
														<xsl:if
															test="/source/request/parameter[@name='start-month']/value = @number">
															<xsl:attribute name="selected">
																<xsl:value-of select="'selected'" />
															</xsl:attribute>
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if test="/source/date/@month = @number">
															<xsl:attribute name="selected">
																<xsl:value-of select="'selected'" />
															</xsl:attribute>
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
															test="/source/request/parameter[@name='start-day']/value = @number">
															<xsl:attribute name="selected">
																<xsl:value-of select="'selected'" />
															</xsl:attribute>
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if test="/source/date/@day = @number">
															<xsl:attribute name="selected">
																<xsl:value-of select="'selected'" />
															</xsl:attribute>
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
									<xsl:value-of select="'Meter Serial Number '" />
									<input name="msn"
										value="{/source/request/parameter[@name = 'msn']/value}" />
								</label>
								<br />
								<br />
								<label>
									<xsl:value-of select="'GSP Group '" />
									<select name="gsp-group-id">
										<xsl:for-each select="/source/gsp-group">
											<option value="{@id}">
												<xsl:if
													test="@id = /source/request/parameter[@name='gsp-group-id']/value">
													<xsl:attribute name="selected" />
												</xsl:if>
												<xsl:value-of select="concat(@code, ' ', @description)" />
											</option>
										</xsl:for-each>
									</select>
								</label>
								<br />
								<br />
								<label>
									<xsl:value-of select="'MOP Contract '" />
									<select name="mop-contract-id">
										<xsl:for-each select="/source/mop-contract">
											<option value="{@id}">
												<xsl:if
													test="@id = /source/request/parameter[@name='mop-contract-id']/value">
													<xsl:attribute name="selected" />
												</xsl:if>
												<xsl:value-of select="@name" />
											</option>
										</xsl:for-each>
									</select>
								</label>
								<br />
								<label>
									<xsl:value-of select="'MOP Account '" />
									<input name="mop-account"
										value="{/source/request/parameter[@name = 'mop-account']/value}" />
								</label>
								<br />
								<br />
								<label>
									<xsl:value-of select="'HHDC Contract '" />
									<select name="hhdc-contract-id">
										<xsl:for-each select="/source/hhdc-contract">
											<option value="{@id}">
												<xsl:if
													test="@id = /source/request/parameter[@name='hhdc-contract-id']/value">
													<xsl:attribute name="selected" />
												</xsl:if>
												<xsl:value-of select="@name" />
											</option>
										</xsl:for-each>
									</select>
								</label>
								<br />
								<label>
									<xsl:value-of select="'HHDC Account '" />
									<input name="hhdc-account"
										value="{/source/request/parameter[@name = 'hhdc-account']/value}" />
								</label>
								<br />
								<br />
								<label>
									<xsl:value-of select="'Profile Class '" />
									<select name="pc-id">
										<xsl:for-each select="/source/pc">
											<option value="{@id}">
												<xsl:if
													test="@id = /source/request/parameter[@name='pc-id']/value">
													<xsl:attribute name="selected" />
												</xsl:if>
												<xsl:value-of select="concat(@code, ' ', @description)" />
											</option>
										</xsl:for-each>
									</select>
								</label>
								<br />
								<label>
									<xsl:value-of select="'MTC '" />
									<input name="mtc-code"
										value="{/source/request/parameter[@name = 'mtc-code']/value}" />
								</label>
								<br />
								<label>
									<xsl:value-of select="'CoP '" />
									<select name="cop-id">
										<xsl:for-each select="/source/cop">
											<option value="{@id}">
												<xsl:if
													test="@id = /source/request/parameter[@name='cop-id']/value">
													<xsl:attribute name="selected" />
												</xsl:if>
												<xsl:value-of select="concat(@code, ' ', @description)" />
											</option>
										</xsl:for-each>
									</select>
								</label>
								<br />
								<label>
									<xsl:value-of select="'SSC '" />
									<input name="ssc-code"
										value="{/source/request/parameter[@name = 'ssc-code']/value}" />
								</label>
								<br />
								<br />
								<fieldset>
									<legend>Import</legend>
									<label>
										<xsl:value-of select="'Mpan Core '" />
										<input name="import-mpan-core" size="35"
											value="{/source/request/parameter[@name = 'import-mpan-core']/value}" />
									</label>
									<br />
									<label>
										<xsl:value-of select="'LLFC '" />
										<input name="import-llfc-code"
											value="{/source/request/parameter[@name = 'import-llfc-code']/value}" />
									</label>
									<br />
									<br />
									<label>
										<xsl:value-of select="'Agreed Supply Capacity '" />
										<input name="import-agreed-supply-capacity"
											value="{/source/request/parameter[@name = 'import-agreed-supply-capacity']/value}" />
									</label>
									<br />
									<label>
										<xsl:value-of select="'Supplier Contract '" />
										<select name="import-supplier-contract-id">
											<xsl:for-each select="/source/supplier-contract">
												<option value="{@id}">
													<xsl:if
														test="@id = /source/request/parameter[@name='import-supplier-contract-id']/value">
														<xsl:attribute name="selected" />
													</xsl:if>
													<xsl:value-of select="@name" />
												</option>
											</xsl:for-each>
										</select>
									</label>
									<br />
									<label>
										<xsl:value-of select="'Supplier Account '" />
										<input name="import-supplier-account"
											value="{/source/request/parameter[@name = 'import-supplier-account']/value}" />
									</label>
								</fieldset>
								<br />
								<fieldset>
									<legend>Export</legend>
									<label>
										<xsl:value-of select="'Mpan Core '" />
										<input name="export-mpan-core" size="35"
											value="{/source/request/parameter[@name = 'export-mpan-core']/value}" />
									</label>
									<br />
									<label>
										<xsl:value-of select="'LLFC '" />
										<input name="export-llfc-code"
											value="{/source/request/parameter[@name = 'export-llfc-code']/value}" />
									</label>
									<br />
									<label>
										<xsl:value-of select="'Agreed Supply Capacity '" />
										<input name="export-agreed-supply-capacity"
											value="{/source/request/parameter[@name = 'export-agreed-supply-capacity']/value}" />
									</label>
									<br />
									<label>
										<xsl:value-of select="'Supplier Contract '" />
										<select name="export-supplier-contract-id">
											<xsl:for-each select="/source/supplier-contract">
												<option value="{@id}">
													<xsl:if
														test="@id = /source/request/parameter[@name='export-supplier-contract-id']/value">
														<xsl:attribute name="selected" />
													</xsl:if>
													<xsl:value-of select="@name" />
												</option>
											</xsl:for-each>
										</select>
									</label>
									<br />
									<label>
										<xsl:value-of select="'Supplier Account '" />
										<input name="export-supplier-account"
											value="{/source/request/parameter[@name = 'export-supplier-account']/value}" />
									</label>
								</fieldset>
								<br />
								<input name="insert" type="submit" value="Insert" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>