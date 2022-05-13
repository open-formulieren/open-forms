import {onResponseHook} from './session-expiry';

const fetchDefaults = {
    credentials: 'same-origin',  // required for Firefox 60, which is used in werkplekken
};


class ValidationErrors extends Error {
    constructor(message, errors) {
        super(message);
        this.errors = errors;
    }
}
Object.defineProperty(ValidationErrors.prototype, 'name', {
    value: 'ValidationErrors',
});


const fetch = async (url, opts) => {
    const options = Object.assign({}, fetchDefaults, opts);
    const response = await window.fetch(url, options);
    onResponseHook(response);
    return response;
};

const apiCall = fetch;

const get = async (url, params={}) => {
    if (Object.keys(params).length) {
        const searchparams = new URLSearchParams(params);
        url += `?${searchparams}`;
    }
    const response = await fetch(url);
    if (!response.ok) {
        return {
            ok: response.ok,
            status: response.status
        };
    } else {
        const data = await response.json();
        return {
            ok: response.ok,
            status: response.status,
            data: data
        };
    }
};

const _unsafe = async (method = 'POST', url, csrftoken, data = {}, throwOn400=false) => {
    const opts = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify(data),
    };
    const response = await fetch(url, opts);

    let responseData = null;
    // Check if the response contains json data
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.indexOf("application/json") !== -1) {
        responseData = await response.json();
    }

    if (response.status === 400 && throwOn400) {
        throw new ValidationErrors(
            'Call did not validate on the backend',
            responseData.invalidParams,
        );
    }

    return {
        ok: response.ok,
        status: response.status,
        data: responseData,
    };
};

const post = async (url, csrftoken, data = {}, throwOn400=false) => {
    const resp = await _unsafe('POST', url, csrftoken, data, throwOn400);
    return resp;
};

const put = async (url, csrftoken, data = {}, throwOn400=false) => {
    const resp = await _unsafe('PUT', url, csrftoken, data, throwOn400);
    return resp;
};

const apiDelete = async (url, csrftoken) => {
    const opts = {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
    };
    return await fetch(url, opts);
};

export {ValidationErrors};
export {get, post, put, apiDelete, apiCall};
