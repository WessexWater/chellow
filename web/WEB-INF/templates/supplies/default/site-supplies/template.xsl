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
					href="{/source/request/@context-path}/reports/19/output/" />

				<title>
					Chellow &gt; Organizations &gt;
					<xsl:value-of select="/source/site-supplies/supply/org/@name" />
					&gt; Supplies &gt;
					<xsl:value-of select="/source/site-supplies/supply/@id" />
					&gt; Site-supplies &gt;
				</title>

			</head>

			<body>
				<xsl:if test="//message">
					<ul>
						<xsl:for-each select="//message">
							<li>
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>

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
						href="{/source/request/@context-path}/orgs/{/source/site-supplies/supply/org/@id}/">
						<xsl:value-of
							select="/source/site-supplies/supply/org/@name" />
					</a>
					&gt;
	<a
						href="{/source/request/@context-path}/orgs/{/source/site-supplies/supply/org/@id}/supplies/">					
					Supplies
					</a>
					&gt;
	<a
						href="{/source/request/@context-path}/orgs/{/source/site-supplies/supply/org/@id}/supplies/{/source/site-supplies/supply/@id}/">					
					<xsl:value-of
							select="/source/site-supplies/supply/@id" />
					</a>
					&gt;
					Site-supplies
				</p>
				<br />

				<table>
					<caption>Site-supplies</caption>
					<thead>
						<tr>
							<th>Code</th>
							<th>Name</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each select="/source/site-supplies/site-supply">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/supply/org/@id}/sites/{site/@id}">
										<xsl:value-of select="site/@code" />
									</a>
								</td>
								<td>
									<xsl:value-of select="site/@name" />
								</td>
								<xsl:if
									test="count(/source/site-supplies/site-supply) &gt; 1">
									<td>

										<form method="delete"
											action="{@id}/">
											<fieldset>
												<legend>
													Detach site
												</legend>
												<input type="submit"
													value="Detach" />
											</fieldset>
										</form>
									</td>
								</xsl:if>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>

				<form method="post" action=".">
					<fieldset>
						<legend>Attach a site</legend>
						<label>
							<xsl:value-of select="'Site code '" />
							<input name="site-code"
								value="{/source/request/parameter[@name='site-code']/value}" />
						</label>
						<input type="submit" value="Attach" />
						<input type="reset" value="Reset" />
					</fieldset>
				</form>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>