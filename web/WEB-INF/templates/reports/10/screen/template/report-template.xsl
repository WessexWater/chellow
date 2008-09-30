<?xml version="1.0" encoding="us-ascii"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="xml" doctype-public="-//W3C//DTD SVG 1.1//EN"
        doctype-system="http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd"
        indent="yes" />
    <xsl:template match="/">
      <svg width="{count(/source/site/hh) + 200}px" height="400px" version="1.1"
            xmlns="http://www.w3.org/2000/svg">
        <xsl:choose>
	  <xsl:when test="/source/site/hh">
        <xsl:variable name="scale-factor" select="300 div (/source/site/@max-scale - /source/site/@min-scale)" />
        <g transform="translate(100, {50 + /source/site/@max-scale * $scale-factor})">
          <g transform="matrix(1,0,0,-1,0,0)" stroke="blue">
            <xsl:for-each select="/source/site/hh">
              <line x1="{position()}" y1="0" x2="{position()}">
                <xsl:if test="@incomplete">
                  <xsl:attribute name="stroke">black</xsl:attribute>
                </xsl:if>
                <xsl:attribute name="y2">
                  <xsl:choose>
                    <xsl:when test="@value = 0 and @incomplete">
                      <xsl:value-of select="/source/site/@max-scale * $scale-factor"/>
                    </xsl:when>
                    <xsl:otherwise>
                      <xsl:value-of select="@value * $scale-factor"/>
                    </xsl:otherwise>
                  </xsl:choose>
                </xsl:attribute>
              </line>
            </xsl:for-each>
          </g>

          <g stroke="black">

            <xsl:for-each select="/source/site/hh">

              <xsl:if test="@hour = 0 and @minute = 0">

                <text x="{position() + 16}" y="{20 - ../@min-scale * $scale-factor}"  font-size="12">
                  <xsl:if test="@day-of-week &gt; 4">
                    <xsl:attribute name="stroke">red</xsl:attribute>  
                  </xsl:if>
                  <xsl:value-of select="@day"/>
                </text>
                <line x1="{position()}" y1="{-1 * ../@min-scale * $scale-factor}" x2="{position()}" y2="{5 - ../@min-scale * $scale-factor}" />

                <xsl:if test="@day = 15">
                  <text x="{position() + 16}" y="{45 - ../@min-scale * $scale-factor}"  font-size="12">
                    <xsl:value-of select="@month-text"/>
                  </text>
                </xsl:if>


              </xsl:if>
            </xsl:for-each>
            <xsl:for-each select="/source/scale/scale-point">
              <xsl:variable name="y" select="-1 * @value * $scale-factor" />
              <line x1="-5" y1="{$y}" x2="{count(/source/site/hh)}" y2="{$y}" />
              <text x="-40" y="{$y + 5}"  font-size="12">
                <xsl:value-of select="@value * 2"/>
              </text>
            </xsl:for-each>
            <text x="-90" y="-150"  font-size="12">
                kW
            </text>
          </g>

        </g>
        <g>
          <text x="30" y="30" font-size="12"
                font-family="Verdana">
            <xsl:value-of select="concat('Electricity use at site ', /source/site/@code, ' ', /source/site/@name, ' for ', /source/request/parameter[@name='months'], ' month')"/>
              <xsl:if test="/source/request/parameter[@name='months'] &gt; 1">
                <xsl:value-of select="'s'"/>
              </xsl:if>
              <xsl:value-of select="concat(' ending ', /source/@finish-date-month-text, ' ', /source/request/parameter[@name='finish-date-year']/value)"/>
          </text>
        </g>
</xsl:when>
				<xsl:otherwise>
					<g>
						<text x="10" y="30" font-size="11"
							font-family="Verdana">
							<xsl:value-of
								select="'No data for this period'" />
						</text>
					</g>
				</xsl:otherwise>
			</xsl:choose>
      </svg>
    </xsl:template>
</xsl:stylesheet>

