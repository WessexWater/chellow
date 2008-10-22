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
					Chellow &gt; Reports &gt;
					<xsl:value-of select="/source/report/@name" />
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
						href="{/source/request/@context-path}/reports/">
						<xsl:value-of select="'Reports'" />
					</a>
					&gt;
					<xsl:value-of select="/source/report/@name" />
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
								<legend>
									Are you sure you want to delete this
									report?
								</legend>
								<input type="submit" name="delete"
									value="Delete" />
							</fieldset>
						</form>
						<p>
							<a href=".">Cancel</a>
						</p>
					</xsl:when>
					<xsl:otherwise>
						<ul>
							<li>
								<a href="output/">Output</a>
							</li>
							<li>
								<a href="xml-output/">XML Output</a>
							</li>
						</ul>
						<form method="post" action=".">
							<fieldset>
								<legend>Update Report</legend>
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
														select="/source/report/@name" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
									</input>
								</label>
								<br />
								<br />
								<label>Script</label>
								<br />
								<textarea name="script" cols="80"
									rows="50">
									<xsl:choose>
										<xsl:when
											test="/source/request/parameter[@name = 'script']/value">
											<xsl:value-of
												select="/source/script/text()" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
												select="/source/report/script/text()" />
										</xsl:otherwise>
									</xsl:choose>
								</textarea>
								<br />
								<br />
								<label>Template</label>
								<br />
								<textarea name="template" cols="80"
									rows="50">
									<xsl:choose>
										<xsl:when
											test="/source/request/parameter[@name = 'template']/value">
											<xsl:value-of
												select="/source/template/text()" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
												select="/source/report/template/text()" />
										</xsl:otherwise>
									</xsl:choose>
								</textarea>
								<br />
								<input type="submit" value="Save" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
						<br />
						<br />
						<form action=".">
							<fieldset>
								<legend>Delete this report</legend>
								<input type="hidden" name="view"
									value="confirm-delete" />
								<input type="submit" value="Delete" />
							</fieldset>
						</form>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>