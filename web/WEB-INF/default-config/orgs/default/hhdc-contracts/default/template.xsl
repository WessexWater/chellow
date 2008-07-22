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
						select="/source/hhdc-contract/org/@name" />
					&gt; HHDC Contracts &gt;
					<xsl:value-of select="/source/hhdc-contract/@name" />
				</title>

			</head>

			<body>
				<xsl:if test="//message">
					<ul>
						<xsl:for-each select="//message">
							<li>
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>

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
						href="{/source/request/@context-path}/orgs/{/source/hhdc-contract/org/@id}/">
						<xsl:value-of
							select="/source/hhdc-contract/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/hhdc-contract/org/@id}/hhdc-contracts/">
						<xsl:value-of select="'HHDC Contracts'" />
					</a>
					&gt;
					<xsl:value-of
						select="concat(/source/hhdc-contract/@name, ' [')" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/hhdc-contract/org/@id}/reports/57/screen/output/?contract-id={/source/hhdc-contract/@id}">
						<xsl:value-of select="'view'" />
					</a>
					<xsl:value-of select="']'" />
				</p>
				<br />

				<form action="." method="post">
					<fieldset>
						<legend>Update Contract</legend>
						<label>
							HHDC
							<select name="participant-id">
								<xsl:for-each
									select="/source/provider">
									<option value="{participant/@id}">
										<xsl:choose>
											<xsl:when
												test="/source/request/parameter[@name='participant-id']">
												<xsl:if
													test="/source/request/parameter[@name='participant-id']/value/text() = participant/@id">
													<xsl:attribute
														name="selected" />
												</xsl:if>
											</xsl:when>
											<xsl:otherwise>
												<xsl:if
													test="/source/hhdc-contract/provider/participant/@id = participant/@id">
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
								<option value="0">
									<xsl:choose>
										<xsl:when
											test="/source/request/parameter[@name = 'frequency']">
											<xsl:if
												test="number(/source/request/parameter[@name = 'frequency']/Value) = '0'">
												<xsl:attribute
													name="selected" />
											</xsl:if>
										</xsl:when>
										<xsl:otherwise>
											<xsl:if
												test="/source/hhdc-contract/@frequency = '0'">
												<xsl:attribute
													name="selected" />
											</xsl:if>
										</xsl:otherwise>
									</xsl:choose>
									Daily
								</option>
								<option value="1">
									<xsl:choose>
										<xsl:when
											test="/source/request/parameter[@name = 'frequency']">
											<xsl:if
												test="number(/source/request/parameter[@name = 'frequency']/Value) = '1'">
												<xsl:attribute
													name="selected" />
											</xsl:if>
										</xsl:when>
										<xsl:otherwise>
											<xsl:if
												test="/source/hhdc-contract/@frequency = '1'">
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
						<input type="submit" value="Update" />
						<input type="reset" value="Reset" />
					</fieldset>
				</form>

				<form action="?view=confirm-delete">
					<fieldset>
						<legend>Delete this contract</legend>
						<input type="submit" value="Delete" />
					</fieldset>
				</form>

				<ul>
					<li>
						<a href="hh-data-imports/">HH data imports</a>
					</li>
					<li>
						<a href="channel-snags/">Channel Snags</a>
					</li>
					<li>
						<a href="snags-site/">Site Snags</a>
					</li>
					<xsl:if
						test="/source/hhdc-contract/@has-stark-automatic-hh-data-importer='true'">
						<li>
							<a
								href="stark-automatic-hh-data-importer/">
								Stark Automatic HH Data Importer
							</a>
						</li>
					</xsl:if>
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>