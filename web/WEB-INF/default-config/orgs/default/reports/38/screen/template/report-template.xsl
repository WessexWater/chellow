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
					<xsl:value-of select="/source/org/@name" />
					&gt; Suppliers &gt;
					<xsl:value-of
						select="/source/supplier-service/supplier/@name" />
					&gt; Services &gt;
					<xsl:value-of select="/source/supplier-service/@name" />
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
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/35/screen/output/">
						<xsl:value-of select="'Suppliers'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/36/screen/output/?supplier-id={/source/supplier-service/supplier/@id}">
						<xsl:value-of
							select="/source/supplier-service/supplier/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/37/screen/output/?supplier-id={/source/supplier-service/supplier/@id}">
						<xsl:value-of select="'Services'" />
					</a>
					&gt;
					<xsl:value-of select="/source/supplier-service/@name" />
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
									select="/source/supplier-service/@id" />
							</td>
						</tr>
						<tr>
							<td>Name</td>
							<td>
								<xsl:value-of
									select="/source/supplier-service/@name" />
							</td>
						</tr>
						<tr>
							<td>Start Date</td>
							<td>
								<xsl:value-of
									select="concat(/source/supplier-service/rate-script[position()=1]/hh-end-date[@label='start']/@year, '-', /source/supplier-service/rate-script[position()=1]/hh-end-date[@label='start']/@month, '-', /source/supplier-service/rate-script[position()=1]/hh-end-date[@label='start']/@day)" />
							</td>
						</tr>
						<tr>
							<td>Finish Date</td>
							<td>
								<xsl:choose>
									<xsl:when
										test="/source/supplier-service/rate-script[position()=last()]/hh-end-date[@label='finish']">
										<xsl:value-of
											select="concat(/source/supplier-service/rate-script[position()=last()]/hh-end-date[@label='finish']/@year, '-', /source/supplier-service/rate-script[position()=last()]/hh-end-date[@label='finish']/@month, '-', /source/supplier-service/rate-script[position()=last()]/hh-end-date[@label='finish']/@day)" />
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
						select="/source/supplier-service/rate-script/@script" />
				</pre>

				<table><caption>Rate Scripts</caption>
					<thead>
						<tr>
							<th>Id</th>
							<th>From</th>
							<th>To</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each
							select="/source/supplier-service/rate-script">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/39/screen/output/?supplier-rate-script-id={@id}">
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
				
				<ul>
				<li><a href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/44/screen/output/?supplier-service-id={/source/supplier-service/@id}">Batches</a></li>
				<li><a href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/44/screen/output/?supplier-service-id={@id}">Account Snags</a></li>
				<li><a href="{/source/request/@context-path}/orgs/{/source/org/@id}/reports/44/screen/output/?supplier-service-id={@id}"></a>Bill Snags</li>
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>