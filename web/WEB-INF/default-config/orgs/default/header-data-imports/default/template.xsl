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
					<xsl:value-of
						select="/source/header-import-process/org/@name" />
					&gt; Header Data Imports &gt;
					<xsl:value-of
						select="/source/header-import-process/@id" />
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
						href="{/source/request/@context-path}/orgs/{/source/header-import-process/org/@id}/">
						<xsl:value-of
							select="/source/header-import-process/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/header-import-process/org/@id}/header-data-imports/">
						<xsl:value-of select="'Header Data Imports'" />
					</a>
					&gt;
					<xsl:value-of
						select="/source/header-import-process/@id" />
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
				<br />
				<xsl:if test="/source/csvLine">
					<table id="import_table">
						<caption>Failed line</caption>

						<thead>
							<tr>
								<th>Line number</th>
								<th>Action</th>

								<th>Type</th>
							</tr>
						</thead>

						<tbody>
							<xsl:for-each select="/source/csvLine">
								<tr>
									<td>
										<xsl:value-of select="@number" />
									</td>

									<xsl:for-each select="Field">
										<td>
											<xsl:if
												test="position() > 2">
												<em>
													<xsl:value-of
														select="@name" />
												</em>
												<xsl:value-of
													select="' '" />
											</xsl:if>
											<xsl:value-of
												select="text()" />
										</td>
									</xsl:for-each>

									<td>
										<xsl:if test="check-digit">
											<p>
												There's a problem with a
												check-digit (the last
												digit of the MPAN core).
												<xsl:value-of
													select="check-digit/message/@description" />
											</p>
										</xsl:if>
										<xsl:if test="mpan-core">
											<p>
												There's a problem with
												the
												<xsl:value-of
													select="mpan-core/@label" />
												MPAN core.
												<xsl:value-of
													select="mpan-core/message/@description" />
											</p>
										</xsl:if>

										<xsl:if test="source-code">
											<xsl:if
												test="source-code/message/@code = 'string_too_long'">
												<p>
													The maximum length
													of the Source Code
													is
													<xsl:value-of
														select="source-code/message/parameter/@value" />
												</p>
											</xsl:if>
										</xsl:if>
										<xsl:if test="mpan-core-raw">
											<p>
												There's a problem with
												the
												<xsl:value-of
													select="mpan-core-raw/@label" />
												MPAN core.
												<xsl:value-of
													select="mpan-core-raw/message/@description" />
											</p>
										</xsl:if>
										<xsl:if test="mpan-raw">

											<p>
												Problem with the
												<xsl:value-of
													select="MpanRaw/@label" />
												MPAN.
												<xsl:value-of
													select="MpanRaw/message/@description" />
											</p>
										</xsl:if>

										<xsl:if test="supply">
											<xsl:value-of
												select="supply/message/@description" />
										</xsl:if>

										<xsl:if test="date">
											<xsl:value-of
												select="date/message/@description" />
										</xsl:if>

										<xsl:if test="hh-end-date">
											<p>
												Problem with the
												<xsl:value-of
													select="hh-end-date/@label" />
												date.
											</p>
											<xsl:value-of
												select="hh-end-date/message/@description" />
										</xsl:if>
										<xsl:if
											test="meter-timeswitch-code">
											<p>
												Problem with the Meter
												Timeswitch Code
											</p>
											<xsl:value-of
												select="meter-timeswitch-code/message/@description" />
										</xsl:if>
										<xsl:if test="message">
											<ul>
												<xsl:for-each
													select="message">
													<li>
														<xsl:value-of
															select="@description" />
													</li>
												</xsl:for-each>
											</ul>
										</xsl:if>
									</td>
								</tr>
							</xsl:for-each>
						</tbody>
					</table>
				</xsl:if>

				<xsl:if
					test="/source/header-import-process/@progress">
					<p>
						<xsl:value-of
							select="/source/header-import-process/@progress" />
					</p>
					<p>Refresh the page to see latest progress.</p>

					<form method="post" action=".">

						<input type="submit" value="Cancel Import" />
					</form>
				</xsl:if>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>

