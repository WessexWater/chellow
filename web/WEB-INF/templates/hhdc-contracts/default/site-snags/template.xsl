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
					Chellow &gt; HHDC Contracts
					<xsl:value-of
						select="/source/site-snags/hhdc-contract/@name" />
					&gt; Site Snags
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
					<a
						href="{/source/request/@context-path}/hhdc-contracts/">
						<xsl:value-of select="'HHDC Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/hhdc-contracts/{/source/site-snags/hhdc-contract/@id}/">
						<xsl:value-of
							select="/source/site-snags/hhdc-contract/@name" />
					</a>
					&gt;
					<xsl:value-of select="'Site Snags ['" />
					<a
						href="{/source/request/@context-path}/orgs/{/source/site-snags/hhdc-contract/org/@id}/reports/19/screen/output/?hhdc-contract-id={/source/site-snags/hhdc-contract/@id}">
						<xsl:value-of select="'view'" />
					</a>
					<xsl:value-of select="']'" />
				</p>
				<br />
				<table>
					<thead>
						<tr>
							<th>Chellow Id</th>
							<th>Site</th>
							<th>Snag Type</th>
							<th>Start</th>
							<th>Finish</th>
						</tr>
					</thead>
					<tbody>
						<xsl:for-each
							select="/source/site-snags/site-snag">
							<tr>
								<td>
									<a href="{@id}/">
										<xsl:value-of select="@id" />
									</a>
								</td>
								<td>
									<a
										href="{/source/request/@context-path}/sites/{site/@id}/">
										<xsl:value-of
											select="concat(site/@code, ' ', site/@name)" />
									</a>
								</td>
								<td>
									<xsl:value-of select="@description" />
								</td>
								<td>
									<xsl:value-of
										select="concat(hh-end-date[@label='start']/@year, '-', hh-end-date[@label='start']/@month, '-', hh-end-date[@label='start']/@day, 'T', hh-end-date[@label='start']/@hour, ':', hh-end-date[@label='start']/@minute, 'Z')" />
								</td>
								<td>
									<xsl:value-of
										select="concat(hh-end-date[@label='finish']/@year, '-', hh-end-date[@label='finish']/@month, '-', hh-end-date[@label='finish']/@day, 'T', hh-end-date[@label='finish']/@hour, ':', hh-end-date[@label='finish']/@minute, 'Z')" />
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
				<br />
				<form method="post" action=".">
					<fieldset>
						<legend>Bulk ignore</legend>
						<p>Ignore all snags before</p>
						<input name="ignore-date-year">
							<xsl:choose>
								<xsl:when
									test="/source/request/parameter[@name='ignore-date-year']">

									<xsl:attribute name="value">
										<xsl:value-of
											select="/source/request/parameter[@name='ignore-date-year']/value/text()" />
									</xsl:attribute>
								</xsl:when>
								<xsl:otherwise>
									<xsl:attribute name="value">
										<xsl:value-of
											select="/source/date/@year" />
									</xsl:attribute>
								</xsl:otherwise>
							</xsl:choose>
						</input>
						-
						<select name="ignore-date-month">
							<xsl:for-each
								select="/source/months/month">
								<option value="{@number}">
									<xsl:choose>
										<xsl:when
											test="/source/request/parameter[@name='ignore-date-month']">

											<xsl:if
												test="/source/request/parameter[@name='ignore-date-month']/value/text() = number(@number)">

												<xsl:attribute
													name="selected" />
											</xsl:if>
										</xsl:when>
										<xsl:otherwise>
											<xsl:if
												test="/source/date/@month = @number">
												<xsl:attribute
													name="selected" />
											</xsl:if>
										</xsl:otherwise>
									</xsl:choose>

									<xsl:value-of select="@number" />
								</option>
							</xsl:for-each>
						</select>
						-
						<select name="ignore-date-day">
							<xsl:for-each select="/source/days/day">
								<option value="{@number}">
									<xsl:choose>
										<xsl:when
											test="/source/request/parameter[@name='ignore-date-day']">

											<xsl:if
												test="/source/request/parameter[@name='ignore-date-day']/value/text() = @number">

												<xsl:attribute
													name="selected" />
											</xsl:if>
										</xsl:when>
										<xsl:otherwise>
											<xsl:if
												test="/source/date/@day = @number">
												<xsl:attribute
													name="selected" />
											</xsl:if>
										</xsl:otherwise>
									</xsl:choose>

									<xsl:value-of select="@number" />
								</option>
							</xsl:for-each>
						</select>
						<xsl:value-of select="' '" />
						<input type="submit" name="ignore"
							value="Ignore" />
						<input type="reset" value="Reset" />
					</fieldset>
				</form>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>