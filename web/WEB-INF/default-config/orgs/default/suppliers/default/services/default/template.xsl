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
						select="/source/supplier-service/supplier/org/@name" />
					&gt; Suppliers &gt;
					<xsl:value-of
						select="/source/supplier-service/supplier/@name" />
					&gt; Services &gt;
					<xsl:value-of
						select="/source/supplier-service/@name" />
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
						href="{/source/request/@context-path}/orgs/{/source/supplier-service/supplier/org/@id}/">
						<xsl:value-of
							select="/source/supplier-service/supplier/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/supplier-service/supplier/org/@id}/suppliers/">
						<xsl:value-of select="'Suppliers'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/supplier-service/supplier/org/@id}/suppliers/{/source/supplier-service/supplier/@id}">
						<xsl:value-of
							select="/source/supplier-service/supplier/@name" />
					</a>
					&gt;
					<a href="..">Services</a>
					&gt;
					<xsl:value-of
						select="/source/supplier-service/@name" />
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

				<form action="." method="post">
					<fieldset>
						<legend>Update service</legend>
						<br />
						<xsl:value-of select="'Type: Contract'" />
						<br />
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
												select="/source/supplier-service/@name" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
							</input>
						</label>
						<br />
						<br />
						Charge script
						<br />
						<textarea name="charge-script" rows="40"
							cols="80">
							<xsl:choose>
								<xsl:when
									test="/source/request/parameter[@name='charge-script']">
									<xsl:value-of
										select="translate(/source/request/parameter[@name='charge-script']/value, '&#xD;','')" />
								</xsl:when>
								<xsl:otherwise>
									<xsl:value-of
										select="/source/supplier-service/@charge-script" />
								</xsl:otherwise>
							</xsl:choose>
						</textarea>
						<br />
						<br />
						<input type="submit" value="Update" />
						<input type="reset" value="Reset" />
						<br />
						<br />
						<fieldset>
							<legend>Test</legend>
							<label>
								<xsl:value-of select="'Bill id '" />
								<input name="bill-id">
									<xsl:attribute name="value">
										<xsl:choose>
											<xsl:when
												test="/source/request/parameter[@name='bill-id']">
												<xsl:value-of
													select="/source/request/parameter[@name='bill-id']/value" />
											</xsl:when>
											<xsl:otherwise>
												<xsl:value-of
													select="/source/supplier-service/@bill-id" />
											</xsl:otherwise>
										</xsl:choose>
									</xsl:attribute>
								</input>
							</label>
							<xsl:value-of select="' '" />
							<input type="submit" name="test"
								value="Test without saving" />
							<br />
							<xsl:if
								test="/source/request/parameter[@name='test']">
								<xsl:call-template
									name="bill-element-template">
									<xsl:with-param name="billElement"
										select="/source/bill-element" />
								</xsl:call-template>
							</xsl:if>
						</fieldset>
					</fieldset>
				</form>

				<form action=".">
					<fieldset>
						<legend>Delete this service</legend>
						<input type="hidden" name="view"
							value="confirm-delete" />
						<input type="submit" value="Delete" />
					</fieldset>
				</form>
				<ul>
					<li>
						<a href="batches/">Batches</a>
					</li>
					<li>
						<a href="rate-scripts/">Rate Scripts</a>
					</li>
					<li>
						<a href="account-snags/">Account Snags</a>
					</li>
					<li>
						<a href="bill-snags/">Bill Snags</a>
					</li>
				</ul>
			</body>
		</html>
	</xsl:template>
	<xsl:template name="bill-element-template">
		<xsl:param name="billElement" />
		<p>
			<em>
				<xsl:value-of select="$billElement/@name" />
			</em>
			:
			<xsl:value-of select="$billElement/@cost" />
		</p>
		<p>
			<xsl:value-of select="$billElement/@working" />
		</p>
		<xsl:if test="$billElement/bill-element">
			<ul>
				<xsl:for-each select="$billElement/bill-element">
					<li>
						<xsl:call-template name="bill-element-template" />
						<xsl:with-param name="billElement"
							select="bill-element" />
					</li>
				</xsl:for-each>
			</ul>
		</xsl:if>
	</xsl:template>
</xsl:stylesheet>