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
					href="{/source/request/@context-path}/orgs/{/source/supplier-contract/org/@id}/reports/9/stream/output/" />

				<title>
					<xsl:value-of
						select="/source/supplier-contract/org/@name" />
					&gt; Supplier Contracts &gt;
					<xsl:value-of
						select="/source/supplier-contract/@name" />
				</title>
			</head>
			<body>
				<p>
					<a
						href="{/source/request/@context-path}/orgs/{/source/supplier-contract/org/@id}/reports/0/screen/output/">
						<xsl:value-of
							select="/source/supplier-contract/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/supplier-contract/org/@id}/reports/37/screen/output/">
						<xsl:value-of select="'Supplier Contracts'" />
					</a>
					&gt;
					<xsl:value-of
						select="concat(/source/supplier-contract/@name, ' [')" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/supplier-contract/org/@id}/supplier-contracts/{/source/supplier-contract/@id}/">
						<xsl:value-of select="'edit'" />
					</a>
					<xsl:value-of select="']'" />
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
					<tbody>
						<tr>
							<th>Chellow Id</th>
							<td>
								<xsl:value-of
									select="/source/supplier-contract/@id" />
							</td>
						</tr>
						<tr>
							<th>Name</th>
							<td>
								<xsl:value-of
									select="/source/supplier-contract/@name" />
							</td>
						</tr>
						<tr>
							<th>Supplier</th>
							<td>
								<a
									href="{/source/request/@context-path}/orgs/{/source/supplier-contract/org/@id}/reports/23/screen/output/?provider-id={/source/supplier-contract/provider/@id}">
									<xsl:value-of
										select="/source/supplier-contract/provider/@name" />
								</a>
							</td>
						</tr>
						<tr>
							<th>Start Date</th>
							<td>
								<xsl:value-of
									select="concat(/source/supplier-contract/rate-script[position()=1]/hh-end-date[@label='start']/@year, '-', /source/supplier-contract/rate-script[position()=1]/hh-end-date[@label='start']/@month, '-', /source/supplier-contract/rate-script[position()=1]/hh-end-date[@label='start']/@day)" />
							</td>
						</tr>
						<tr>
							<th>Finish Date</th>
							<td>
								<xsl:choose>
									<xsl:when
										test="/source/supplier-contract/rate-script[position()=last()]/hh-end-date[@label='finish']">
										<xsl:value-of
											select="concat(/source/supplier-contract/rate-script[position()=last()]/hh-end-date[@label='finish']/@year, '-', /source/supplier-contract/rate-script[position()=last()]/hh-end-date[@label='finish']/@month, '-', /source/supplier-contract/rate-script[position()=last()]/hh-end-date[@label='finish']/@day)" />
									</xsl:when>
									<xsl:otherwise>
										Ongoing
									</xsl:otherwise>
								</xsl:choose>
							</td>
						</tr>
					</tbody>
				</table>
				<br />
				<table>
					<caption>Rate Scripts</caption>
					<thead>
						<tr>
							<th>Chellow Id</th>
							<th>From</th>
							<th>To</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each
							select="/source/supplier-contract/rate-script">
							<tr>
								<td>
									<a
										href="{/source/request/@context-path}/orgs/{/source/supplier-contract/org/@id}/reports/39/screen/output/?rate-script-id={@id}">
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
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/supplier-contract/org/@id}/reports/44/screen/output/?contract-id={/source/supplier-contract/@id}">
							Batches
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/supplier-contract/org/@id}/reports/50/screen/output/?contract-id={/source/supplier-contract/@id}">
							Account Snags
						</a>
					</li>
					<li>
						<a
							href="{/source/request/@context-path}/orgs/{/source/supplier-contract/org/@id}/reports/52/screen/output/?contract-id={/source/supplier-contract/@id}">
							Bill Snags
						</a>
					</li>
				</ul>

				<h2>Script</h2>
				<pre>
					<xsl:value-of
						select="/source/supplier-contract/@charge-script" />
				</pre>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>