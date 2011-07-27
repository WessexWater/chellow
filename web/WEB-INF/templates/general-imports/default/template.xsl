<?xml version="1.0" encoding="iso-8859-1"?>
<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="html" encoding="US-ASCII"
		doctype-public="-//W3C//DTD HTML 4.01//EN" doctype-system="http://www.w3.org/TR/html4/strict.dtd"
		indent="yes" />

	<xsl:template match="/">
		<html>
			<head>
				<title>
					Chellow
					&gt; General Imports &gt;
					<xsl:value-of select="/source/general-import/@id" />
				</title>

				<link rel="stylesheet" type="text/css"
					href="{/source/request/@context-path}/reports/19/output/" />
			</head>
			<body>
				<p>
					<a href="{/source/request/@context-path}/reports/1/output/">
						<xsl:value-of select="'Chellow'" />
					</a>
					&gt;
					<a href="{/source/request/@context-path}/general-imports/">
						<xsl:value-of select="'General Imports'" />
					</a>
					&gt;
					<xsl:value-of select="/source/general-import/@id" />
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
				<xsl:if test="/source/csvLine">
					<table id="import_table">
						<caption>Failed line</caption>
						<tbody>
							<xsl:for-each select="/source/csvLine">
								<tr>
									<th>Action</th>
									<th>Type</th>
									<xsl:for-each select="Field[position() &gt; 2]">
										<th>
											<xsl:value-of select="@name" />
										</th>
									</xsl:for-each>
								</tr>
								<tr>
									<xsl:for-each select="Field">
										<td>
											<xsl:value-of select="text()" />
										</td>
									</xsl:for-each>
								</tr>
							</xsl:for-each>
						</tbody>
					</table>
				</xsl:if>

				<xsl:if test="/source/@line-number">
					<p>
						Stopped at line number
						<xsl:value-of select="concat(/source/@line-number, '.')" />
					</p>
				</xsl:if>

				<xsl:if test="/source/general-import/@progress">
					<p>
						<xsl:value-of select="/source/general-import/@progress" />
					</p>
					<p>Refresh the page to see latest progress.</p>

					<form method="post" action=".">

						<input type="submit" value="Cancel Import" />
					</form>
				</xsl:if>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>