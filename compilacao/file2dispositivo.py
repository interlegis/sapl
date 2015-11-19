import re

from odf.element import Node, Text
from odf.opendocument import load
from odf.table import Table, TableCell, TableRow
from odf.text import (List, ListHeader, ListItem, ListLevelStyleBullet,
                      ListLevelStyleNumber, ListStyle, Note)

from sapl import utils


class Parser(object):

    parser_list = []

    def parser(self, _filepath):

        self.filepath = _filepath

        return self.re_parser()

    def re_parser(self):

        self.parser_list = []

        # odt identificado pela extensão ou teste caso o arquivo sem extensão
        if self.filepath.endswith('.odt') or\
                not re.search(r"(\w+)\.(\w+)", self.filepath):

            try:
                odtparser = OdtParser()

                self.parser_list = odtparser.parser(self.filepath)

                return self.parser_list
            except Exception as e:
                print(e)
                # TODO: Continue para outros formatos
                pass

        # doc identificado pela extensão ou teste caso o arquivo sem extensão
        if self.filepath.endswith(('.doc', 'docx')) or\
                not re.search(r"(\w+)\.(\w+)", self.filepath):

            try:
                # TODO
                return []
            except Exception as e:
                # TODO: Continue para outros formatos
                pass

        return []

    def _reduce_terms(self, _nodes=None, level=0):
        print(level)
        if not _nodes:
            nodes = self.parser_list
        else:
            nodes = _nodes

        fstr = True
        i = -1
        for nd in nodes:
            i += 1
            # print(nd)

            if not _nodes:
                fstr = False
                if nd[0] == 'table:table':
                    continue

            if isinstance(nd, list):
                fstr = False
                nodes[i] = self._reduce_terms(nd, level=level + 1)

        if fstr:
            return ' '.join(nodes)
        return nodes


