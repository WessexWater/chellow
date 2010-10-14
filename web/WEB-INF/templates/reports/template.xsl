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
				<title>Chellow &gt; Reports</title>
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					&gt; Reports
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
				<table>
					<thead>
						<tr>
							<th>Chellow Id</th>
							<th>Is Core?</th>
							<th>Name</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each select="/source/reports/report">
							<tr>
								<td>
									<a href="{@id}/">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<xsl:value-of select="@is-core" />
								</td>
								<td>
									<xsl:value-of select="@name" />
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
				<br />
				<form action="." method="post">
					<fieldset>
						<legend>Add a report</legend>
						<label>
							<xsl:value-of select="'Name '" />
							<input name="name"
								value="{/source/request/parameter[@name = 'name']/value}" />
						</label>
						<label>
							<xsl:value-of select="' Is core? '" />
							<input type="checkbox" name="is-core" value="true">
								<xsl:if test="/source/request/parameter[@name = 'is-core']">
									<xsl:attribute name="checked">
								<xsl:value-of select="'true'" />
									</xsl:attribute>
								</xsl:if>
							</input>
						</label>
						<br />
						<br />
						<input type="submit" value="Add" />
						<input type="reset" value="Reset" />
					</fieldset>
				</form>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>