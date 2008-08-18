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
					Chellow &gt; DSOs &gt;
					<xsl:value-of
						select="concat(/source/dso-service/dso/@code, ' &gt; Services &gt; ')" />
					<xsl:value-of select="/source/dso-service/@name" />
				</title>
			</head>

			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img
							src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					<xsl:value-of select="' &gt; '" />
					<a href="{/source/request/@context-path}/dsos/">
						<xsl:value-of select="'DSOs'" />
					</a>
					<xsl:value-of select="' &gt; '" />
					<a
						href="{/source/request/@context-path}/dsos/{/source/dso-service/dso/@id}/">
						<xsl:value-of
							select="/source/dso-service/dso/@code" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/dsos/{/source/dso-service/dso/@id}/services/">
						<xsl:value-of select="'Services'" />
					</a>
					&gt;
					<xsl:value-of select="/source/dso-service/@name"/>
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
				<form action="." method="post">
					<fieldset>
						<legend>Update Service</legend>
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
						<legend>Delete this service</legend>
						<input type="hidden" name="view"
							value="confirm-delete" />
						<input type="submit" value="Delete" />
					</fieldset>
				</form>
				<ul>
					<li>
						<a href="rate-scripts/">Rate Scripts</a>
					</li>
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

