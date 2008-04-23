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
						select="/source/contract-mop/mop/org/@name" />
					&gt; MOPs &gt;
					<xsl:value-of select="/source/contract-mop/mop/@name" />
					&gt; Contracts &gt;
					<xsl:value-of select="/source/contract-mop/@name" />
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
						href="{/source/request/@context-path}/orgs/{/source/contract-mop/mop/org/@id}/">
						<xsl:value-of
							select="/source/contract-mop/mop/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/contract-mop/mop/org/@id}/mops/">
						MOPs
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/contract-mop/mop/org/@id}/mops/{/source/contract-mop/mop/@id}">
						<xsl:value-of
							select="/source/contract-mop/mop/@name" />
					</a>
					&gt;
					<a href="..">Contracts</a>
					&gt;
					<xsl:value-of select="/source/contract-mop/@name" />
				</p>
				<br />

				<form action="." method="post">
					<fieldset>
						<legend>Update contract</legend>
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
												select="/source/contract-mop/@name" />
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
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>