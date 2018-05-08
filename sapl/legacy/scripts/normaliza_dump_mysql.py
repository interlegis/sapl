#!/usr/bin/env python
import re
import sys

from unipath import Path

cabecalho = '''
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

/*!40000 DROP DATABASE IF EXISTS `{banco}`*/;

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `{banco}` /*!40100 DEFAULT CHARACTER SET latin1 */;

USE `{banco}`;

'''


def normaliza_dump_mysql(nome_arquivo):
    arquivo = Path(nome_arquivo).expand()
    banco = arquivo.stem
    conteudo = arquivo.read_file()
    inicio = re.finditer('--\n-- Table structure for table .*\n--\n', conteudo)
    inicio = next(inicio).start()
    conteudo = cabecalho.format(banco=banco) + conteudo[inicio:]
    arquivo.write_file(conteudo)


if __name__ == "__main__":
    nome_aquivo = sys.argv[1]
    normaliza_dump_mysql(nome_aquivo)
