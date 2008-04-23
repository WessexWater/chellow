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
					<xsl:value-of select="/source/suppliers/org/@name" />
					&gt; Suppliers
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
					<a href="{/source/request/@context-path}/orgs/">
						<xsl:value-of select="'Organizations'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/suppliers/org/@id}/">
						<xsl:value-of
							select="/source/suppliers/org/@name" />
					</a>
					&gt; Suppliers
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
				<xsl:when test="/source/response/@status-code = '201'">
					<p>
						The
						<a
							href="{/source/response/header[@name = 'Location']/@value}">
							<xsl:value-of select="'new supplier'"/>
						</a>
						has been successfully created.
					</p>
				</xsl:when>
				<xsl:otherwise>
				<br />

				<ul>
					<xsl:for-each select="/source/suppliers/supplier">
						<li>
							<a href="{@id}">
								<xsl:value-of select="@name" />
							</a>
						</li>
					</xsl:for-each>
				</ul>
				<br />
				<hr />
				<form action="." method="post">
					<fieldset>
						<legend>Add a supplier</legend>

						<label>
							Name
							<xsl:value-of select="' '" />
							<input name="name" />
						</label>
						<br />
						<br />
						<input type="submit" value="Add supplier" />
						<input type="reset" value="Reset" />
					</fieldset>
				</form>
				</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>