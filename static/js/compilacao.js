function initTinymce() {

	tinymce.init({
		mode : "textareas",
		force_br_newlines : false,
		force_p_newlines : false,
		forced_root_block : '',
		plugins: ["table save code"],
		menubar: "edit format table tools",
		toolbar: "save | undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent",
		tools: "inserttable",
		save_onsavecallback: onSubmitEditForm,
		border_css: "/static/styles/compilacao_tinymce.css",
		content_css: "/static/styles/compilacao_tinymce.css"
	});
}

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
