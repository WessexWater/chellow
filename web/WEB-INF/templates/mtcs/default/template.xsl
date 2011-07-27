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
					Chellow &gt; Meter Timeswitches &gt;
					<xsl:value-of select="/source/mtc/@code" />
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
					<a href="{/source/request/@context-path}/mtcs/">
						<xsl:value-of select="'MTCs'" />
					</a>
					<xsl:value-of
						select="concat(' &gt; ', /source/mtc/@code)" />
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
					<tr>
						<th>Chellow Id</th>
						<td>
							<xsl:value-of select="/source/mtc/@id" />
						</td>
					</tr>
					<tr>
						<th>Code</th>
						<td>
							<xsl:value-of select="/source/mtc/@code" />
						</td>
					</tr>
					<tr>
						<th>Dno</th>
						<td>
							<xsl:choose>
								<xsl:when test="/source/mtc/provider">
									<a
										href="{/source/request/@context-path}/providers/{/source/mtc/provider/@id}/">
										<xsl:value-of
											select="/source/mtc/provider/@dno-code" />
									</a>
								</xsl:when>
								<xsl:otherwise>All</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
					<tr>
						<th>Description</th>
						<td>
							<xsl:value-of
								select="/source/mtc/@description" />
						</td>
					</tr>
					<tr>
						<th>Has Related Metering?</th>
						<td>
							<xsl:choose>
								<xsl:when
									test="/source/mtc/@has-related-metering = 'true'">
									Yes
								</xsl:when>
								<xsl:otherwise>No</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
					<tr>
						<th>Has Comms?</th>
						<td>
							<xsl:choose>
								<xsl:when
									test="/source/mtc/@has-comms">
									<xsl:choose>
										<xsl:when
											test="/source/mtc/@has-comms='true'">
											Yes
										</xsl:when>
										<xsl:otherwise>
											No
										</xsl:otherwise>
									</xsl:choose>
								</xsl:when>
								<xsl:otherwise>Unknown</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
					<tr>
						<th>HH / NHH</th>
						<td>
							<xsl:choose>
								<xsl:when test="/source/mtc/@is-hh">
									<xsl:choose>
										<xsl:when
											test="/source/mtc/@is-hh='true'">
											HH
										</xsl:when>
										<xsl:otherwise>
											NHH
										</xsl:otherwise>
									</xsl:choose>
								</xsl:when>
								<xsl:otherwise>Unknown</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
					<tr>
						<th>Meter Type</th>
						<td>
							<a
								href="{/source/request/@context-path}/meter-types/{/source/mtc/meter-type/@id}/">
								<xsl:value-of
									select="/source/mtc/meter-type/@description" />
							</a>
						</td>
					</tr>
					<tr>
						<th>Payment Type</th>
						<td>
							<a
								href="{/source/request/@context-path}/meter-payment-types/{/source/mtc/meter-payment-type/@id}/">
								<xsl:value-of
									select="/source/mtc/meter-payment-type/@description" />
							</a>
						</td>
					</tr>
					<tr>
						<th>TPR Count</th>
						<td>
							<xsl:choose>
								<xsl:when
									test="/source/mtc/@tpr-count">
									<xsl:value-of
										select="/source/mtc/@tpr-count" />
								</xsl:when>
								<xsl:otherwise>N / A</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
					<tr>
						<th>Valid From</th>
						<td>
							<xsl:value-of
								select="concat(/source/mtc/date[@label='from']/@year, '-', /source/mtc/date[@label='from']/@month, '-', /source/mtc/date[@label='from']/@day, ' ', /source/mtc/date[@label='from']/@hour, ':', /source/mtc/date[@label='from']/@minute, ' Z')" />
						</td>
					</tr>
					<tr>
						<th>Valid To</th>
						<td>
							<xsl:choose>
								<xsl:when
									test="/source/mtc/date[@label='to']">
									<xsl:value-of
										select="concat(/source/mtc/date[@label='to']/@year, '-', /source/mtc/date[@label='to']/@month, '-', /source/mtc/date[@label='to']/@day, ' ', /source/mtc/date[@label='to']/@hour, ':', /source/mtc/date[@label='to']/@minute, ' Z')" />
								</xsl:when>
								<xsl:otherwise>Ongoing</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>