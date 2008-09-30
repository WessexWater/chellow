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
						select="/source/permissions/role/@name" />
					&gt; Permissions
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
					<a href="{/source/request/@context-path}/roles/">
						<xsl:value-of select="'Roles'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/roles/{/source/permissions/role/@id}/">
						<xsl:value-of
							select="/source/permissions/role/@name" />
					</a>
					&gt; Permissions
				</p>
				<xsl:choose>
					<xsl:when
						test="/source/response/@status-code = '201'">
						<p>
							The
							<a
								href="{/source/response/header[@name = 'Location']/@value}">
								<xsl:value-of select="'new permission'" />
							</a>
							has been successfully created.
						</p>
					</xsl:when>
					<xsl:otherwise>
						<table>
							<thead>
								<tr>
									<th>Id</th>
									<th>URL</th>
									<th>Allowed methods</th>
								</tr>
							</thead>
							<tbody>
								<xsl:for-each
									select="/source/permissions/permission">
									<tr>
										<td>
											<a href="{@id}/">
												<xsl:value-of
													select="@id" />
											</a>
										</td>
										<td>
											<a>
												<xsl:if
													test="@is-get-allowed='true'">
													<xsl:attribute
														name="href">
														<xsl:value-of
															select="concat(/source/request/@context-path, @uri-pattern)" />
													</xsl:attribute>
												</xsl:if>
												<xsl:value-of
													select="@uri-pattern" />
											</a>
										</td>
										<td>
											<ul>
												<xsl:if
													test="@is-get-allowed='true'">
													<li>GET</li>
												</xsl:if>
												<xsl:if
													test="@is-post-allowed='true'">
													<li>POST</li>
												</xsl:if>
											</ul>
										</td>
									</tr>
								</xsl:for-each>
							</tbody>
						</table>
						<br/>
						<xsl:if test="//message">
							<ul>
								<xsl:for-each select="//message">
									<li>
										<xsl:value-of
											select="@description" />
									</li>
								</xsl:for-each>
							</ul>
						</xsl:if>
						<form method="post" action=".">
							<fieldset>
								<legend>Add new permission</legend>
								<br />
								<label>
									URL
									<input name="uri-pattern"
										value="{/source/request/parameter[@name='uri-pattern']/value}" />
								</label>
								<br />
								<br />
								<fieldset>
									<legend>Allowed methods</legend>
									<label>
										Get
										<input type="checkbox"
											name="is-get-allowed" value="true" />
									</label>
									<label>
										Post
										<input type="checkbox"
											name="is-post-allowed" value="true" />
									</label>
								</fieldset>
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

