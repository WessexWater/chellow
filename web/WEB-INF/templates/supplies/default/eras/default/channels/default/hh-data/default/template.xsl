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
					<xsl:value-of
						select="/source/hh-datum/channel/era/supply/@id" />
					&gt; Supply Generations &gt;
					<xsl:value-of select="/source/hh-datum/channel/era/@id" />
					&gt; Channels &gt;
					<xsl:value-of select="/source/hh-datum/channel/@id" />
					&gt; HH Data &gt;
					<xsl:value-of select="/source/hh-datum/@id" />
				</title>
			</head>
			<body>
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
						href="{/source/request/@context-path}/reports/7/output/?supply-id={/source/hh-datum/channel/era/supply/@id}">
						<xsl:value-of
							select="/source/hh-datum/channel/era/supply/@id" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/hh-datum/channel/era/supply/@id}/eras/{/source/hh-datum/channel/era/@id}/channels/">
						<xsl:value-of
							select="concat('Generation ', /source/hh-datum/channel/era/@id, ' channels')" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/hh-datum/channel/era/supply/@id}/eras/{/source/hh-datum/channel/era/@id}/channels/{/source/hh-datum/channel/@id}/">
						<xsl:value-of select="/source/hh-datum/channel/@id" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/supplies/{/source/hh-datum/channel/era/supply/@id}/eras/{/source/hh-datum/channel/era/@id}/channels/{/source/hh-datum/channel/@id}/hh-data/">
						<xsl:value-of select="'HH Data'" />
					</a>
					&gt;
					<xsl:value-of select="/source/hh-datum/@id" />
				</p>
				<xsl:if test="//message">
					<ul>
						<xsl:for-each select="//message">
							<li>
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>

				<table><caption>Supply Generation</caption>
					<tr>
						<td>Start Date</td>
						<td>
							<xsl:value-of
								select="concat(/source/hh-datum/channel/era/hh-start-date[@label='start']/@year, '-', /source/hh-datum/channel/era/hh-start-date[@label='start']/@month, '-', /source/hh-datum/channel/era/hh-start-date[@label='start']/@day, ' ', /source/hh-datum/channel/era/hh-start-date[@label='start']/@hour, ':', /source/hh-datum/channel/era/hh-start-date[@label='start']/@minute)" />
						</td>
					</tr>
					<tr>
						<td>Finish Date</td>
						<td>
							<xsl:choose>
								<xsl:when
									test="/source/hh-datum/channel/era/hh-start-date[@label='finish']">
									<xsl:value-of
										select="concat(/source/hh-datum/channel/era/hh-start-date[@label='finish']/@year, '-', /source/hh-datum/channel/era/hh-start-date[@label='finish']/@month, '-', /source/hh-datum/channel/era/hh-start-date[@label='finish']/@day, ' ', /source/hh-datum/channel/era/hh-start-date[@label='finish']/@hour, ':', /source/hh-datum/channel/era/hh-start-date[@label='finish']/@minute)" />
								</xsl:when>
								<xsl:otherwise>
									Ongoing
								</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
				</table>

				<h4>Channel</h4>
				<ul>
					<li>
						<xsl:choose>
							<xsl:when test="/source/hh-datum/channel/@is-import = 'true'">
								Import
							</xsl:when>
							<xsl:otherwise>
								Export
							</xsl:otherwise>
						</xsl:choose>
					</li>
					<li>
						<xsl:choose>
							<xsl:when test="/source/hh-datum/channel/@is-kwh = 'true'">
								kWh
							</xsl:when>
							<xsl:otherwise>
								kVArh
							</xsl:otherwise>
						</xsl:choose>
					</li>
				</ul>
				<h4>HH Datum</h4>
				<xsl:choose>
					<xsl:when
						test="/source/request/@method='get' and /source/request/parameter[@name='view']/value='confirm-delete'">
						<form method="post" action=".">
							<fieldset>
								<legend>Confirm Delete</legend>
								<p>
									Are you sure you want to delete this
									HH datum?
								</p>
								<input type="submit" name="delete" value="Delete" />
							</fieldset>
						</form>
						<p>
							<a href=".">Cancel</a>
						</p>
					</xsl:when>
					<xsl:otherwise>
						<table>
							<tr>
								<th>Date</th>
								<td>
									<xsl:value-of
										select="concat(/source/hh-datum/hh-start-date/@year, '-', /source/hh-datum/hh-start-date/@month, '-', /source/hh-datum/hh-start-date/@day, ' ', /source/hh-datum/hh-start-date/@hour, ':', /source/hh-datum/hh-start-date/@minute)" />
								</td>
							</tr>
						</table>
						<br />
						<form action="." method="post">
							<fieldset>
								<legend>Update</legend>
								<label>
									Value
									<input name="value">
										<xsl:attribute name="value">
											<xsl:choose>
												<xsl:when test="/source/request/parameter[@name='value']">
													<xsl:value-of
											select="/source/request/parameter[@name='value']/value/text()" />
												</xsl:when>
												<xsl:otherwise>
													<xsl:value-of select="/source/hh-datum/@value" />
												</xsl:otherwise>
											</xsl:choose>
										</xsl:attribute>
									</input>
								</label>
								<br />
								<label>
									Status
									<select name="status">
										<option value="E">
											<xsl:choose>
												<xsl:when test="/source/request/parameter[@name='status']">

													<xsl:if
														test="/source/request/parameter[@name='status']/value/text() = 'E'">
														<xsl:attribute name="selected" />
													</xsl:if>
												</xsl:when>
												<xsl:otherwise>
													<xsl:if test="/source/hh-datum/@status = 'E'">
														<xsl:attribute name="selected" />
													</xsl:if>
												</xsl:otherwise>
											</xsl:choose>
											Estimate
										</option>
										<option value="A">
											<xsl:choose>
												<xsl:when test="/source/request/parameter[@name='status']">

													<xsl:if
														test="/source/request/parameter[@name='status']/value/text() = 'A'">
														<xsl:attribute name="selected" />
													</xsl:if>
												</xsl:when>
												<xsl:otherwise>
													<xsl:if test="/source/hh-datum/@status = 'A'">
														<xsl:attribute name="selected" />
													</xsl:if>
												</xsl:otherwise>
											</xsl:choose>
											Actual
										</option>
									</select>
								</label>
								<br />
								<br />
								<input type="submit" value="Update" />
								<xsl:value-of select="' '" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
						<br />
						<form action=".">
							<fieldset>
								<input type="hidden" name="view" value="confirm-delete" />
								<legend>Delete</legend>
								<br />
								<input type="submit" value="Delete" />
								<xsl:value-of select="' '" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>