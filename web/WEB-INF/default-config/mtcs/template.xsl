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
				<title>Chellow &gt; MTCs</title>
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
					<xsl:value-of select="' &gt; MTCs'" />
				</p>

				<table>
					<thead>
						<tr>
							<th>Chellow Id</th>
							<th>Code</th>
							<th>Dso</th>
							<th>Description</th>
							<th>Has Related Metering?</th>
							<th>Has Comms?</th>
							<th>HH / NHH</th>
							<th>Meter Type</th>
							<th>Payment Type</th>
							<th>TPR Count</th>
							<th>Valid From</th>
							<th>Valid To</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each select="/source/mtcs/mtc">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/mtcs/{@id}/">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<xsl:value-of select="@code" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when test="dso">
											<a
												href="{/source/request/@context-path}/dsos/{dso/@id}/">
												<xsl:value-of
													select="dso/@code" />
											</a>
										</xsl:when>
										<xsl:otherwise>
											All
										</xsl:otherwise>
									</xsl:choose>
								</td>
								<td>
									<xsl:value-of select="@description" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when
											test="@has-related-metering = 'true'">
											Yes
										</xsl:when>
										<xsl:otherwise>
											No
										</xsl:otherwise>
									</xsl:choose>
								</td>
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
										<xsl:otherwise>
											Unknown
										</xsl:otherwise>
									</xsl:choose>
								</td>
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
										<xsl:otherwise>
											Unknown
										</xsl:otherwise>
									</xsl:choose>
								</td>
								<td>
									<a
										href="{/source/request/@context-path}/meter-types/{meter-type/@id}/">
										<xsl:value-of
											select="meter-type/@description" />
									</a>
								</td>
								<td>
									<a
										href="{/source/request/@context-path}/meter-payment-types/{meter-payment-type/@id}/">
										<xsl:value-of
											select="meter-payment-type/@description" />
									</a>
								</td>
								<td>
									<xsl:choose>
										<xsl:when test="@tpr-count">
											<xsl:value-of
												select="@tpr-count" />
										</xsl:when>
										<xsl:otherwise>
											N / A
										</xsl:otherwise>
									</xsl:choose>
								</td>
								<td>
									<xsl:value-of
										select="concat(date[@label='from']/@year, '-', date[@label='from']/@month, '-', date[@label='from']/@day, ' ', date[@label='from']/@hour, ':', date[@label='from']/@minute, ' Z')" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when
											test="date[@label='to']">
											<xsl:value-of
												select="concat(date[@label='to']/@year, '-', date[@label='to']/@month, '-', date[@label='to']/@day, ' ', date[@label='to']/@hour, ':', date[@label='to']/@minute, ' Z')" />
										</xsl:when>
										<xsl:otherwise>
											Ongoing
										</xsl:otherwise>
									</xsl:choose>
								</td>

							</tr>
						</xsl:for-each>
					</tbody>
				</table>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>