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
						select="/source/account/organization/@name" />
					&gt; Suppliers &gt;
					<xsl:value-of
						select="/source/account/supplier/@name" />
					&gt; Accounts &gt;
					<xsl:value-of select="/source/account/@reference" />
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
						href="{/source/request/@context-path}/orgs/{/source/account/organization/@id}/">
						<xsl:value-of
							select="/source/account/organization/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/account/organization/@id}/suppliers/">
						<xsl:value-of select="'Suppliers'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/account/organization/@id}/suppliers/{/source/account/supplier/@id}">
						<xsl:value-of
							select="/source/account/supplier/@name" />
					</a>
					&gt;
					<a href="..">
						<xsl:value-of select="'Accounts'" />
					</a>
					&gt;
					<xsl:value-of select="/source/account/@reference" />
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
						test="/source/request/@method='get' and /source/request/parameter[@name='view']='confirm-delete'">
						<form method="post" action=".">
							<fieldset>
								<legend>Delete this account</legend>
								<input type="submit" name="delete"
									value="Delete" />
							</fieldset>
						</form>
					</xsl:when>
					<xsl:otherwise>

						<form action="." method="post">
							<fieldset>
								<legend>Update Account</legend>
								<label>
									<xsl:value-of select="'Reference '" />
									<input name="reference">
										<xsl:attribute name="value">
											<xsl:choose>
												<xsl:when
													test="/source/request/parameter[@name = 'reference']/value">
													<xsl:value-of
														select="/source/request/parameter[@name = 'reference']/value" />
												</xsl:when>
												<xsl:otherwise>
													<xsl:value-of
														select="/source/account/@reference" />
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

						<form action=".">
							<fieldset>
								<input type="hidden" name="view"
									value="confirm-delete" />
								<legend>Delete this account</legend>
								<input type="submit" value="Delete" />
							</fieldset>
						</form>

						<ul>
							<li>
								<a href="bills/">Bills</a>
							</li>
						</ul>

						<h2>MPANs</h2>

						<ul>
							<xsl:for-each
								select="/source/account/mpan">
								<li>
									<xsl:value-of
										select="concat(profile-class/@code, ' ', meter-timeswitch/@code, ' ', line-loss-factor/@code, ' ', mpan-core/@core, ' ')" />
									<a
										href="{/source/request/@context-path}/orgs/{/source/account/organization/@id}/supplies/{supply-generation/supply/@id}/generations/{supply-generation/@id}/">
										Supply Generation
									</a>
								</li>
							</xsl:for-each>
						</ul>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>