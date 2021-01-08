import { parse, serialize } from "uri-js";

const fetchDefaults = {
    credentials: 'same-origin', // required for Firefox 60, which is used in werkplekken
};

const apiCall = (url, opts) => {
    const options = { ...fetchDefaults, ...opts };
    const targetUrl = serialize({
      ...parse(url),
      scheme: undefined,
      host: undefined,
      port: undefined,
    });
    return window.fetch(targetUrl, options);
};

const get = async (url, params = {}, multiParams = []) => {
    let searchParams = new URLSearchParams();
    if (Object.keys(params).length) {
        searchParams = new URLSearchParams(params);
    }
    if (multiParams.length > 0) {
        multiParams.forEach((param) => {
            const paramName = Object.keys(param)[0]; // param={foo: bar}
            searchParams.append(paramName, param[paramName]);
        });
    }
    url += `?${searchParams}`;
    const response = await apiCall(url);
    const data = await response.json();
    return data;
};

const _unsafe = async (method = 'POST', url, data = {}) => {
    const csrfTokenCookie = await window.cookieStore.get('csrftoken');
    const csrftoken = csrfTokenCookie.value;
    const opts = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify(data),
    };
    const response = await apiCall(url, opts);
    const responseData = await response.json();
    return {
        ok: response.ok,
        status: response.status,
        data: responseData,
    };
};

const post = async (url, data = {}) => {
    const resp = await _unsafe('POST', url, data);
    return resp;
};

const patch = async (url, data = {}) => {
    const resp = await _unsafe('PATCH', url, data);
    return resp;
};

const put = async (url, data = {}) => {
    const resp = await _unsafe('PUT', url, data);
    return resp;
};

const destroy = async (url) => {
    const csrfTokenCookie = await window.cookieStore.get('csrftoken');
    const csrftoken = csrfTokenCookie.value;
    const opts = {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrftoken,
        },
    };
    const response = await apiCall(url, opts);
    if (!response.ok) {
        const responseData = await response.json();
        console.error('Delete failed', responseData);
        throw new Error('Delete failed');
    }
};

export {
    apiCall, get, post, put, patch, destroy,
};
