<?xml version="1.0" encoding="iso-8859-1"?>
<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="html" encoding="US-ASCII"
		doctype-public="-//W3C//DTD HTML 4.01//EN"
		doctype-system="http://www.w3.org/TR/html4/strict.dtd" indent="yes" />

	<xsl:template match="/">
		<html>
			<head>
				<title>
					Chellow &gt; Organizations &gt;
					<xsl:value-of select="/source/supply/org/@name" />
					&gt; Sites &gt;
					<xsl:value-of
						select="concat(/source/supply/@code, ' ', /source/supply/@name)" />
				</title>

				<link rel="stylesheet" type="text/css"
					href="{/source/request/@context-path}/style/" />
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
						href="{/source/request/@context-path}/orgs/{/source/supply/org/@id}/">
						<xsl:value-of select="/source/supply/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/supply/org/@id}/supplies/">
						<xsl:value-of select="'Supplies'" />
					</a>
					&gt;
					<xsl:value-of
						select="concat(/source/supply/@id, ' [')" />
					<a
						href="{/source/request/@context-path}/orgs/1/reports/3/screen/output/?supply-id={/source/supply/@id}">
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
								<legend>Delete</legend>
								<p>
									Are you sure you want to delete this
									supply?
								</p>
								<input type="submit" name="delete"
									value="Delete" />
							</fieldset>
						</form>
						<p>
							<a href=".">Cancel</a>
						</p>
					</xsl:when>
					<xsl:otherwise>
						<form method="post" action=".">
							<fieldset>
								<legend>Update this supply</legend>
								<br />
								<label>
									<xsl:value-of select="'Name '" />
									<input name="name">
										<xsl:attribute name="value">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='name']">
													<xsl:value-of
														select="/source/request/parameter[@name='name']/value" />
												</xsl:when>
												<xsl:otherwise>
													<xsl:value-of
														select="/source/supply/@name" />
												</xsl:otherwise>
											</xsl:choose>
										</xsl:attribute>
									</input>
								</label>
								<br />
								<br />
								<label>
									<xsl:value-of
										select="'Source Code '" />
									<select name="source-id">
										<xsl:for-each
											select="/source/source">
											<option value="{@id}">
												<xsl:choose>
													<xsl:when
														test="/source/request/parameter[@name='source-id']">
														<xsl:if
															test="@id = /source/request/parameter[@name='source-id']/value">
															<xsl:attribute
																name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if
															test="@id = /source/supply/source/@id">
															<xsl:attribute
																name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of
													select="@code" />
											</option>
										</xsl:for-each>
									</select>
								</label>
								<xsl:value-of select="' '" />
								<a
									href="{/source/request/@context-path}/sources/">
									<xsl:value-of select="'Sources'" />
								</a>
								<br />
								<br />
								<input type="submit" value="Update" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
						<br />
						<form action=".">
							<fieldset>
								<legend>Delete this supply</legend>
								<input type="hidden" name="view"
									value="confirm-delete" />
								<input type="submit" value="Delete" />
							</fieldset>
						</form>
						<h4>
							<a href="generations/">Generations</a>
						</h4>
						<h4>
							<a href="channels/">Channels</a>
						</h4>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>