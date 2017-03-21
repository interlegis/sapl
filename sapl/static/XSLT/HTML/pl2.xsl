<?xml version="1.0" encoding="ISO-8859-1"?> 
<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
xmlns:ind="/XSD/ProjLei"> 


<xsl:template match="/"> 
<html> 
<head> 
<link href="/sapl/XSLT/HTML/estilo.css" rel="stylesheet" type="text/css"/>
</head> 
<body> 
<div> 
    <div id="imagem"> 
        <img border="0" src="/sapl/sapl_documentos/props_sapl/logo_casa"/> 
    </div><br></br> 
    <p class ="cabecalho">Câmara Municipal de Agudo</p> 
    <p class ="pequeno">Estado do Rio Grande do Sul<br></br><br></br><br></br> </p> 
 </div>

<xsl:apply-templates /> 
</body> 
</html> 
</xsl:template>

<xsl:template match="ind:epigrafe_text"> 
	<p class ="autor"><strong><xsl:value-of select="text()" /></strong></p>
</xsl:template>

<xsl:template match="ind:ementa_text"> 
	<p class ="ementa"><xsl:value-of select="text()" /></p>
</xsl:template>

<xsl:template match="ind:preambulo_text"> 
	<p class ="artigo"><xsl:value-of select="text()" /></p>
</xsl:template>

<xsl:template match="ind:parte_text"> 
        <p class ="titulos1"><xsl:value-of select="concat(../@Rotulo,'  ')"/></p>
	<p class ="titulos2"><xsl:value-of select="text()"/></p>
</xsl:template>

<xsl:template match="ind:livro_text">
        <p class ="titulos1"><xsl:value-of select="concat(../@Rotulo,'  ')"/></p>
	<p class ="titulos2"><xsl:value-of select="text()"/></p>
</xsl:template>

<xsl:template match="ind:titulo_text">
        <p class ="titulos1"><xsl:value-of select="concat(../@Rotulo,'  ')"/></p>
	<p class ="titulos2"><xsl:value-of select="text()"/></p>
</xsl:template>

<xsl:template match="ind:capitulo_text"> 
        <p class ="titulos1"><xsl:value-of select="concat(../@Rotulo,'  ')"/></p>
	<p class ="titulos2"><xsl:value-of select="text()"/></p>
</xsl:template>

<xsl:template match="ind:secao_text"> 
        <p class ="titulos1"><xsl:value-of select="concat(../@Rotulo,'  ')"/></p>
	<p class ="titulos2"><xsl:value-of select="text()"/></p>
</xsl:template>

<xsl:template match="ind:subsecao_text">
        <p class ="titulos1"><xsl:value-of select="concat(../@Rotulo,'  ')"/></p>
	<p class ="titulos2"><xsl:value-of select="text()"/></p>
</xsl:template>

<xsl:template match="ind:artigo_text">
	<p class="artigo"><xsl:value-of select="concat(../@Rotulo,'  ',text())"/></p>
</xsl:template>

<xsl:template match="ind:paragrafo_text">
	<p class="artigo"><xsl:value-of select="concat(../@Rotulo,'  ',text())"/></p>
</xsl:template>

<xsl:template match="ind:inciso_text">
	<p class="artigo"><xsl:value-of select="concat(../@Rotulo,'  ',text())"/></p>
</xsl:template>

<xsl:template match="ind:alinea_text">
	<p class="artigo"><xsl:value-of select="concat(../@Rotulo,'  ',text())"/></p>
</xsl:template>

<xsl:template match="ind:item_text">
	<p class="artigo"><xsl:value-of select="concat(../@Rotulo,'  ',text())"/></p>
</xsl:template>

<xsl:template match="ind:data_apresentacao_text">
	<p class="artigo"><xsl:value-of select="concat(../@Rotulo,'  ',text())"/></p>
</xsl:template>

<xsl:template match="ind:autor_text">
	<p class="artigo"><xsl:value-of select="concat(../@Rotulo,'  ',text())"/></p>
</xsl:template>

<xsl:template match="ind:justificativa_text">
        <p class="artigo"><xsl:value-of select="text()" /></p>
</xsl:template>

</xsl:stylesheet>