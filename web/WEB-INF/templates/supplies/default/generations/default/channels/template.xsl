<?xml version="1.0" encoding="us-ascii"?>
<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="html" encoding="US-ASCII"
		doctype-public="-//W3C//DTD HTML 4.01//EN" doctype-system="http://www.w3.org/TR/html4/strict.dtd"
		indent="yes" />
	<xsl:template match="/">
		<html>
			<head>
				<link rel="stylesheet" type="text/css"
					href="{/source/request/@context-path}/reports/19/output/" />
				<title>
					Chellow &gt; Supplies &gt;
					<xsl:value-of select="/source/channels/supply-generation/supply/@id" />
					&gt; Generations &gt;
					<xsl:value-of select="/source/channels/supply-generation/@id" />
					&gt; Channels
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
					<a href="{/source/request/@context-path}/reports/1/output/">
						<xsl:value-of select="'Chellow'" />
					</a>
					&gt;
					<a href="{/source/request/@context-path}/reports/99/output/">
						<xsl:value-of select="'Supplies'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/reports/7/output/?supply-id={/source/channels/supply-generation/supply/@id}">
						<xsl:value-of select="/source/channels/supply-generation/supply/@id" />
					</a>
					&gt;
					<xsl:value-of
						select="concat('Generation ', /source/channels/supply-generation/@id, ' channels')" />
				</p>
				<br />
				<table>
					<thead>
						<tr>
							<th>Chellow Id</th>
							<th colspan="2">Type</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each select="/source/channels/channel">
							<tr>
								<td>
									<a href="{@id}/">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<xsl:choose>
										<xsl:when test="@is-import='true'">
											import
										</xsl:when>
										<xsl:otherwise>
											export
										</xsl:otherwise>
									</xsl:choose>
								</td>
								<td>
									<xsl:choose>
										<xsl:when test="@is-kwh='true'">
											kWh
										</xsl:when>
										<xsl:otherwise>
											kVArh
										</xsl:otherwise>
									</xsl:choose>
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
				<br />
				<form method="post" action=".">
					<fieldset>
						<legend>
							Add New Channel
								</legend>
						<br />
						<select name="is-import">
							<option value="true">
								<xsl:if
									test="/source/request/parameter[@name='is-import']/value = 'true'">
									<xsl:attribute name="selected" />
								</xsl:if>
								<xsl:value-of select="'Import'" />
							</option>
							<option value="false">
								<xsl:if
									test="/source/request/parameter[@name='is-import']/value = 'false'">
									<xsl:attribute name="selected" />
								</xsl:if>
								<xsl:value-of select="'Export'" />
							</option>
						</select>
						<xsl:value-of select="' '" />
						<select name="is-kwh">
							<option value="true">
								<xsl:if
									test="/source/request/parameter[@name='is-kwh']/value = 'true'">
									<xsl:attribute name="selected" />
								</xsl:if>
								<xsl:value-of select="'kWh'" />
							</option>
							<option value="false">
								<xsl:if
									test="/source/request/parameter[@name='is-kwh']/value = 'false'">
									<xsl:attribute name="selected" />
								</xsl:if>
								<xsl:value-of select="'kVArh'" />
							</option>
						</select>
						<xsl:value-of select="' '" />
						<input type="submit" value="Add" />
						<input type="reset" value="Reset" />
					</fieldset>
				</form>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>