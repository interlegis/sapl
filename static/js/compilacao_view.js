$( window ).scroll(function() {
    if (window.pageYOffset <= 180)
        $( "section.vigencias" ).removeClass("fixed");
    else if ( ! $( "section.vigencias" ).hasClass("fixed") )
        $( "section.vigencias" ).addClass("fixed");
});


function isElementInViewport (el) {

    //special bonus for those using jQuery
    if (typeof jQuery === "function" && el instanceof jQuery) {
        el = el[0];
    }

    var rect = el.getBoundingClientRect();

    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) && /*or $(window).height() */
        rect.right <= (window.innerWidth || document.documentElement.clientWidth) /*or $(window).width() */
    );
}

function textoMultiVigente(item, diff) {
	var elv = null;
	var ldpts = $(".dptt")
	for (var i = 0; i < ldpts.length; i++) {
		if ($(ldpts[i]).hasClass('displaynone'))
			continue;
		if (isElementInViewport( ldpts[i])) {
			elv = ldpts[i];
			break;
		}
	}

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

    if (elv) {
	    $('html, body').animate({
			scrollTop: $(elv).parent().offset().top - 60
		}, 0);
    }
}

function textoVigente(item, link) {
	var elv = null;
	var ldpts = $(".dptt")
	for (var i = 0; i < ldpts.length; i++) {
		if ($(ldpts[i]).hasClass('displaynone'))
			continue;
		if (isElementInViewport( ldpts[i])) {
			elv = ldpts[i];
			break;
		}
	}

		$(".cp .tipo-vigencias a").removeClass("selected")
		$(item).addClass("selected")

		$(".dptt.desativado").addClass("displaynone");
		$(".link_alterador").removeClass("displaynone");
		if (!link)
			$(".link_alterador").addClass("displaynone");

	if (elv) {
	    $('html, body').animate({
			scrollTop: $(elv).parent().offset().top - 60
		}, 0);
    }
}

$(document).ready(function() {
    setTimeout(function() {
    	var href = location.href.split('#')
    	if (href.length == 2) {
    		$('html, body').animate({
                scrollTop: $('#dptt' + href[1] ).offset().top - window.innerHeight / 9
            }, 0);
        }
    }, 100);


	$("#btn_font_menos").click(function() {
	    $(".dpt").css("font-size", "-=1");
	});
	$("#btn_font_mais").click(function() {
	    $(".dpt").css("font-size", "+=1");
	});

    $(".dpt").each(function() {
        var nivel = parseInt($(this).attr('nivel'));

        $(this).css('z-index', 20-nivel)

    });
});
