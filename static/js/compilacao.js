function SetCookie(cookieName,cookieValue,nDays) {
    var today = new Date();
    var expire = new Date();
    if (nDays==null || nDays==0) nDays=1;
    expire.setTime(today.getTime() + 3600000*24*nDays);
    document.cookie = cookieName+"="+escape(cookieValue)
    + ";expires="+expire.toGMTString();
}

function ReadCookie(cookieName) {
    var theCookie=" "+document.cookie;
    var ind=theCookie.indexOf(" "+cookieName+"=");
    if (ind==-1) ind=theCookie.indexOf(";"+cookieName+"=");
    if (ind==-1 || cookieName=="") return "";
    var ind1=theCookie.indexOf(";",ind+1);
    if (ind1==-1) ind1=theCookie.length;
    return unescape(theCookie.substring(ind+cookieName.length+2,ind1));
}

function insertWaitAjax(element) {
    //jQuery(element).append('<div style="text-align:center;"><img src="/static/img/ajax-loader.gif"></div>');
    jQuery(element).append('<div style="text-align:center;"><i style="font-size: 200%;"class="fa fa-refresh fa-spin"></i></div>');
}
