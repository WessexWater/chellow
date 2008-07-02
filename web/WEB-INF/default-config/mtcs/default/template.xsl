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
							<xsl:value-of select="@id" />
						</td>
					</tr>
					<tr>
						<th>Code</th>
						<td>
							<xsl:value-of select="@code" />
						</td>
					</tr>
					<tr>
						<th>Dso</th>
						<td>
							<xsl:choose>
								<xsl:when test="dso">
									<a
										href="{/source/request/@context-path}/dsos/{@id}/">
										<xsl:value-of
											select="dso/@code" />
									</a>
								</xsl:when>
								<xsl:otherwise>All</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
					<tr>
						<th>Description</th>
						<td>
							<xsl:value-of select="@description" />
						</td>
					</tr>
					<tr>
						<th>Has Related Metering?</th>
						<td>
							<xsl:choose>
								<xsl:when
									test="@has-related-metering = 'true'">
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
								<xsl:when test="@has-comms">
									<xsl:choose>
										<xsl:when
											test="@has-comms='true'">
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
								<xsl:when test="@is-hh">
									<xsl:choose>
										<xsl:when
											test="@is-hh='true'">
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
								href="{/source/request/@context-path}/meter-types/{meter-type/@id}/">
								<xsl:value-of
									select="meter-type/@description" />
							</a>
						</td>
					</tr>
					<tr>
						<th>Payment Type</th>
						<td>
							<a
								href="{/source/request/@context-path}/meter-payment-types/{meter-payment-type/@id}/">
								<xsl:value-of
									select="meter-payment-type/@description" />
							</a>
						</td>
					</tr>
					<tr>
						<th>TPR Count</th>
						<td>
							<xsl:choose>
								<xsl:when test="@tpr-count">
									<xsl:value-of select="@tpr-count" />
								</xsl:when>
								<xsl:otherwise>N / A</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
					<tr>
						<th>Valid From</th>
						<td>
							<xsl:value-of
								select="concat(date[@label='from']/@year, '-', date[@label='from']/@month, '-', date[@label='from']/@day, ' ', date[@label='from']/@hour, ':', date[@label='from']/@minute, ' Z')" />
						</td>
					</tr>
					<tr>
						<th>Valid To</th>
						<td>
							<xsl:choose>
								<xsl:when test="date[@label='to']">
									<xsl:value-of
										select="concat(date[@label='to']/@year, '-', date[@label='to']/@month, '-', date[@label='to']/@day, ' ', date[@label='to']/@hour, ':', date[@label='to']/@minute, ' Z')" />
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

