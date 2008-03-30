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
					Chellow &gt; DNOs &gt;
					<xsl:value-of
						select="/source/mpan-top/line-loss-factor/dso/@code" />
					&gt; MPAN Top Lines &gt;
					<xsl:value-of select="/source/mpan-top/@id" />
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
						href="{/source/request/@context-path}/dsos/{/source/mpan-top/line-loss-factor/dso/@id}/">
						<xsl:value-of
							select="/source/mpan-top/line-loss-factor/dso/@code" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/dsos/{/source/mpan-top/line-loss-factor/dso/@id}/mpan-tops/">
						<xsl:value-of select="'MPAN tops'" />
					</a>
					&gt;
					<xsl:value-of select="/source/mpan-top/@id" />
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
					<caption>MPAN top line properties</caption>
					<thead>
						<tr>
							<th>Property</th>
							<th>Value</th>
						</tr>
					</thead>
					<tbody>
						<tr>
							<td>Profile Class</td>
							<td>
								<a
									href="{/source/request/@context-path}/profile-classes/{/source/mpan-top/profile-class/@id}/">
									<xsl:value-of
										select="concat(/source/mpan-top/profile-class/@code, ' - ', /source/mpan-top/profile-class/@description)" />
								</a>
							</td>
						</tr>
						<tr>
							<td>Meter Timeswitch</td>
							<td>
								<a
									href="{/source/request/@context-path}/meter-timeswitches/{/source/mpan-top/meter-timeswitch/@id}/">
									<xsl:value-of
										select="concat(/source/mpan-top/meter-timeswitch/@code, ' - ', /source/mpan-top/meter-timeswitch/@description)" />
								</a>
							</td>
						</tr>
						<tr>
							<td>Line Loss Factor</td>
							<td>
								<a
									href="{/source/request/@context-path}/dsos/{/source/mpan-top/line-loss-factor/dso/@id}/llfs/{/source/mpan-top/line-loss-factor/@id}/">
									<xsl:value-of
										select="concat(/source/mpan-top/line-loss-factor/@code, ' - ', /source/mpan-top/line-loss-factor/@description)" />
								</a>
							</td>
						</tr>
					</tbody>
				</table>

				<h3>SSCs</h3>

				<ul>
					<xsl:for-each select="/source/mpan-top/ssc">
						<li>
							<a
								href="{/source/request/@context-path}/sscs/{@id}/">
								<xsl:value-of select="@code" />
							</a>
						</li>
					</xsl:for-each>
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>