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

function textoMultiVigente(item) {
	$(".cp .tipo-vigencias a").removeClass("selected")
	$(item).addClass("selected")
	$(".desativado").removeClass("displaynone");
	$(".link_alterador").removeClass("displaynone");
}

function textoVigente(item, link) {
	$(".cp .tipo-vigencias a").removeClass("selected")
	$(item).addClass("selected")
	$(".desativado").addClass("displaynone");
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
