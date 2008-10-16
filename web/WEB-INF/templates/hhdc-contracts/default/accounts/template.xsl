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
					Chellow &gt; HHDC Contracts &gt;
					<xsl:value-of
						select="/source/accounts/hhdc-contract/@name" />
					&gt; Accounts
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
					<a
						href="{/source/request/@context-path}/hhdc-contracts/">
						<xsl:value-of select="'HHDC Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/hhdc-contracts/{/source/accounts/hhdc-contract/@id}/">
						<xsl:value-of
							select="/source/accounts/hhdc-contract/@name" />
					</a>
					&gt;
					<xsl:value-of select="'Accounts ['" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/accounts/hhdc-contract/org/@id}/reports/1/screen/output/">
						<xsl:value-of select="'view'" />
					</a>
					<xsl:value-of select="']'" />
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
				<br />
				<xsl:choose>
					<xsl:when
						test="/source/response/@status-code = '201'">
						<p>
							The
							<a
								href="{/source/response/header[@name = 'Location']/@value}">
								<xsl:value-of select="'new account'" />
							</a>
							has been successfully created.
						</p>
					</xsl:when>
					<xsl:otherwise>
						<ul>
							<xsl:for-each
								select="/source/accounts/account">
								<li>
									<a href="{@id}/">
										<xsl:value-of
											select="@reference" />
									</a>
								</li>
							</xsl:for-each>
						</ul>
						<br />
						<form action="." method="post">
							<fieldset>
								<legend>Add an account</legend>
								<br />
								<label>
									<xsl:value-of select="'Reference '" />
									<input name="reference"
										value="{/source/request/parameter[@name = 'reference']/value}" />
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