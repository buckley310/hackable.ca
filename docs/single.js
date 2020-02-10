let userinfo;

function loadingError(e) {
    alert(e);
}

function api(path, args = false) {
    if (!localStorage.getItem('apiEndpoint'))
        return fetch('/api/' + path, { cache: "no-cache" }).then(x => x.json());

    let apiURL = localStorage.getItem('apiEndpoint');
    return (args ?
        fetch(apiURL + path, { cache: "no-cache", method: 'POST', body: JSON.stringify(args) }) :
        fetch(apiURL + path, { cache: "no-cache" })
    ).then(x => x.json());
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

    api('/userinfo').then(function (x) {
        userinfo = x;

        unhideElements(userinfo.username ?
            ['tab_profile', 'tab_logout'] :
            ['tab_login', 'tab_register']);

        if (window['contentInit']) contentInit();

    }).catch(loadingError);
});