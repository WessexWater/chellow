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
					Chellow &gt; Roles &gt;
					<xsl:value-of
						select="/source/permission/role/@name" />
					&gt; Permissions &gt;
					<xsl:value-of
						select="/source/permission/@uri-pattern" />
				</title>
			</head>

			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img src="{/source/request/@context-path}/logo/"
							alt="Chellow Logo" />
						<span class="logo">Chellow</span>
					</a>
					<xsl:value-of select="' &gt; '" />
					<a href="{/source/request/@context-path}/roles/">
						Roles
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/roles/{/source/permission/role/@id}/">
						<xsl:value-of
							select="/source/permission/role/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/roles/{/source/permission/role/@id}/permissions/">
						<xsl:value-of select="'Permissions'" />
					</a>
					&gt;
					<xsl:value-of
						select="/source/permission/@uri-pattern" />
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
						test="/source/request/parameter[@name='view']/value='confirm-delete'">
						<form method="post" action=".">
							<fieldset>
								<legend>
									Do you really want to delete the
									permission '
									<xsl:value-of
										select="/source/permission/@uri-pattern" />
									'?
								</legend>
								<br/>
								<input type="submit" name="delete"
									value="Delete" />
								<p>
									<a href=".">Cancel</a>
								</p>
							</fieldset>
						</form>
					</xsl:when>
					<xsl:otherwise>
						<form method="post" action=".">
							<fieldset>
								<legend>Update details</legend>
								<br />
								<label>
									URL
									<input name="uri-pattern">
										<xsl:attribute name="value">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='uri-pattern']">
													<xsl:value-of
														select="/source/request/parameter[@name='uri-pattern']/value" />
												</xsl:when>
												<xsl:otherwise>
													<xsl:value-of
														select="/source/permission/@uri-pattern" />
												</xsl:otherwise>
											</xsl:choose>
										</xsl:attribute>
									</input>
								</label>
								<fieldset>
									<legend>Allowed methods</legend>
									<label>
										Get
										<input type="checkbox"
											name="is-get-allowed" value="true">
											<xsl:choose>
												<xsl:when
													test="/source/request/@method='post'">
													<xsl:if
														test="/source/request/parameter[@name='is-get-allowed']">
														<xsl:attribute
															name="checked">
															checked
														</xsl:attribute>
													</xsl:if>
												</xsl:when>
												<xsl:otherwise>
													<xsl:if
														test="/source/permission/@is-get-allowed='true'">
														<xsl:attribute
															name="checked">
															checked
														</xsl:attribute>
													</xsl:if>
												</xsl:otherwise>
											</xsl:choose>
										</input>
									</label>
									<label>
										Post
										<input type="checkbox"
											name="is-post-allowed" value="true">
											<xsl:choose>
												<xsl:when
													test="/source/request/@method='post'">
													<xsl:if
														test="/source/request/parameter[@name='is-post-allowed']">
														<xsl:attribute
															name="checked">
															checked
														</xsl:attribute>
													</xsl:if>
												</xsl:when>
												<xsl:otherwise>
													<xsl:if
														test="/source/permission/@is-post-allowed='true'">
														<xsl:attribute
															name="checked">
															checked
														</xsl:attribute>
													</xsl:if>
												</xsl:otherwise>
											</xsl:choose>
										</input>
									</label>
								</fieldset>
								<br />
								<br />
								<input type="submit" value="Update" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
						<form action=".">
							<fieldset>
								<input type="hidden" name="view"
									value="confirm-delete" />
								<legend>Delete this permission</legend>
								<input type="submit" value="Delete" />
							</fieldset>
						</form>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

