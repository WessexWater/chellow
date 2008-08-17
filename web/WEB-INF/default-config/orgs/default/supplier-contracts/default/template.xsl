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
						select="/source/supplier-contract/org/@name" />
					&gt; Supplier Contracts &gt;
					<xsl:value-of
						select="/source/supplier-contract/@name" />
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
						href="{/source/request/@context-path}/orgs/{/source/supplier-contract/org/@id}/">
						<xsl:value-of
							select="/source/supplier-contract/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/supplier-contract/org/@id}/supplier-contracts/">
						Supplier Contracts
					</a>
					&gt;
					<xsl:value-of
						select="concat(/source/supplier-contract/@name, ' [')" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/supplier-contract/org/@id}/reports/38/screen/output/?contract-id={/source/supplier-contract/@id}">
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

				<form action="." method="post">
					<fieldset>
						<legend>Update contract</legend>
						<br />
						<label>
							Supplier
							<select name="provider-id">
								<xsl:for-each
									select="/source/provider">
									<option value="{@id}">
										<xsl:choose>
											<xsl:when
												test="/source/request/parameter[@name='provider-id']">
												<xsl:if
													test="/source/request/parameter[@name='provider-id']/value/text() = @id">
													<xsl:attribute
														name="selected" />
												</xsl:if>
											</xsl:when>
											<xsl:otherwise>
												<xsl:if
													test="/source/supplier-contract/provider/@id = @id">
													<xsl:attribute
														name="selected" />
												</xsl:if>
											</xsl:otherwise>
										</xsl:choose>
										<xsl:value-of
											select="concat(participant/@code, ' : ', @name)" />
									</option>
								</xsl:for-each>
							</select>
						</label>
						<br />
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
												select="/source/supplier-contract/@name" />
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
										select="/source/supplier-contract/@charge-script" />
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
													select="/source/supplier-contract/@bill-id" />
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
				<br />
				<form action=".">
					<fieldset>
						<legend>Delete this contract</legend>
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
						<a href="accounts/">Accounts</a>
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