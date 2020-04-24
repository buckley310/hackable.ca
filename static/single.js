let userinfo;

function loadingError(e) {
    console.error(e);
    document.getElementById('errorText').textContent = 'An error was encountered accessing the API';
}

function api(path, args = false) {
    let headers = {};

    let st = localStorage.getItem('sessionToken');
    if (st)
        headers['X-Sesid'] = st;

    if (args)
        headers['Content-Type'] = 'application/json';

    return fetch('http://127.0.0.1:5000/' + path, {
        cache: "no-cache",
        method: args ? 'POST' : 'GET',
        body: args ? JSON.stringify(args) : null,
        headers: headers
    }).then(x => x.json());
}

function unhideElements(elems) {
    for (let c of elems)
        document.getElementById(c).style.display = '';
}

function insertChallengeCards(targetElem, userId) {
    let challengeDetails = function (challenge) {
        let mod = document.createElement('div');
        mod.classList.add('modalBG');
        mod.addEventListener('click', function (e) {
            if (e.target === this || e.target.classList.contains('modalClose'))
                document.body.removeChild(this);
        });
        mod.innerHTML = `<div class="modalBox">
                            <div class="modalClose">&#10060;</div>
                            <div style="margin:10px">
                                 <h3>${challenge.title}</h3>
                                 ${challenge.text}<br><br>
                                 <b>Points</b>: ${challenge.points}<br>
                                 <b>Solves</b>: ${challenge.solves}<br>
                            </div>
                         </div>`;
        document.body.appendChild(mod);
    };
    api('challenges?uid=' + userId).then(function (j) {
        let sections = {};
        for (let chal of j) {
            if (!sections[chal['category']]) {
                let sectionTitle = document.createElement('div');
                sectionTitle.textContent = chal['category'];
                sectionTitle.style.fontSize = '1.5em';
                targetElem.appendChild(sectionTitle);

                let sectionDiv = document.createElement('div');
                sectionDiv.classList.add('challengeSection');
                sections[chal['category']] = sectionDiv;
                targetElem.appendChild(sectionDiv);
            }
            let card = document.createElement('div');
            card.classList.add('challengeCard')
            card.style.backgroundColor = chal.solved ? "#28a745" : "#dc3545";
            card.innerHTML = `<br><b>${chal.title}</b>
                               <br>${chal.points} points<br><br>`;
            card.onclick = () => challengeDetails(chal);
            sections[chal['category']].appendChild(card);
        }
    }).catch(loadingError);
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