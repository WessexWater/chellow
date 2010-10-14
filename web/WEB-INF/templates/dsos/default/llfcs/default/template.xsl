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
					Chellow &gt; DSOs &gt;
					<xsl:value-of select="/source/llfc/dso/@code" />
					&gt; Line Loss Factor Classes &gt;
					<xsl:value-of select="/source/llfc/@code" />
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
					<a href="{/source/request/@context-path}/dsos/">
						<xsl:value-of select="'DSOs'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/dsos/{/source/llfc/dso/@id}/">
						<xsl:value-of select="/source/llfc/dso/@code" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/dsos/{/source/llfc/dso/@id}/llfcs/">
						<xsl:value-of select="'LLFCs'" />
					</a>
					&gt;
					<xsl:value-of select="/source/llfc/@code" />
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
				<table>
					<tbody>
						<tr>
							<th>Chellow Id</th>
							<td>
								<xsl:value-of select="/source/llfc/@id" />
							</td>
						</tr>
						<tr>
							<th>Code</th>
							<td>
								<xsl:value-of
									select="/source/llfc/@code" />
							</td>
						</tr>
						<tr>
							<th>Description</th>
							<td>
								<xsl:value-of
									select="/source/llfc/@description" />
							</td>
						</tr>
						<tr>
							<th>Voltage Level</th>
							<td>
								<xsl:value-of
									select="concat(/source/llfc/voltage-level/@code, ' - ', /source/llfc/voltage-level/@name)" />
							</td>
						</tr>
						<tr>
							<th>Is substation?</th>
							<td>
								<xsl:value-of
									select="/source/llfc/@is-substation" />
							</td>
						</tr>
						<tr>
							<th>Is import?</th>
							<td>
								<xsl:value-of
									select="/source/llfc/@is-import" />
							</td>
						</tr>
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>