class OdtParser(Parser):
    FNC1 = '1'
    FNCI = 'I'
    FNCi = 'i'
    FNCA = 'A'
    FNCa = 'a'
    FNC8 = '*'
    FNCN = 'N'

    def re_parser(self):

        self.textdoc = load(self.filepath)
        self.level_list = 0
        self.control_list = {}

        # mm = ODF2MoinMoin(self.filepath)
        # self.parser_list = [mm.toString(), ]

        self.parser_list = self._import_itens(self.textdoc.text, level=0)

        # self._reduce_terms()

        return self.parser_list

    def _import_itens(self, element, level=0):
        try:
            result = []
            for el in element.childNodes:
                print(level, el.tagName)
                _r = ''
                if el.tagName == 'Text':
                    _r = str(el)
                else:
                    if el.isInstanceOf(Note):
                        continue
                    elif el.isInstanceOf(Table):
                        _r = self._import_table(el, level=level + 1)
                    elif el.isInstanceOf(List):
                        _r = self._import_list(el, level=level + 1)
                    # elif el.isInstanceOf(P):
                    #    _r = [self.extractText(el),]
                    elif el.hasChildNodes():
                        _r = self._import_itens(el, level=level + 1)
                    else:
                        _r = str(el)

                if _r:
                    if isinstance(_r, str):
                        result += [_r, ]
                    else:
                        result += _r

            return result
        except Exception as e:
            print(e)

    def _import_table(self, element, level=0):
        result = ''
        print(level)
        try:
            if element.isInstanceOf(Table):
                result += '<table width="100%">'

            for el in element.childNodes:
                _r = ''
                if isinstance(el, Text):
                    _r = str(el)
                else:
                    if el.isInstanceOf(TableRow):
                        _r = self._import_table(el, level=level + 1)
                        _r = '<tr>%s</tr>' % (''.join(_r))
                        result += ''.join(_r)
                    elif el.isInstanceOf(TableCell):
                        _r = self._import_table(el, level=level + 1)
                        if el.getAttribute('numberrowsspanned'):
                            _r = '<td rowspan="%s">%s</td>' % (
                                el.getAttribute('numberrowsspanned'),
                                ''.join(_r))
                        elif el.getAttribute('numbercolumnsspanned'):
                            _r = '<td colspan="%s">%s</td>' % (
                                el.getAttribute('numbercolumnsspanned'),
                                ''.join(_r))
                        else:
                            _r = '<td>%s</td>' % (''.join(_r))

                        result += ''.join(_r)
                    else:
                        _r = self.extractText(el)
                        # _r = self._reduce_terms(_r)
                        if isinstance(_r, list):
                            result += '<br>'.join(_r)
                        else:
                            if _r:
                                result += _r + '<br>'

            if element.isInstanceOf(Table):
                result += '</table>'

            return [result, ]
        except Exception as e:
            print(e)

    def _import_list(self, element, level=0):
        self.level_list += 1
        result = []
        print(level)

        numsufixo = ''
        numformat = ''
        startvalue = ''

        count_list_item = 0

        try:
            if element.isInstanceOf(List):
                _stylename = element.getAttribute('stylename')

                if _stylename:
                    self.stylename = _stylename

                liststyles = self.textdoc.getElementsByType(ListStyle)

                for liststyle in liststyles:
                    if liststyle.getAttribute('name') == self.stylename:
                        break

                stylesnumbers = liststyle.getElementsByType(
                    ListLevelStyleNumber)

                for item in stylesnumbers:
                    if item.getAttribute('level') == str(self.level_list):
                        numsufixo = item.getAttribute('numsuffix') or ''
                        numformat = item.getAttribute('numformat') or ''
                        startvalue = item.getAttribute('startvalue') or ''
                        break

                if not numformat:
                    stylesbullets = liststyle.getElementsByType(
                        ListLevelStyleBullet)
                    for item in stylesbullets:
                        if item.getAttribute('level') == str(self.level_list):
                            numformat = '*'
                            break

                _id = element.getAttribute('id')
                if _id:
                    self.id_last_list = _id

                if self.id_last_list not in self.control_list:
                    self.control_list[self.id_last_list] = [0, ] * 10

                if _id:
                    if not element.getAttribute('continuelist') and\
                            self.level_list == 1:
                        self.control_list[self.id_last_list] = [0, ] * 10

        except Exception as e:
            print(e)

        try:
            flag_first = True
            for el in element.childNodes:
                prefixo = ''
                if isinstance(el, Text):
                    _r = [str(el), ]
                else:
                    if el.isInstanceOf(ListHeader) or\
                            el.isInstanceOf(ListItem):

                        if startvalue and flag_first:
                            self.control_list[self.id_last_list][
                                self.level_list - 1] = int(startvalue) - 1
                            flag_first = False

                        self.control_list[self.id_last_list][
                            self.level_list - 1] += 1
                        count_list_item = self.control_list[self.id_last_list][
                            self.level_list - 1]

                        if numformat == OdtParser.FNC1:
                            prefixo = str(count_list_item)
                        elif numformat == OdtParser.FNCI:
                            prefixo = utils.int_to_roman(count_list_item)
                        elif numformat == OdtParser.FNCi:
                            prefixo = utils.int_to_roman(
                                count_list_item).lower()
                        elif numformat == OdtParser.FNCA:
                            prefixo = utils.int_to_letter(count_list_item)
                        elif numformat == OdtParser.FNCa:
                            prefixo = utils.int_to_letter(
                                count_list_item).lower()
                        elif numformat == OdtParser.FNC8:
                            prefixo = '*'
                        else:
                            prefixo = str(count_list_item)

                        prefixo += numsufixo

                    _r = self._import_itens(el, level=level + 1)

                if _r:
                    if prefixo:
                        _r[0] = '%s %s' % (prefixo, _r[0])
                        result += _r
                    else:
                        result += _r

            self.level_list -= 1
            return result

        except Exception as e:
            print(e)

    def extractText(self, odfElement):
        """ Extract text content from an Element, with whitespace represented
            properly. Returns the text, with tabs, spaces, and newlines
            correctly evaluated. This method recursively descends through the
            children of the given element, accumulating text and "unwrapping"
            <text:s>, <text:tab>, and <text:line-break> elements along the way.
        """
        result = []

        if len(odfElement.childNodes) != 0:
            for child in odfElement.childNodes:
                if child.nodeType == Node.TEXT_NODE:
                    result.append(child.data)
                elif child.nodeType == Node.ELEMENT_NODE:
                    subElement = child
                    tagName = subElement.qname
                    if tagName == (u"urn:oasis:names:tc:opendocument:xmlns:" +
                                   "text:1.0", u"line-break"):
                        result.append("\n")
                    elif tagName == (u"urn:oasis:names:tc:opendocument:" +
                                     "xmlns:text:1.0", u"tab"):
                        result.append("\t")
                    elif tagName == (u"urn:oasis:names:tc:opendocument:" +
                                     "xmlns:text:1.0", u"s"):
                        c = subElement.getAttribute('c')
                        if c:
                            spaceCount = int(c)
                        else:
                            spaceCount = 1

                        result.append(" " * spaceCount)
                    else:
                        result.append(self.extractText(subElement))
        return ''.join(result)
