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
						select="/source/account-snag/supplier-service/supplier/organization/@name" />
					&gt; Suppliers &gt;
					<xsl:value-of
						select="/source/account-snag/supplier-service/supplier/@name" />
					&gt; Services &gt;
					<xsl:value-of
						select="/source/account-snag/supplier-service/@name" />
					&gt; Account Snags &gt;
					<xsl:value-of select="/source/account-snag/@id" />
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
						href="{/source/request/@context-path}/orgs/{/source/account-snag/supplier-service/supplier/organization/@id}/">
						<xsl:value-of
							select="/source/account-snag/supplier-service/supplier/organization/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/account-snag/supplier-service/supplier/organization/@id}/suppliers/">
						<xsl:value-of select="'Suppliers'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/account-snag/supplier-service/supplier/organization/@id}/suppliers/{/source/account-snag/supplier-service/supplier/@id}">
						<xsl:value-of
							select="/source/account-snag/supplier-service/supplier/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/account-snag/supplier-service/supplier/organization/@id}/suppliers/{/source/account-snag/supplier-service/supplier/@id}/services/">
						<xsl:value-of select="'Services'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/account-snag/supplier-service/supplier/organization/@id}/suppliers/{/source/account-snag/supplier-service/supplier/@id}/services/{/source/account-snag/supplier-service/@id}/">
						<xsl:value-of
							select="/source/account-snag/supplier-service/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/account-snag/supplier-service/supplier/organization/@id}/suppliers/{/source/account-snag/supplier-service/supplier/@id}/services/{/source/account-snag/supplier-service/@id}/batches/">
						<xsl:value-of select="'Batches'" />
					</a>
					&gt;
					<xsl:value-of
						select="/source/account-snag/@reference" />
				</p>
				<br />

				<ul>
					<li>Id</li>
					<li>
						Account:
						<xsl:value-of select="' '" />
						<a
							href="{/source/request/@context-path}/orgs/{/source/account-snag/supplier-service/supplier/organization/@id}/suppliers/{/source/account-snag/supplier-service/supplier/@id}/accounts/{@id}/">
							<xsl:value-of select="account/@reference" />
						</a>
					</li>
					<li>
						Start Date:
						<xsl:value-of
							select="concat(' ', hh-end-date[@label='start']/@year, '-', hh-end-date[@label='start']/@month, '-', hh-end-date[@label='start']/@day)" />
					</li>
					<li>
						Finish Date:
						<xsl:value-of
							select="concat(' ', hh-end-date[@label='finish']/@year, '-', hh-end-date[@label='finish']/@month, '-', hh-end-date[@label='finish']/@day)" />
					</li>
					<li>
						Date Created:
						<xsl:value-of
							select="concat(' ', date[@label='created']/@year, '-', date[@label='created']/@month, '-', date[@label='created']/@day)" />
					</li>
					<li>
						Date Resolved:
						<xsl:choose>
							<xsl:when
								test="hh-end-date[@label='resolved']">
								<xsl:value-of
									select="concat(hh-end-date[@label='resolved']/@year, '-', hh-end-date[@label='resolved']/@month, '-', hh-end-date[@label='resolved']/@day)" />
							</xsl:when>
							<xsl:otherwise>Unresolved</xsl:otherwise>
						</xsl:choose>
					</li>
					<li>
						Is Ignored?:
						<td>
							<xsl:choose>
								<xsl:when test="@is-ignored = 'true'">
									Yes
								</xsl:when>
								<xsl:otherwise>No</xsl:otherwise>
							</xsl:choose>
						</td>
					</li>
					<li>
						Description:
						<xsl:value-of select="@description" />
					</li>
				</ul>

				<form action="." method="post">
					<fieldset>
						<legend>Update batch</legend>
						<br />
						<label>
							<xsl:value-of select="'Reference '" />
							<input name="reference">
								<xsl:attribute name="value">
									<xsl:choose>
										<xsl:when
											test="/source/request/parameter[@name = 'reference']/value">
											<xsl:value-of
												select="/source/request/parameter[@name = 'reference']/value" />
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of
												select="/source/account-snag/@reference" />
										</xsl:otherwise>
									</xsl:choose>
								</xsl:attribute>
							</input>
						</label>
						<br />
						<br />
						<input type="submit" value="Update" />
						<input type="reset" value="Reset" />
					</fieldset>
				</form>

				<form action="?view=confirm-delete">
					<fieldset>
						<legend>Delete this account snag</legend>
						<input type="submit" value="Delete" />
					</fieldset>
				</form>
				<ul>
					<li>
						<a href="invoice-imports/">Invoice imports</a>
					</li>
					<li>
						<a href="invoices/">Invoices</a>
					</li>
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>