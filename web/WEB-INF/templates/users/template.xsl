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
				<title>Chellow &gt; Users</title>
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/reports/1/output/">
						<xsl:value-of select="'Chellow'" />
					</a>
					<xsl:value-of select="' &gt; Users'" />
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
				<table>
					<thead>
						<tr>
							<th>Chellow Id</th>
							<th>Email Address</th>
							<th>Role</th>
							<th>Party</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each select="/source/users/user">
							<tr>
								<td>
									<a href="{/source/request/@context-path}/users/{@id}/">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<xsl:value-of select="@email-address" />
								</td>
								<td>
									<a
										href="{/source/request/@context-path}/user-roles/{user-role/@id}/">
										<xsl:value-of select="user-role/@code" />
									</a>
								</td>
								<td>
									<xsl:value-of select="concat(dno/@name, provider/@name)" />
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
				<br />
				<form method="post" action=".">
					<fieldset>
						<legend>Add new user</legend>
						<br />
						<label>
							Email Address
							<input name="email-address"
								value="{/source/request/parameter[@name='email-address']/value/text()}" />
						</label>
						<br />
						<label>
							Password
							<input type="password" name="password" />
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
											<xsl:attribute name="checked" />
										</xsl:otherwise>
									</xsl:choose>
								</input>
								Editor
							</label>
							<br />
							<label>
								<input type="radio" name="user-role-id" value="3">
									<xsl:if
										test="/source/request/parameter[@name='user-role-id']/value/text() = '3'">
										<xsl:attribute name="checked" />
									</xsl:if>
								</input>
								Viewer
							</label>
							<br />
							<label>
								<input type="radio" name="user-role-id" value="2">
									<xsl:if
										test="/source/request/parameter[@name='user-role-id']/value/text() = '2'">
										<xsl:attribute name="checked" />
									</xsl:if>
								</input>
								Party Viewer
							</label>
							<select name="party-id">
								<xsl:for-each select="/source/provider">
									<option value="{@id}">
										<xsl:if
											test="/source/request/parameter[@name='user-role-id']/value/text() = @id">
											<xsl:attribute name="selected" />
										</xsl:if>
										<xsl:value-of
											select="concat(@name, ' ', participant/@code, ' ', market-role/@description)" />
									</option>
								</xsl:for-each>
							</select>
						</fieldset>
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