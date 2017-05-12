<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:pl="/XSD/ProjLei">
	<xsl:output encoding="ISO-8859-1"/>
	<xsl:template match="/pl:pl">
		<html>
			<head>
				<title>
					<xsl:value-of select="@id"/>
				</title>
				<style type="text/css">
                    body {margin-left: 2cm; margin-right: 1cm;}
                    p {font-family: Times; font-size: 12pt;}
                    p.epigrafe {text-align: center; text-transform: uppercase;}
                    p.ementa {text-align: justify; margin-left: 50%;}
                    p.preambulo {text-transform: uppercase; text-indent: 1cm;}
                    p.artigo {text-align: justify; text-indent: 1cm;}
                    p.paragrafo {text-align: justify; text-indent: 1cm;}
                    p.inciso {text-align: justify; text-indent: 1cm;}
                    p.alinea {text-align: justify; text-indent: 1cm;}
                    p.item {text-align: justify; text-indent: 1cm;}
                    p.justificativa {text-align: justify; text-indent: 1cm;}
                    p.mensagem {text-align: justify;}
                    p.data_apresentacao {text-align: justify; text-indent: 1cm;}
                    p.autor {text-align: center; text-transform: uppercase;}
                    h3.cab_secao {text-align: center; font-size: 12pt;}
                </style>
			</head>
			<body>
				<xsl:apply-templates/>
			</body>
		</html>
	</xsl:template>
	<xsl:template match="pl:proposicao">
		<hr/>
		<h3 class="cab_secao">PROPOSIÇÃO</h3>
		<hr/>
		<xsl:apply-templates select="./*"/>
	</xsl:template>
	<xsl:template match="pl:epigrafe">
		<p class="epigrafe">
			<xsl:value-of select="pl:epigrafe_text"/>
		</p>
	</xsl:template>
	<xsl:template match="pl:ementa">
		<p class="ementa">
			<xsl:value-of select="pl:ementa_text"/>
		</p>
	</xsl:template>
	<xsl:template match="pl:preambulo">
		<p class="preambulo">
			<xsl:value-of select="pl:preambulo_text"/>
		</p>
	</xsl:template>
	<xsl:template match="pl:artigo_text">
		<p class="artigo">
			<xsl:value-of select="concat(../@Rotulo,'  ',text())"/>
		</p>
	</xsl:template>
	<xsl:template match="pl:paragrafo_text">
		<p class="paragrafo">
			<xsl:value-of select="concat(../@Rotulo,'  ',text())"/>
		</p>
	</xsl:template>
	<xsl:template match="pl:inciso_text">
		<p class="inciso">
			<xsl:value-of select="concat(../@Rotulo,' - ',text())"/>
		</p>
	</xsl:template>
	<xsl:template match="pl:alinea_text">
		<p class="alinea">
			<xsl:value-of select="concat(../@Rotulo,'  ',text())"/>
		</p>
	</xsl:template>
	<xsl:template match="pl:item_text">
		<p class="item">
			<xsl:value-of select="concat(../@Rotulo,'  ',text())"/>
		</p>
	</xsl:template>
	<xsl:template match="pl:data_apresentacao_text">
		<p class="data_apresentacao">
			<xsl:value-of select="text()"/>
		</p>
	</xsl:template>
	<xsl:template match="pl:autor_text">
		<p class="autor">
			<xsl:value-of select="text()"/>
		</p>
	</xsl:template>
	<xsl:template match="pl:justificativa">
		<hr/>
		<h3 class="cab_secao">JUSTIFICATIVA</h3>
		<hr/>
		<p class="justificativa">
			<xsl:value-of select="pl:justificativa_text"/>
		</p>
	</xsl:template>
	<xsl:template match="pl:mensagem">
		<hr/>
		<h3 class="cab_secao">MENSAGEM</h3>
		<hr/>
		<p class="mensagem">
			<xsl:value-of select="pl:mensagem_text"/>
		</p>
	</xsl:template>
</xsl:stylesheet>