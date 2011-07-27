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
					Chellow &gt; DNOs &gt;
					<xsl:value-of
						select="concat(/source/dno-contract/dno/@code, ' &gt; Contracts &gt; ')" />
					<xsl:value-of select="/source/dno-contract/@name" />
				</title>
			</head>

			<body>
				<p>
					<a href="{/source/request/@context-path}/reports/1/output/">
						<xsl:value-of select="'Chellow'" />
					</a>
					&gt;
					<a href="{/source/request/@context-path}/reports/137/output/">
						<xsl:value-of select="'DNOs'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/reports/139/output/?dno-id={/source/dno-contract/dno/@id}">
						<xsl:value-of select="/source/dno-contract/dno/@code" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/reports/67/output/?dno-contract-id={/source/dno-contract/@id}">
						<xsl:value-of select="concat('Contract ', /source/dno-contract/@name)" />
					</a>
					&gt; Edit
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
					<xsl:when
						test="/source/request/@method='get' and /source/request/parameter[@name='view']/value='confirm-delete'">
						<form method="post" action=".">
							<fieldset>
								<legend>Delete</legend>
								<p>
									Are you sure you want to delete this contract and its rate
									scripts?
								</p>
								<input type="submit" name="delete" value="Delete" />
							</fieldset>
						</form>
						<p>
							<a href=".">Cancel</a>
						</p>
					</xsl:when>
					<xsl:otherwise>

						<form action="." method="post">
							<fieldset>
								<legend>Update Contract</legend>
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
											<xsl:value-of select="/source/dno-contract/@name" />
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
											<xsl:value-of select="/source/dno-contract/@charge-script" />
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
								<legend>Delete this Contract</legend>
								<input type="hidden" name="view" value="confirm-delete" />
								<input type="submit" value="Delete" />
							</fieldset>
						</form>
					</xsl:otherwise>
				</xsl:choose>
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
						<xsl:with-param name="billElement" select="bill-element" />
					</li>
				</xsl:for-each>
			</ul>
		</xsl:if>
	</xsl:template>
</xsl:stylesheet>

