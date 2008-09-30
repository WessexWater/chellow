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
				<title>Chellow &gt; Users</title>
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img
							src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
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
				<xsl:choose>
					<xsl:when
						test="/source/response/@status-code = '201'">
						<p>
							The
							<a
								href="{/source/response/header[@name = 'Location']/@value}">
								<xsl:value-of select="'new user'" />
							</a>
							has been successfully created.
						</p>
					</xsl:when>
					<xsl:otherwise>
						<table>
							<thead>
								<tr>
									<th>Chellow Id</th>
									<th>Email Address</th>
								</tr>
							</thead>
							<tbody>
								<xsl:for-each
									select="/source/users/user">
									<tr>
										<td>
											<a
												href="{/source/request/@context-path}/users/{@id}/">
												<xsl:value-of
													select="@id" />
											</a>
										</td>
										<td>
											<xsl:value-of
												select="@email-address" />
										</td>
									</tr>
								</xsl:for-each>
							</tbody>
						</table>
						<br/>
						<form method="post" action="..">
							<fieldset>
								<legend>Add new user</legend>
								<br />
								<label>
									Email Address
									<input name="email-address" />
								</label>
								<br />
								<label>
									Password
									<input type="password"
										name="password" />
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