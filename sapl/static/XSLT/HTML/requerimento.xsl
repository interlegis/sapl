<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:req="/XSD/Requerimento">

<xsl:template match="/">
	<html>
		<body>
			<table>
				<xsl:apply-templates />
		        </table>
		</body>
	</html>
</xsl:template>
<xsl:template match="req:destinatario_text">
	<tr>
		<td colspan="2" align="left"><xsl:value-of select="text()" /></td>
	</tr>
</xsl:template>

<xsl:template match="req:ementa_text">
	<tr>
		<td width="50%"></td>
		<td width="50%" align="left"><xsl:value-of select="text()" /></td>
	</tr>
</xsl:template>

<xsl:template match="req:requisicao_text">
	<tr>
		<td colspan="2" align="left"><xsl:value-of select="text()" /></td>
	</tr>
</xsl:template>

<xsl:template match="req:justificativa_text">
	<tr>
		<td colspan="2" align="left"><xsl:value-of select="text()" /></td>
	</tr>
</xsl:template>

<xsl:template match="req:data_text">
	<tr>
		<td colspan="2" align="left"><xsl:value-of select="text()" /></td>
	</tr>
</xsl:template>

<xsl:template match="req:autor_text">
	<tr>
		<td colspan="2" align="left"><xsl:value-of select="text()" /></td>
	</tr>
</xsl:template>

</xsl:stylesheet>
