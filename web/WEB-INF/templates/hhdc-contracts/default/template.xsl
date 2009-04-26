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
					Chellow &gt; HHDC Contracts &gt;
					<xsl:value-of select="/source/hhdc-contract/@name" />
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
					<a
						href="{/source/request/@context-path}/hhdc-contracts/">
						<xsl:value-of select="'HHDC Contracts'" />
					</a>
					&gt;
					<xsl:value-of
						select="concat(/source/hhdc-contract/@name, ' [')" />
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
				<br />

				<form action="." method="post">
					<fieldset>
						<legend>Update Contract</legend>
						<label>
							HHDC
							<select name="provider-id">
								<xsl:for-each
									select="/source/provider">
									<option value="{@id}">
										<xsl:choose>
											<xsl:when
												test="/source/request/parameter[@name='provider-id']">
												<xsl:if
													test="/source/request/parameter[@name='provider-id']/value/text() = @id">
													<xsl:attribute
														name="selected" />
												</xsl:if>
											</xsl:when>
											<xsl:otherwise>
												<xsl:if
													test="/source/hhdc-contract/provider/@id = @id">
													<xsl:attribute
														name="selected" />
												</xsl:if>
											</xsl:otherwise>
										</xsl:choose>
										<xsl:value-of
											select="concat(participant/@code, ' : ', @name)" />
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
										<xsl:when
											test="/source/request/parameter[@name = 'name']/value">
											<xsl:value-of
												select="/source/request/parameter[@name = 'name']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
												select="/source/hhdc-contract/@name" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
							</input>
						</label>
						<br />
						<label>
							Frequency with which the data arrives
							<select name="frequency">
								<option value="daily">
									<xsl:choose>
										<xsl:when
											test="/source/request/parameter[@name = 'frequency']">
											<xsl:if
												test="/source/request/parameter[@name = 'frequency']/Value = 'daily'">
												<xsl:attribute
													name="selected" />
											</xsl:if>
										</xsl:when>
										<xsl:otherwise>
											<xsl:if
												test="/source/hhdc-contract/@frequency = 'daily'">
												<xsl:attribute
													name="selected" />
											</xsl:if>
										</xsl:otherwise>
									</xsl:choose>
									Daily
								</option>
								<option value="monthly">
									<xsl:choose>
										<xsl:when
											test="/source/request/parameter[@name = 'frequency']">
											<xsl:if
												test="/source/request/parameter[@name = 'frequency']/Value = 'monthly'">
												<xsl:attribute
													name="selected" />
											</xsl:if>
										</xsl:when>
										<xsl:otherwise>
											<xsl:if
												test="/source/hhdc-contract/@frequency = 'monthly'">
												<xsl:attribute
													name="selected" />
											</xsl:if>
										</xsl:otherwise>
									</xsl:choose>
									Monthly
								</option>
							</select>
						</label>
						<br />
						<label>
							Lag (number of days behind that the data is
							delivered)
							<input name="lag">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
											test="/source/request/parameter[@name = 'lag']">
											<xsl:value-of
												select="/source/request/parameter[@name = 'lag']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
												select="/source/hhdc-contract/@lag" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
							</input>
						</label>
						<br />
						<br />
						Charge script
						<br />
						<textarea name="charge-script" rows="40"
							cols="80">
							<xsl:choose>
								<xsl:when
									test="/source/request/parameter[@name='charge-script']">
									<xsl:value-of
										select="/source/@charge-script" />
								</xsl:when>
								<xsl:otherwise>
									<xsl:value-of
										select="/source/hhdc-contract/@charge-script" />
								</xsl:otherwise>
							</xsl:choose>
						</textarea>
						<br />
						<br />
						Properties
						<br />
						<textarea name="properties" rows="40"
							cols="80">
							<xsl:choose>
								<xsl:when
									test="/source/request/parameter[@name='properties']">
									<xsl:value-of
										select="/source/@properties" />
								</xsl:when>
								<xsl:otherwise>
									<xsl:value-of
										select="/source/hhdc-contract/@properties" />
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
								<xsl:when
									test="/source/request/parameter[@name='state']">
									<xsl:value-of
										select="/source/@state" />
								</xsl:when>
								<xsl:otherwise>
									<xsl:value-of
										select="/source/hhdc-contract/@state" />
								</xsl:otherwise>
							</xsl:choose>
						</textarea>
						<h4>Example</h4>
						<p>
							<code>
								<pre>
									lastImportDate0=2008-11-30
									lastImportName0=Example
								</pre>
							</code>
						</p>
						
						<br />
						<input type="submit" name="update-state"
							value="Update" />
						<input type="reset" value="Reset" />
					</fieldset>
				</form>
				<form action=".">
					<fieldset>
						<legend>Delete this contract</legend>
						<input type="hidden" name="view"
							value="confirm-delete" />
						<input type="submit" value="Delete" />
					</fieldset>
				</form>
				<ul>
					<li>
						<a href="accounts/">Accounts</a>
					</li>
					<li>
						<a href="hh-data-imports/">HH data imports</a>
					</li>
					<li>
						<a href="channel-snags/">Channel Snags</a>
					</li>
					<xsl:if
						test="/source/hhdc-contract/@has-automatic-hh-data-importer='true'">
						<li>
							<a
								href="automatic-hh-data-importer/">
								Automatic HH Data Importer
							</a>
						</li>
					</xsl:if>
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>