import debounce from 'lodash/debounce';
import {createGlobalstate} from 'state-pool';

const SessionExpiresInHeader = 'X-Session-Expires-In';

let sessionExpiresAt = createGlobalstate({
    date: null,
    numSeconds: null,
    authFailure: false,
});

const updateSessionExpiry = (seconds, authFailed=false) => {
    const newExpiry = new Date();
    newExpiry.setSeconds(newExpiry.getSeconds() + seconds);
    sessionExpiresAt.updateValue((expiry) => {
        expiry.date = newExpiry;
        expiry.numSeconds = seconds;
        expiry.authFailure = authFailed;
    });
};

const debouncedUpdate = debounce(updateSessionExpiry, 200);

const onResponseHook = (response) => {
    const sessionExpiry = response.headers.get(SessionExpiresInHeader);
    if (sessionExpiry) {
        const numSeconds = parseInt(sessionExpiry, 10);
        const authFailed = response.status === 401;
        debouncedUpdate.cancel();
        debouncedUpdate(numSeconds, authFailed);
    }
}

export {
    SessionExpiresInHeader,
    sessionExpiresAt,
    onResponseHook,
};
