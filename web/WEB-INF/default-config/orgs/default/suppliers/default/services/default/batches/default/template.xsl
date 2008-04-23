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
						select="/source/batch/supplier-service/supplier/org/@name" />
					&gt; Suppliers &gt;
					<xsl:value-of
						select="/source/batch/supplier-service/supplier/@name" />
					&gt; Services &gt;
					<xsl:value-of
						select="/source/batch/supplier-service/@name" />
					&gt; Batches &gt;
					<xsl:value-of select="/source/batch/@code" />
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
						href="{/source/request/@context-path}/orgs/{/source/batch/supplier-service/supplier/org/@id}/">
						<xsl:value-of
							select="/source/batch/supplier-service/supplier/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/batch/supplier-service/supplier/org/@id}/suppliers/">
						<xsl:value-of select="'Suppliers'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/batch/supplier-service/supplier/org/@id}/suppliers/{/source/batch/supplier-service/supplier/@id}">
						<xsl:value-of
							select="/source/batch/supplier-service/supplier/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/batch/supplier-service/supplier/org/@id}/suppliers/{/source/batch/supplier-service/supplier/@id}/services/">
						<xsl:value-of select="'Services'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/batch/supplier-service/supplier/org/@id}/suppliers/{/source/batch/supplier-service/supplier/@id}/services/{/source/batch/supplier-service/@id}/">
						<xsl:value-of
							select="/source/batch/supplier-service/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/batch/supplier-service/supplier/org/@id}/suppliers/{/source/batch/supplier-service/supplier/@id}/services/{/source/batch/supplier-service/@id}/batches/">
						<xsl:value-of select="'Batches'" />
					</a>
					&gt;
					<xsl:value-of select="/source/batch/@reference" />
				</p>
				<br />
				<xsl:choose>
					<xsl:when
						test="/source/request/@method='get' and /source/request/parameter[@name='view']/value='confirm-delete'">
						<form method="post" action=".">
							<fieldset>
								<legend>Delete</legend>
								<p>
									Are you sure you want to delete this
									batch and all its invoices?
								</p>
								<input type="submit" name="delete"
									value="Delete" />
							</fieldset>
						</form>
						<p>
							<a href=".">Cancel</a>
						</p>
					</xsl:when>
					<xsl:otherwise>
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
														select="/source/batch/@reference" />
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

						<form action=".">
							<fieldset>
								<input type="hidden" name="view"
									value="confirm-delete" />
								<legend>Delete this batch</legend>
								<input type="submit" value="Delete" />
							</fieldset>
						</form>
						<ul>
							<li>
								<a href="invoice-imports/">
									Invoice imports
								</a>
							</li>
							<li>
								<a href="invoices/">Invoices</a>
							</li>
						</ul>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>