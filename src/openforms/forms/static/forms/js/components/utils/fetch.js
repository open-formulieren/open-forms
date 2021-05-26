const fetchDefaults = {
    credentials: 'same-origin',  // required for Firefox 60, which is used in werkplekken
};

const fetch = (url, opts) => {
    const options = Object.assign({}, fetchDefaults, opts);
    return window.fetch(url, options);
};

const apiCall = fetch;

const get = async (url, params={}) => {
    if (Object.keys(params).length) {
        const searchparams = new URLSearchParams(params);
        url += `?${searchparams}`;
    }
    const response = await fetch(url);
    const data = await response.json();
    return data;
};

const _unsafe = async (method = 'POST', url, csrftoken, data = {}) => {
    const opts = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify(data),
    };
    const response = await fetch(url, opts);
    const responseData = await response.json();
    return {
        ok: response.ok,
        status: response.status,
        data: responseData,
    };
};

const post = async (url, csrftoken, data = {}) => {
    const resp = await _unsafe('POST', url, csrftoken, data);
    return resp;
};

const put = async (url, csrftoken, data = {}) => {
    const resp = await _unsafe('PUT', url, csrftoken, data);
    return resp;
};

export {get, post, put, apiCall};
