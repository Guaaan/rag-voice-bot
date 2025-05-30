// function changeLoginButtonText(buttons) {
//     for (var i = 0; i < buttons.length; i++) {
//         if (buttons[i].innerText === 'Continue with Azure-ad-b2c') {
//             buttons[i].innerHTML = '<img class="MuiButton-startIcon MuiButton-iconSizeMedium css-6xugel MuiSvgIcon-root login-logo" ' +
//                 'src="../public/b2c_logo.png" ' +
//                 'alt="Log in on Client SSO" ' +
//                 'role="presentation" >' +
//                 'Login with Client Portal';
//             }
//     }
// }

// function mutationObserverCallback(mutationsList, observer) {
//     var buttons = document.querySelectorAll('button');
//     if (buttons.length === 1) {
//         changeLoginButtonText(buttons);
//         observer.disconnect();
//     }
// }

// if (window.location.href.includes('login')) {
//     const observer = new MutationObserver(mutationObserverCallback);
//     const config = { childList: true, subtree: true };
//     observer.observe(document.body, config);
// }

// Guardar sesión en localStorage cuando se autentique
window.addEventListener('message', (event) => {
    if (event.data.type === 'CHAINLIT_AUTH_SUCCESS') {
        localStorage.setItem('chainlit_auth_token', event.data.token);
        localStorage.setItem('chainlit_user', JSON.stringify(event.data.user));
    }
});

// Función para verificar sesión almacenada
function checkStoredSession() {
    const token = localStorage.getItem('chainlit_auth_token');
    const user = JSON.parse(localStorage.getItem('chainlit_user'));
    
    if (token && user) {
        return {
            authenticated: true,
            user: user,
            token: token
        };
    }
    return { authenticated: false };
}