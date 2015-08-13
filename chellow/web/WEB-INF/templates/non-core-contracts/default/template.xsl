<?xml version="1.0" encoding="us-ascii"?>
<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="html" encoding="US-ASCII"
		doctype-public="-//W3C//DTD HTML 4.01//EN" doctype-system="http://www.w3.org/TR/html4/strict.dtd"
		indent="yes" />

	<xsl:template match="/">
		<html>
			<head>
				<link rel="stylesheet" type="text/css"
					href="{/source/request/@context-path}/reports/19/output/" />
				<title>
					Chellow &gt; Non-core Contracts &gt;
					<xsl:value-of select="/source/non-core-contract/@name" />
				</title>
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/reports/1/output/">
						<xsl:value-of select="'Chellow'" />
					</a>
					&gt;
					<a href="{/source/request/@context-path}/non-core-contracts/">
						<xsl:value-of select="'Non-core Contracts'" />
					</a>
					&gt;
					<xsl:value-of select="/source/non-core-contract/@name" />
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
						test="/source/request/@method='get' and /source/request/parameter[@name='view']/value='confirm-delete'">
						<form method="post" action=".">
							<fieldset>
								<legend>
									Are you sure you want to delete this
									contract?
								</legend>
								<input type="submit" name="delete" value="Delete" />
							</fieldset>
						</form>
						<p>
							<a href=".">Cancel</a>
						</p>
					</xsl:when>
					<xsl:otherwise>
						<p>
							Is Core?
							<xsl:value-of select="/source/non-core-contract/@is-core" />
						</p>
						<form action="." method="post">
							<fieldset>
								<legend>Update Contract</legend>
								<br />
								<label>
									Party
									<select name="party_id">
										<xsl:for-each select="/source/party">
											<option value="{@id}">
												<xsl:choose>
													<xsl:when test="/source/request/parameter[@name='party_id']">
														<xsl:if
															test="/source/request/parameter[@name='party_id']/value = @id">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:when>
													<xsl:otherwise>
														<xsl:if test="/source/non-core-contract/party/@id = @id">
															<xsl:attribute name="selected" />
														</xsl:if>
													</xsl:otherwise>
												</xsl:choose>
												<xsl:value-of
													select="concat(participant/@code, ' : ', participant/@name, ' : ', @name)" />
											</option>
										</xsl:for-each>
									</select>
								</label>
								<br />
								<label>
									<xsl:value-of select="'Name '" />
									<input name="name">
										<xsl:attribute name="value">
											<xsl:choose>
												<xsl:when test="/source/request/parameter[@name = 'name']/value">
													<xsl:value-of
											select="/source/request/parameter[@name = 'name']/value" />
												</xsl:when>
												<xsl:otherwise>
													<xsl:value-of select="/source/non-core-contract/@name" />
												</xsl:otherwise>
											</xsl:choose>
										</xsl:attribute>
									</input>
								</label>
								<br />
								<br />
								Charge script
								<br />
								<textarea name="charge-script" rows="40" cols="80">
									<xsl:choose>
										<xsl:when test="/source/request/parameter[@name='charge-script']">
											<xsl:value-of
												select="translate(/source/request/parameter[@name='charge-script']/value, '&#xD;','')" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of select="/source/non-core-contract/@charge-script" />
										</xsl:otherwise>
									</xsl:choose>
								</textarea>
								<br />
								<br />
								<input type="submit" value="Update" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
						<br />
						<form action=".">
							<fieldset>
								<legend>Delete this contract</legend>
								<input type="hidden" name="view" value="confirm-delete" />
								<input type="submit" value="Delete" />
							</fieldset>
						</form>
						<ul>
							<li>
								<a href="rate-scripts/">Rate Scripts</a>
							</li>
						</ul>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>