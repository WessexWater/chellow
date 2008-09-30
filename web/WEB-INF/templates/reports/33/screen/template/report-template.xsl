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
					href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/9/stream/output/" />

				<title>
					<xsl:value-of select="/source/org/@name" />
					&gt; DSOs &gt;
					<xsl:value-of
						select="/source/dso-service/dso/@code" />
					&gt; Services &gt;
					<xsl:value-of select="/source/dso-service/@name" />
				</title>
			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/0/screen/output/">
						<xsl:value-of select="/source/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/68/screen/output/">
						<xsl:value-of select="'DSOs'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/69/screen/output/?dso-id={/source/dso-service/dso/@id}">
						<xsl:value-of
							select="/source/dso-service/dso/@code" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/32/screen/output/?dso-id={/source/dso-service/dso/@id}">
						<xsl:value-of select="'Services'" />
					</a>
					&gt;
					<xsl:value-of select="/source/dso-service/@name" />
				</p>
				<br />
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
					<caption>Properties</caption>
					<thead>
						<tr>
							<th>Name</th>
							<th>Value</th>
						</tr>
					</thead>
					<tbody>
						<tr>
							<td>Id</td>
							<td>
								<xsl:value-of
									select="/source/dso-service/@id" />
							</td>
						</tr>
						<tr>
							<td>Name</td>
							<td>
								<xsl:value-of
									select="/source/dso-service/@name" />
							</td>
						</tr>
						<tr>
							<td>Start Date</td>
							<td>
								<xsl:value-of
									select="concat(/source/dso-service/rate-script[position()=1]/hh-end-date[@label='start']/@year, '-', /source/dso-service/rate-script[position()=1]/hh-end-date[@label='start']/@month, '-', /source/dso-service/rate-script[position()=1]/hh-end-date[@label='start']/@day)" />
							</td>
						</tr>
						<tr>
							<td>Finish Date</td>
							<td>
								<xsl:choose>
									<xsl:when
										test="/source/dso-service/rate-script[position()=last()]/hh-end-date[@label='finish']">
										<xsl:value-of
											select="concat(/source/dso-service/rate-script[position()=last()]/hh-end-date[@label='finish']/@year, '-', /source/dso-service/rate-script[position()=last()]/hh-end-date[@label='finish']/@month, '-', /source/dso-service/rate-script[position()=last()]/hh-end-date[@label='finish']/@day)" />
									</xsl:when>
									<xsl:otherwise>
										Ongoing
									</xsl:otherwise>
								</xsl:choose>
							</td>
						</tr>
					</tbody>
				</table>

				<h2>Script</h2>
				<pre>
					<xsl:value-of
						select="/source/dso-service/rate-script/@script" />
				</pre>

				<h2>Rate Scripts</h2>

				<table>
					<thead>
						<tr>
							<th>Id</th>
							<th>From</th>
							<th>To</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each
							select="/source/dso-service/rate-script">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/34/screen/output/?dso-rate-script-id={@id}">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<xsl:value-of
										select="concat(hh-end-date[@label='start']/@year, '-', hh-end-date[@label='start']/@month, '-', hh-end-date[@label='start']/@day)" />
								</td>
								<td>
									<xsl:choose>
										<xsl:when
											test="hh-end-date[@label='finish']">
											<xsl:value-of
												select="concat(hh-end-date[@label='finish']/@year, '-', hh-end-date[@label='finish']/@month, '-', hh-end-date[@label='finish']/@day)" />
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