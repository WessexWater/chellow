<?xml version="1.0" encoding="iso-8859-1"?>
<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="html" encoding="US-ASCII"
		doctype-public="-//W3C//DTD HTML 4.01//EN"
		doctype-system="http://www.w3.org/TR/html4/strict.dtd" indent="yes" />

	<xsl:template match="/">
		<html>
			<head>
				<title>
					Chellow &gt; Organizations &gt;
					<xsl:value-of select="/source/site/org/@name" />
					&gt; Sites &gt;
					<xsl:value-of
						select="concat(/source/site/@code, ' ', /source/site/@name)" />
				</title>

				<link rel="stylesheet" type="text/css"
					href="{/source/request/@context-path}/style/" />
			</head>
			<body>
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
						href="{/source/request/@context-path}/orgs/{/source/site/org/@id}/">
						<xsl:value-of select="/source/site/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/site/org/@id}/sites/">
						<xsl:value-of select="'Sites'" />
					</a>
					&gt;
					<xsl:value-of
						select="concat(/source/site/@code, ' ', /source/site/@name, ' [')" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/site/org/@id}/reports/2/screen/output/?site-id={/source/site/@id}">
						<xsl:value-of select="'view'" />
					</a>
					<xsl:value-of select="']'" />
				</p>
				<xsl:if test="/source/message">
					<ul>
						<xsl:for-each select="/source/message">
							<li>
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>
				<xsl:choose>
					<xsl:when
						test="/source/request/@method='get' and /source/request/parameter[@name='view']/value='confirm-delete'">
						<form method="post" action=".">
							<fieldset>
								<legend>
									Are you sure you want to delete this
									site and any associated snags?
								</legend>
								<input type="submit" name="delete"
									value="Delete" />
							</fieldset>
						</form>
						<p>
							<a href=".">Cancel</a>
						</p>
					</xsl:when>
					<xsl:otherwise>
						<br />

						<form action="." method="post">
							<fieldset>
								<legend>Update this site</legend>
								<label>
									Name
									<xsl:value-of select="' '" />
									<input name="name"
										value="{/source/site/@name}" />
								</label>
								<br />
								<label>
									Code
									<xsl:value-of select="' '" />
									<input name="code"
										value="{/source/site/@code}" />
								</label>
								<br />
								<br />
								<input type="submit" value="Update" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>

						<br />
						<form action=".">
							<fieldset>
								<input type="hidden" name="view"
									value="confirm-delete" />
								<legend>Delete this site</legend>
								<input type="submit" value="Delete" />
							</fieldset>
						</form>
						<hr />
						<table>
							<caption>Supply generations</caption>
							<tr>
								<th>Id</th>
								<th>Supply</th>
								<th>Import MPAN core</th>
								<th>Export MPAN core</th>
								<th>From</th>
								<th>To</th>
							</tr>
							<xsl:for-each
								select="/source/site/supply-generation">
								<tr>
									<td>
										<a
											href="{/source/request/@context-path}/orgs/{/source/site/org/@id}/supplies/{supply/@id}/generations/{@id}/">
											<xsl:value-of select="@id" />
										</a>
									</td>
									<td>
										<a
											href="{/source/request/@context-path}/orgs/{/source/site/org/@id}/supplies/{supply/@id}/">
											<xsl:value-of
												select="supply/@id" />
										</a>
									</td>

									<td>
										<xsl:if
											test="mpan[mpan-top/llf/@is-import='true']">
											<xsl:value-of
												select="mpan[mpan-top/llf/@is-import='true']/mpan-core/@core" />
										</xsl:if>
									</td>
									<td>
										<xsl:if
											test="mpan[mpan-top/llf/@is-import='false']">
											<xsl:value-of
												select="mpan[mpan-top/llf/@is-import='false']/mpan-core/@core" />
										</xsl:if>
									</td>
									<td>
										<xsl:value-of
											select="concat(hh-end-date[@label='start']/@year, '-', hh-end-date[@label='start']/@month, '-', hh-end-date[@label='start']/@day, ' ', hh-end-date[@label='start']/@hour, ':', hh-end-date[@label='start']/@minute, 'Z')" />
									</td>
									<td>
										<xsl:choose>
											<xsl:when
												test="hh-end-date[@label='finish']">
												<xsl:value-of
													select="concat(hh-end-date[@label='finish']/@year, '-', hh-end-date[@label='finish']/@month, '-', hh-end-date[@label='finish']/@day, ' ', hh-end-date[@label='finish']/@hour, ':', hh-end-date[@label='finish']/@minute, 'Z')" />
											</xsl:when>
											<xsl:otherwise>
												Ongoing
											</xsl:otherwise>
										</xsl:choose>
									</td>
								</tr>
							</xsl:for-each>
						</table>
						<!-- 
							<br />
							<form method="post"
							action="{/source/Request/@contextPath}/editor/insertSupplySite">
							<fieldset>
							<legend>
							Attach an existing supply to this site
							</legend>
							<label>
							<xsl:value-of select="'MPAN core '" />
							<input name="mpanCore"
							value="{/source/request/parameter[@name='mpanCore']}" />
							</label>
							<input type="submit" value="Attach" />
							</fieldset>
							</form>
						-->
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>