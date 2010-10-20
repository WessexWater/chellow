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
					href="{/source/request/@context-path}/reports/19/output/" />
				<title>Chellow &gt; Configuration</title>
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img
							src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					<xsl:value-of select="' &gt; Configuration'" />
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
				<br/>
				<form action="." method="post">
					<fieldset>
						<legend>Update Configuration</legend>
						<br />
						<label>Properties</label>
						<br />
						<textarea name="properties" cols="80"
							rows="50">
							<xsl:choose>
								<xsl:when
									test="/source/request/parameter[@name = 'properties']">
									<xsl:value-of
										select="/source/properties/text()" />
								</xsl:when>
								<xsl:otherwise>
									<xsl:value-of
										select="/source/configuration/properties/text()" />
								</xsl:otherwise>
							</xsl:choose>
						</textarea>
						<h4>Examples</h4>
						<h5>Recognizing Users By IP Address</h5>
						<p>
							The line below means that any request with
							IP 127.0.0.1 will automatically be
							associated with the user
							implicit-user@localhost.
						</p>
						<p>
							<code>
								ip127-0-0-1=implicit-user@localhost
							</code>
						</p>
						<h5>Configuring The ECOES Comparison Report</h5>
						<p>
							<code>
								ecoes.user.name=a_user_name<br/>
								ecoes.password=a_password
							</code>
						</p>
						<br />
						<br />
						<input type="submit" value="Update" />
						<input type="reset" value="Reset" />
					</fieldset>
				</form>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>
