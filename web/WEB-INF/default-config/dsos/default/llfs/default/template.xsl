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
					href="{/source/request/@context-path}/orgs/1/reports/9/stream/output/" />
				<title>
					Chellow &gt; DNOs &gt;
					<xsl:value-of
						select="/source/line-loss-factor/dso/@code" />
					&gt; Line Loss Factors &gt;
					<xsl:value-of
						select="/source/line-loss-factor/@code" />
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
						href="{/source/request/@context-path}/dsos/{/source/line-loss-factor/dso/@id}/">
						<xsl:value-of
							select="/source/line-loss-factor/dso/@code" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/dsos/{/source/line-loss-factor/dso/@id}/llfs/">
						<xsl:value-of select="'Line Loss Factors'" />
					</a>
					&gt;
					<xsl:value-of select="/source/line-loss-factor/@code" />
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
					<caption>Properties</caption>
					<thead>
						<tr>
							<th>Name</th>
							<th>Value</th>
						</tr>
					</thead>
					<tbody>
						<tr>
							<td>Code</td>
							<td>
								<xsl:value-of
									select="/source/line-loss-factor/@code" />
							</td>
						</tr>
						<tr>
							<td>Description</td>
							<td>
								<xsl:value-of
									select="/source/line-loss-factor/@description" />
							</td>
						</tr>
						<tr>
							<td>Voltage Level</td>
							<td>
								<xsl:value-of
									select="concat(/source/line-loss-factor/voltage-level/@code, ' - ', /source/line-loss-factor/voltage-level/@name)" />
							</td>
						</tr>
						<tr>
							<td>Is substation?</td>
							<td>
								<xsl:value-of
									select="/source/line-loss-factor/@is-substation" />
							</td>
						</tr>
						<tr>
							<td>Is import?</td>
							<td>
								<xsl:value-of
									select="/source/line-loss-factor/@is-import" />
							</td>
						</tr>
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>