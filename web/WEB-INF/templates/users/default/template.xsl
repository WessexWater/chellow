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
					Chellow &gt; Users &gt;
					<xsl:value-of select="/source/user/@email-address" />
				</title>
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/reports/1/output/">
						<xsl:value-of select="'Chellow'" />
					</a>
					&gt;
					<a href="{/source/request/@context-path}/users/">
						<xsl:value-of select="'Users'" />
					</a>
					<xsl:value-of select="concat(' &gt; ', /source/user/@email-address)" />
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
									<xsl:value-of select="/source/user/@email-address" />
									'?
								</legend>
								<input type="submit" name="delete" value="Delete" />
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
									<input name="email-address" size="100">
										<xsl:attribute name="value">
											<xsl:choose>
												<xsl:when
											test="/source/request/parameter[@name='email-address']">
													<xsl:value-of
											select="/source/request/parameter[@name='email-address']/value" />
												</xsl:when>
												<xsl:otherwise>
													<xsl:value-of select="/source/user/@email-address" />
												</xsl:otherwise>
											</xsl:choose>
										</xsl:attribute>
									</input>
								</label>
								<br />
								<br />
								<fieldset>
									<legend>Role</legend>
									<label>
										<input type="radio" name="user-role-id" value="1">
											<xsl:choose>
												<xsl:when test="/source/request/parameter[@name='user-role-id']">
													<xsl:if
														test="/source/request/parameter[@name='user-role-id']/value/text() = '1'">
														<xsl:attribute name="checked" />
													</xsl:if>
												</xsl:when>
												<xsl:otherwise>
													<xsl:if test="/source/user/user-role/@id = '1'">
														<xsl:attribute name="checked" />
													</xsl:if>
												</xsl:otherwise>
											</xsl:choose>
										</input>
										Editor
									</label>
									<br />
									<label>
										<input type="radio" name="user-role-id" value="3">
											<xsl:choose>
												<xsl:when test="/source/request/parameter[@name='user-role-id']">
													<xsl:if
														test="/source/request/parameter[@name='user-role-id']/value/text() = '3'">
														<xsl:attribute name="checked" />
													</xsl:if>
												</xsl:when>
												<xsl:otherwise>
													<xsl:if test="/source/user/user-role/@id = '3'">
														<xsl:attribute name="checked" />
													</xsl:if>
												</xsl:otherwise>
											</xsl:choose>
										</input>
										Viewer
									</label>
									<br />
									<label>
										<input type="radio" name="user-role-id" value="2">
											<xsl:choose>
												<xsl:when test="/source/request/parameter[@name='user-role-id']">
													<xsl:if
														test="/source/request/parameter[@name='user-role-id']/value/text() = '2'">
														<xsl:attribute name="checked" />
													</xsl:if>
												</xsl:when>
												<xsl:otherwise>
													<xsl:if test="/source/user/user-role/@id = '2'">
														<xsl:attribute name="checked" />
													</xsl:if>
												</xsl:otherwise>
											</xsl:choose>
										</input>
										Party Viewer
									</label>
									<select name="party-id">
										<xsl:for-each select="/source/provider">
											<option value="{@id}">
												<xsl:choose>
													<xsl:when test="/source/request/parameter[@name='party-id']">
														<xsl:if
															test="/source/request/parameter[@name='party-id']/value/text() = @id">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if test="/source/user/provider/@id = @id">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of
													select="concat(@name, ' ', participant/@code, ' ', market-role/@description)" />
											</option>
										</xsl:for-each>
									</select>
								</fieldset>
								<br />
								<br />
								<input type="submit" value="Update" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
						<br />
						<br />
						<form method="post" action=".">
							<fieldset>
								<legend>Change password</legend>
								<br />
								<label>
									Current password
									<input type="password" name="current-password" />
								</label>
								<br />
								<br />
								<label>
									New password
									<input type="password" name="new-password" />
								</label>
								<br />
								<label>
									Confirm new Password
									<input type="password" name="confirm-new-password" />
								</label>
								<br />
								<br />
								<input type="submit" value="Change" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
						<br />
						<form action=".">
							<fieldset>
								<input type="hidden" name="view" value="confirm-delete" />
								<legend>Delete this user</legend>
								<input type="submit" value="Delete" />
							</fieldset>
						</form>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>