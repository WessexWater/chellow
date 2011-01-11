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
					Chellow &gt; HHDC Contracts &gt;
					<xsl:value-of select="/source/hhdc-contract/@name" />
				</title>
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					&gt;
					<a href="{/source/request/@context-path}/hhdc-contracts/">
						<xsl:value-of select="'HHDC Contracts'" />
					</a>
					&gt;
					<xsl:value-of select="concat(/source/hhdc-contract/@name, ' [')" />
					<a
						href="{/source/request/@context-path}/reports/115/output/?hhdc-contract-id={/source/hhdc-contract/@id}">
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
				<ul>
					<li>
						<a href="batches/">Batches</a>
					</li>
					<li>
						<a href="hh-data-imports/">HH data imports</a>
					</li>
					<li>
						<a href="rate-scripts/">Rate Scripts</a>
					</li>
				</ul>
				<br />
				<xsl:choose>
					<xsl:when
						test="/source/request/@method='get' and /source/request/parameter[@name='view']/value='confirm-delete'">
						<form method="post" action=".">
							<fieldset>
								<legend>Delete</legend>
								<p>
									Are you sure you want to delete this
									contract and its rate
									scripts?
								</p>
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
								<legend>Update Contract</legend>
								<label>
									HHDC
									<select name="participant-id">
										<xsl:for-each select="/source/provider">
											<option value="{participant/@id}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='participant-id']">
														<xsl:if
															test="/source/request/parameter[@name='participant-id']/value/text() = participant/@id">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if
															test="/source/hhdc-contract/provider/participant/@id = participant/@id">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of
													select="concat(participant/@code, ' : ', participant/@name, ' : ', @name)" />
											</option>
										</xsl:for-each>
									</select>
								</label>
								<br />
								<br />
								<label>
									<xsl:value-of select="'Name '" />
									<input name="name">
										<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when test="/source/request/parameter[@name = 'name']/value">
											<xsl:value-of
											select="/source/request/parameter[@name = 'name']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of select="/source/hhdc-contract/@name" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
									</input>
								</label>
								<br />
								<br />
								Charge script
								<br />
								<textarea name="charge-script" rows="40" cols="80">
									<xsl:choose>
										<xsl:when test="/source/request/parameter[@name='charge-script']">
											<xsl:value-of select="/source/@charge-script" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of select="/source/hhdc-contract/@charge-script" />
										</xsl:otherwise>
									</xsl:choose>
								</textarea>
								<br />
								<br />
								Properties
								<br />
								<textarea name="properties" rows="40" cols="80">
									<xsl:choose>
										<xsl:when test="/source/request/parameter[@name='properties']">
											<xsl:value-of select="/source/@properties" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of select="/source/hhdc-contract/@properties" />
										</xsl:otherwise>
									</xsl:choose>
								</textarea>
								<h4>Example</h4>
								<p>
									<code>
										<pre>
											has.importer=yes
											file.type=.df2
											hostname=example.com
											username=username
											password=password
											directory0=downloads1
											directory1=downloads2
								</pre>
									</code>
								</p>
								<br />
								<br />
								<input type="submit" value="Update" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
						<br />
						<form action="." method="post">
							<fieldset>
								<legend>Update State</legend>
								<label>State</label>
								<br />
								<textarea name="state" rows="40" cols="80">
									<xsl:choose>
										<xsl:when test="/source/request/parameter[@name='state']">
											<xsl:value-of select="/source/@state" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of select="/source/hhdc-contract/@state" />
										</xsl:otherwise>
									</xsl:choose>
								</textarea>
								<br />
								<input type="submit" name="update-state" value="Update" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
						<br />
						<form action=".">
							<fieldset>
								<legend>Delete this contract</legend>
								<input type="hidden" name="view" value="confirm-delete" />
								<input type="submit" value="Delete" />
							</fieldset>
						</form>
						<br />
						<form method="post" action=".">
							<fieldset>
								<legend>Ignore all snags before</legend>
								<br />
								<input name="ignore-year" size="4" maxlength="4">
									<xsl:choose>
										<xsl:when test="/source/request/parameter[@name='ignore-year']">

											<xsl:attribute name="value">
										<xsl:value-of
												select="/source/request/parameter[@name='ignore-year']/value/text()" />
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
								<select name="ignore-month">
									<xsl:for-each select="/source/months/month">
										<option value="{@number}">
											<xsl:choose>
												<xsl:when test="/source/request/parameter[@name='ignore-month']">
													<xsl:if
														test="/source/request/parameter[@name='ignore-month']/value/text() = number(@number)">
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
								<select name="ignore-day">
									<xsl:for-each select="/source/days/day">
										<option value="{@number}">
											<xsl:choose>
												<xsl:when test="/source/request/parameter[@name='ignore-day']">
													<xsl:if
														test="/source/request/parameter[@name='ignore-day']/value/text() = @number">
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
								<input type="submit" name="ignore-snags" value="Ignore" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>