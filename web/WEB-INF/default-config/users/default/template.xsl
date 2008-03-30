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
					Chellow &gt; Users &gt;
					<xsl:value-of select="/source/user/@email-address" />
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
					<a href="{/source/request/@context-path}/users/">
						<xsl:value-of select="'Users'" />
					</a>
					<xsl:value-of
						select="concat(' &gt; ', /source/user/@email-address)" />
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
									user '
									<xsl:value-of
										select="/source/user/@email-address" />
									'?
								</legend>
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
									Email Address
									<input name="email-address">
										<xsl:attribute name="value">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name='email-address']">
													<xsl:value-of
														select="/source/request/parameter[@name='email-address']/value" />
												</xsl:when>
												<xsl:otherwise>
													<xsl:value-of
														select="/source/user/@email-address" />
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
						<form method="post" action=".">
							<fieldset>
								<legend>Change password</legend>
								<br />
								<label>
									Current password
									<input type="password"
										name="current-password" />
								</label>
								<br />
								<br />
								<label>
									New password
									<input type="password"
										name="new-password" />
								</label>
								<br />
								<label>
									Confirm new Password
									<input type="password"
										name="confirm-new-password" />
								</label>
								<br />
								<br />
								<input type="submit" value="Change" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
						<form action=".">
							<fieldset>
								<input type="hidden" name="view"
									value="confirm-delete" />
								<legend>Delete this user</legend>
								<input type="submit" value="Delete" />
							</fieldset>
						</form>
						<hr />
						<h3>Roles</h3>

						<ul>
							<xsl:for-each select="/source/user/role">
								<li>
									<a
										href="{/source/request/@context-path}/roles/{@id}/">
										<xsl:value-of select="@name" />
									</a>
								</li>
							</xsl:for-each>
						</ul>
						<form method="post" action=".">
							<fieldset>
								<legend>Add existing role</legend>
								<br />
								<label>
									Role id
									<input name="role-id"
										value="{/source/request/parameter[@name='role-id']/value}" />
								</label>
								<br />
								<br />
								<input type="submit" value="Add" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>