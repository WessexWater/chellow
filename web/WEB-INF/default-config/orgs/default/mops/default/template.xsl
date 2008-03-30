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
					<xsl:value-of
						select="/source/mop/organization/@name" />
					&gt; MOPs &gt;
					<xsl:value-of select="/source/mop/@id" />
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
						href="{/source/request/@context-path}/orgs/{/source/mop/organization/@id}/">
						<xsl:value-of
							select="/source/mop/organization/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/mop/organization/@id}/mops/">
						<xsl:value-of select="'MOPs'" />
					</a>
					&gt;
					<xsl:value-of select="/source/mop/@name" />
				</p>
				<xsl:if test="/source/message">
					<ul>
						<xsl:for-each select="/source/message">
							<li>
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>

				<br />
				<xsl:choose>
					<xsl:when
						test="/source/request/@method='get' and /source/request/parameter[@name='view']='confirm-delete'">
						<form method="post" action=".">
							<fieldset>
								<legend>Delete this MOP</legend>
								<input type="submit" name="delete"
									value="Delete" />
							</fieldset>
						</form>
					</xsl:when>
					<xsl:otherwise>
						<form action="." method="post">
							<fieldset>
								<legend>Update this MOP</legend>
								<label>
									Name
									<xsl:value-of select="' '" />
									<input name="name"
										value="{/source/mop/@name}" />
								</label>
								<br />
								<br />
								<input type="submit" value="Update" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>

						<br />
						<form action="?view=confirm-delete">
							<fieldset>
								<legend>Delete this MOP</legend>
								<input type="submit" value="Delete" />
							</fieldset>
						</form>

						<hr />
						<p>
							<a href="contracts/">Contracts</a>
						</p>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>