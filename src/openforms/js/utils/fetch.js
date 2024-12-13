import {APIError, NotAuthenticatedError, ValidationErrors} from './exception';
import {onResponseHook} from './session-expiry';

export const API_BASE_URL = process.env.API_BASE_URL;

const fetchDefaults = {
  credentials: 'same-origin', // required for Firefox 60, which is used in werkplekken
};

const normalizeUrl = url => {
  if (!API_BASE_URL) return url;
  // make URL fully qualified, which makes the mocks work on Github pages, Chromatic and
  // local dev environments.
  try {
    new URL(url);
  } catch (exc) {
    // URLs like '/api/v2/foo' cannot be parsed as a URL without base, so we know
    // we are missing the prefix
    url = `${API_BASE_URL}${url}`;
  }
  return url;
};

const fetch = async (url, opts) => {
  url = normalizeUrl(url);
  const response = await window.fetch(normalizeUrl(url), opts);
  onResponseHook(response);
  return response;
};

const apiCall = fetch;

// TODO: throwOn400 is legacy and should be removed in the future
const throwForStatus = (response, responseData = null, throwOn400 = true) => {
  if (response.ok) return;

  switch (response.status) {
    case 400: {
      if (throwOn400) {
        throw new ValidationErrors(
          'Call did not validate on the backend',
          responseData?.invalidParams
        );
      }
      break;
    }
    case 401: {
      throw new NotAuthenticatedError('User not or no longer authenticated');
      break;
    }
    default: {
      throw new APIError(`Error ${response.status} from backend`, response.status);
      break;
    }
  }
};

const get = async (url, params = {}) => {
  if (Object.keys(params).length) {
    const searchparams = new URLSearchParams(params);
    url += `?${searchparams}`;
  }
  const response = await fetch(url);
  // TODO: this should use:
  //  throwForStatus(response);
  if (!response.ok) {
    return {
      ok: response.ok,
      status: response.status,
    };
  } else {
    const data = await response.json();
    return {
      ok: response.ok,
      status: response.status,
      data: data,
    };
  }
};

const _unsafe = async (method = 'POST', url, csrftoken, data = {}, throwOn400 = false) => {
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
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.indexOf('application/json') !== -1) {
    responseData = await response.json();
  }
  throwForStatus(response, responseData, throwOn400);
  return {
    ok: response.ok,
    status: response.status,
    data: responseData,
  };
};

const post = async (url, csrftoken, data = {}, throwOn400 = false) => {
  const resp = await _unsafe('POST', url, csrftoken, data, throwOn400);
  return resp;
};

const put = async (url, csrftoken, data = {}, throwOn400 = false) => {
  const resp = await _unsafe('PUT', url, csrftoken, data, throwOn400);
  return resp;
};

const patch = async (url, csrftoken, data = {}, throwOn400 = true) => {
  const resp = await _unsafe('PATCH', url, csrftoken, data, throwOn400);
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
  const response = await fetch(url, opts);
  throwForStatus(response);
  return response;
};

export {ValidationErrors};
export {get, post, put, patch, apiDelete, apiCall};
