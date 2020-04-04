let userinfo;

function loadingError(e) {
    console.error(e);
    document.getElementById('errorText').textContent = 'An error was encountered accessing the API';
}

function api(path, args = false) {
    let st = localStorage.getItem('sessionToken');
    return fetch('http://127.0.0.1:5000/' + path, {
        cache: "no-cache",
        method: args ? 'POST' : 'GET',
        body: args ? JSON.stringify(args) : null,
        headers: st ? { 'X-Sesid': st } : {}
    }).then(x => x.json());
}

function unhideElements(elems) {
    for (let c of elems)
        document.getElementById(c).style.display = '';
}

window.addEventListener('load', function () {

    if (!localStorage.getItem('sessionToken')) {

        unhideElements(['tab_login', 'tab_register']);
        if (window['contentInit']) contentInit();
        return;
    }

    api('userinfo').then(function (x) {
        userinfo = x;

        unhideElements(userinfo.username ?
            ['tab_profile', 'tab_logout'] :
            ['tab_login', 'tab_register']);

        if (window['contentInit']) contentInit();

    }).catch(loadingError);
});