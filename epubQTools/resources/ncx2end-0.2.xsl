<?xml version="1.0"?>
<xsl:stylesheet version="1.0" 
                exclude-result-prefixes="ncx xsl"
                xmlns="http://www.w3.org/1999/xhtml"
                xmlns:ncx="http://www.daisy.org/z3986/2005/ncx/"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- Text for the top-level `h1` inside the primary `nav` element -->
  <xsl:param name='contents-str'>Spis treści</xsl:param>

  <!-- @id value for primary toc `nav` element -->
  <xsl:param name='toc-id'>toc</xsl:param>


  <xsl:template match="ncx:ncx">
    <html>
      <xsl:call-template name="html-head"/>
      <body>
        <xsl:apply-templates/>
      </body>
    </html>
  </xsl:template>

  <xsl:template match="ncx:navMap|ncx:pageList">
        <xsl:choose>
          <xsl:when test="ncx:navInfo">
            <xsl:apply-templates select="ncx:navInfo"/>
          </xsl:when>
          <xsl:when test="ncx:navLabel">
            <xsl:apply-templates select="ncx:navLabel" mode="heading"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:if test="self::ncx:navMap">
              <h1><xsl:value-of select="$contents-str"/></h1>
            </xsl:if>
          </xsl:otherwise>
        </xsl:choose>
        <ul>
          <xsl:apply-templates select="ncx:navPoint|ncx:navLabel|ncx:pageTarget"/>
        </ul>

  </xsl:template>

  <xsl:template match="ncx:navInfo">
    <h1>
      <xsl:copy-of select="@class"/>
      <xsl:apply-templates/>
    </h1>
  </xsl:template>
  <xsl:template match="ncx:pageList/ncx:navLabel" mode="heading">
    <h2>
      <xsl:copy-of select="@class"/>
      <xsl:apply-templates/>
    </h2>
  </xsl:template>

  <xsl:template match="ncx:navPoint|ncx:pageTarget">
    <xsl:text>&#10;</xsl:text>
    <li>
      <xsl:copy-of select="@class"/>

      <!-- every navPoint and pageTarget has to have a navLabel and content -->
      <a>
         <xsl:attribute name="href">
          <xsl:value-of select="ncx:content[1]/@src"/>
        </xsl:attribute>
        <xsl:apply-templates select="ncx:navLabel"/>
      </a>

      <!-- Only some navPoints have more navPoints inside them for deep NCXes. pageTargets cannot nest. -->
      <xsl:if test="ncx:navPoint">
        <ul>
          <xsl:apply-templates select="ncx:navPoint"/>
        </ul>
      </xsl:if>
    </li>
  </xsl:template>

  <xsl:template match="ncx:navLabel|
                       ncx:text">
    <xsl:apply-templates/>
  </xsl:template>

  <!-- Ignore these elements -->
  <xsl:template match="ncx:head|
                       ncx:docAuthor|
                       ncx:docTitle|
                       ncx:pageList/ncx:navLabel"/>
  <xsl:template match="ncx:head/text()|
                       ncx:docAuthor/text()|
                       ncx:docTitle/text()|
                       ncx:navLabel/text()"/>

  <!-- Default rule to catch omissions -->
  <xsl:template match="*">
    <xsl:message terminate="yes">ERROR: <xsl:value-of select="name(.)"/> not matched!
    </xsl:message>
  </xsl:template>

  <xsl:template name="html-head">
    <head>
      <title><xsl:apply-templates select="/ncx:ncx/ncx:docTitle/ncx:text"/></title>
      <style type="text/css">ul {padding-left: 1em} h1 {text-align: center}</style>
    </head>  
  </xsl:template>

</xsl:stylesheet>
