import {createGlobalstate} from 'state-pool';

const SessionExpiresInHeader = 'X-Session-Expires-In';

let sessionExpiresAt = createGlobalstate({
    date: null,
    numSeconds: null,
    authFailure: false,
});

const updateSesionExpiry = (seconds, authFailed=false) => {
    const newExpiry = new Date();
    newExpiry.setSeconds(newExpiry.getSeconds() + seconds);
    sessionExpiresAt.updateValue((expiry) => {
        expiry.date = newExpiry;
        expiry.numSeconds = seconds;
        expiry.authFailure = authFailed;
    });
    // TODO: we can schedule a message to be set if expiry is getting close
};

const onResponseHook = (response) => {
    const sessionExpiry = response.headers.get(SessionExpiresInHeader);
    if (sessionExpiry) {
        const numSeconds = parseInt(sessionExpiry, 10);
        const authFailed = response.status === 401;
        updateSesionExpiry(numSeconds, authFailed);
    }
}

export {
    SessionExpiresInHeader,
    sessionExpiresAt,
    onResponseHook,
};
