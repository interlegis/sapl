<?xml version="1.0" encoding="ISO-8859-1"?> 
<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
xmlns:ind="/XSD/Requerimento"> 


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

<xsl:template match="ind:ementa_text"> 
	<p class="autor"><strong><xsl:value-of select="text()" /></strong></p> 
</xsl:template>

<xsl:template match="ind:formatratamento_text"> 
	<p class="semrecuo"><xsl:value-of select="text()"/> </p>
</xsl:template> 

<xsl:template match="ind:parlamentar_text"> 
	<p class="semrecuo"><xsl:value-of select="text()" /></p> 
</xsl:template>

<xsl:template match="ind:cargofuncao_text"> 
	<p class="semrecuo"><xsl:value-of select="text()" /></p> 
</xsl:template>

<xsl:template match="ind:requisicao_text"> 
	<p class="texto"><xsl:value-of select="text()" /></p> 

</xsl:template> 
<xsl:template match="ind:justificativa_text"> 
	<p class="texto"><xsl:value-of select="text()" /></p> 

</xsl:template> 
<xsl:template match="ind:data_text"> 
	<p><xsl:value-of select="text()" /></p> 
</xsl:template> 

<xsl:template match="ind:autor_text"> 
	<p class="autor"><xsl:value-of select="text()" /></p> 
</xsl:template> 

</xsl:stylesheet>