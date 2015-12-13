$( window ).scroll(function() {
    if (window.pageYOffset <= 180)
        $( "section.vigencias" ).removeClass("fixed");
    else if (!$( "section.vigencias" ).hasClass("fixed"))
        $( "section.vigencias" ).addClass("fixed");
});

$(window).load(function() {
    setTimeout(function() {
	    height = $( "section.vigencias" ).height();
        $('html, body').animate({
        scrollTop:  window.pageYOffset - height - 55
        }, 300);
    }, 100);
});

function textoMultiVigente(item, diff) {
	$(".cp .tipo-vigencias a").removeClass("selected")
	$(item).addClass("selected")
	$(".dptt.desativado").removeClass("displaynone");
	$(".dtxt").removeClass("displaynone");
	$(".dtxt.diff").remove();
	$(".link_alterador").removeClass("displaynone");

    if (diff) {
        $(".dtxt[id^='da'").each(function() {
  
            if ( $(this).html().search( /<\/\w+>/g ) > 0)
                return;

            var pk = $(this).attr('pk')
            var pks = $(this).attr('pks')

            var a = $('#d'+pks).contents().filter(function () {
                return this.nodeType === Node.TEXT_NODE;
            });
            var b = $('#da'+pk).contents().filter(function () {
                return this.nodeType === Node.TEXT_NODE;
            });




            var  diff = JsDiff.diffWordsWithSpace($(a).text(), $(b).text());

            if (diff.length > 0) {
                $('#d'+pks).closest('.desativado').addClass("displaynone");

                var clone = $('#da'+pk).clone();
                $('#da'+pk).after( clone );
                $('#da'+pk).addClass('displaynone');
                $(clone).addClass('diff').html('');


                diff.forEach(function(part){
                    var color = part.added ? '#018' :
                      part.removed ? '#faa' : '';

                    var span = document.createElement('span');

                    var value = part.value;

                    if (part.removed) {
                        $(span).addClass('desativado')
                        value += ' ';
                    }
                    else if (part.added) {
                        $(span).addClass('added')
                    }

                    span.appendChild(document.createTextNode(value));
                    $(clone).append(span);
                });
            }
        });
        //textoVigente(item, true);
    }
}

function textoVigente(item, link) {
	$(".cp .tipo-vigencias a").removeClass("selected")
	$(item).addClass("selected")

	$(".dptt.desativado").addClass("displaynone");
	$(".link_alterador").removeClass("displaynone");
	if (!link)
		$(".link_alterador").addClass("displaynone");
}

$(document).ready(function() {
	$("#btn_font_menos").click(function() {
	    $(".dpt").css("font-size", "-=1");
	});
	$("#btn_font_mais").click(function() {
	    $(".dpt").css("font-size", "+=1");
	});




});
