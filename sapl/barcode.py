from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.graphics.shapes import Drawing
from reportlab.lib.units import mm


class BarcodeDrawing(Drawing):

    def __init__(self, text_value, *args, **kw):
        barcode = createBarcodeDrawing(
            'Code128',
            value=text_value,
            barHeight=10 * mm,
            humanReadable=True)
        Drawing.__init__(self, barcode.width, barcode.height, *args, **kw)
        self.add(barcode, name='barcode')


# def barcode(request):
#     #instantiate a drawing object
#     import barcode
#     d = barcode.BarcodeDrawing("HELLO WORLD")
#     binaryStuff = d.asString('gif')
#     return HttpResponse(binaryStuff, 'image/gif')

if __name__ == '__main__':
    # use the standard 'save' method to save barcode.gif, barcode.pdf etc
    # for quick feedback while working.
    BarcodeDrawing("HELLO WORLD").save(
        formats=['gif', 'pdf'], outDir='.', fnRoot='barcode')
