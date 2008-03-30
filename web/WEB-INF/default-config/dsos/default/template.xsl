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
					<xsl:value-of select="/source/dso/@code" />
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
					<xsl:value-of
						select="concat(' &gt; ', /source/dso/@code)" />
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
					<caption>
						DSO
						<xsl:value-of
							select="concat(/source/dso/@code, ' (',/source/dso/@name, ')')" />
					</caption>
					<thead>
						<tr>
							<th>Profile Class</th>
							<th>Line Loss Factor</th>
							<th>Meter Timeswitch</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each
							select="/source/dso/line-loss-factor">
							<tr>
								<td>
									<xsl:for-each
										select="profile-class">
										<a
											href="{/source/request/@context-path}/profile-classes/{@id}/">
											<xsl:value-of
												select="@code" />
										</a>
										<xsl:if
											test="position() != last()">
											<xsl:value-of select="', '" />
										</xsl:if>
									</xsl:for-each>
								</td>
								<td>
									<xsl:value-of
										select="concat(@code, ' ', @description)" />
								</td>
								<td>
									<xsl:for-each
										select="meter-timeswitch">
										<a
											href="{/source/request/@context-path}/meter-timswitches/{@id}/">
											<xsl:value-of
												select="@code" />
										</a>
										<xsl:if
											test="position() != last()">
											<xsl:value-of select="', '" />
										</xsl:if>
									</xsl:for-each>
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
				<ul>
									<li>
						<a href="llfs/">Line Loss Factors</a>
					</li>
									<li>
						<a href="mpan-tops/">MPAN top lines</a>
					</li>
				
					<li>
						<a href="services/">Services</a>
					</li>
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

