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
					Chellow &gt; Organizations &gt;
					<xsl:value-of
						select="/source/bills/account/supplier/organization/@name" />
					&gt; Suppliers &gt;
					<xsl:value-of
						select="/source/bills/account/supplier/@name" />
					&gt; Accounts &gt;
					<xsl:value-of
						select="/source/bills/account/@reference" />
					&gt; Bills &gt;
				</title>
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
					&gt;
					<a href="{/source/request/@context-path}/orgs/">
						<xsl:value-of select="'Organizations'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bills/account/supplier/organization/@id}/">
						<xsl:value-of
							select="/source/bills/account/supplier/organization/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bills/account/supplier/organization/@id}/suppliers/">
						<xsl:value-of select="'Suppliers'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bills/account/supplier/organization/@id}/suppliers/{/source/bills/account/supplier/@id}/">
						<xsl:value-of
							select="/source/bills/account/supplier/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bills/account/supplier/organization/@id}/suppliers/{/source/bills/account/supplier/@id}/accounts/">
						<xsl:value-of select="'Accounts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/bills/account/supplier/organization/@id}/suppliers/{/source/bills/account/supplier/@id}/">
						<xsl:value-of
							select="/source/bills/account/@reference" />
					</a>
					&gt;
					<xsl:value-of select="'Bills'" />
				</p>
				<br />
				<xsl:choose>
					<xsl:when
						test="/source/response/@status-code = '201'">
						<p>
							The
							<a
								href="{/source/response/header[@name = 'Location']/@value}">
								<xsl:value-of select="'new bill'" />
							</a>
							has been successfully created.
						</p>
					</xsl:when>
					<xsl:otherwise>
						<table>
							<caption>Bills</caption>
							<thead>
								<tr>
									<th>Id</th>
									<th>From</th>
									<th>To</th>
									<th>Net</th>
									<th>VAT</th>
								</tr>
							</thead>
							<tbody>
								<xsl:for-each
									select="/source/bills/bill">
									<tr>
										<td>
											<a href="{@id}/">
												<xsl:value-of
													select="@id" />
											</a>
										</td>
										<td>
											<xsl:value-of
												select="concat(day-start-date/@year, '-', day-start-date/@month, '-', day-start-date/@day)" />
										</td>
										<td>
											<xsl:value-of
												select="concat(day-finish-date/@year, '-', day-finish-date/@month, '-', day-finish-date/@day)" />
										</td>
										<td>
											<xsl:value-of select="@net" />
										</td>
										<td>
											<xsl:value-of select="@vat" />
										</td>
									</tr>
								</xsl:for-each>
							</tbody>
						</table>
						<br />
						<hr />
						<form action="." method="post">
							<fieldset>
								<legend>Add a bill</legend>
								<input type="submit" value="Add" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>