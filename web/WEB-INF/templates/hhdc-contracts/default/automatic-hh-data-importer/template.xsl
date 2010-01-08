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
					Chellow &gt; HHDC Contracts &gt;
					<xsl:value-of
						select="/source/automatic-hh-data-importer/hhdc-contract/@name" />
					&gt; Automatic HH Data Downloader
				</title>

			</head>
			<body>
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
						href="{/source/request/@context-path}/hhdc-contracts/{/source/automatic-hh-data-importer/hhdc-contract/@id}/">
						<xsl:value-of
							select="/source/automatic-hh-data-importer/hhdc-contract/@name" />
					</a>
					&gt; Automatic HH Data Downloader
				</p>
				<table>
					<tr>
						<th>Is any import running?</th>
						<td>
							<xsl:choose>
								<xsl:when
									test="/source/@an-import-running='true'">
									Yes
								</xsl:when>
								<xsl:otherwise>No</xsl:otherwise>
							</xsl:choose>
						</td>
					</tr>
					<tr>
						<th>Status of this particular import</th>
						<td>
							<xsl:value-of
								select="/source/@thread-status" />
						</td>
					</tr>
					<tr>
						<th>Is this particular import locked?</th>
						<td>
							<xsl:value-of
								select="/source/@is-locked" />
						</td>
					</tr>
					
					<tr>
						<th>Stack trace of this particular import</th>
						<td>
							<xsl:value-of
								select="/source/stack-trace/text()" />
						</td>
					</tr>
				</table>
				<p>
					<a href=".">Refresh page</a>
				</p>
				<xsl:choose>
					<xsl:when
						test="/source/@thread-status = 'null' or /source/@thread-status = 'dead'">
						<form action="." method="post">
							<fieldset>
								<legend>Import now</legend>
								<input type="submit" value="Import" />
							</fieldset>
						</form>
					</xsl:when>
					<xsl:when test="/source/@thread-status = 'alive'">
						<form action="." method="post">
							<fieldset>
								<legend>Interrupt The Import</legend>
								<input type="submit" name="interrupt"
									value="Interrupt" />
							</fieldset>
						</form>
					</xsl:when>
				</xsl:choose>
				<br />
				<h1>Log</h1>
				<ul>
					<xsl:for-each select="//message">
						<li>
							<xsl:value-of select="@description" />
						</li>
					</xsl:for-each>
				</ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>