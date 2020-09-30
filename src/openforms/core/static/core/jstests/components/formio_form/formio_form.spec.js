import {assert} from 'chai';
import {FormIOForm} from '../../../js/components/formio_form/formio_form';
import sinon from 'sinon';

const FIXTURES = {
    FORM: {
        URL: '/api/v1/forms/foo',
        GET: `{ 
            "url": "/api/v1/forms/foo",
            "slug": "foo",
            "user_current_step": {
                "index": 1
            }
        }`,
    },
    FORM_STEP: {
        URL: '/api/v1/forms/foo/steps/1',
        GET: `{}`,
    },
    SUBMISSIONS: {
        URL: '/api/v1/submissions/',
        POST: `{}`,
    }
};

/**
 * Returns Promise which resolves in "timeout" milliseconds (1000 equals 1 second).
 * @param {number} [timeout=0] The timeout in milliseconds after which the Promise should resolve.
 * A value of 0 (default) causes the Promise to resolve at the end of the event loop.
 * @return {Promise}
 */
export const delay = (timeout = 0) => {
    return new Promise(resolve => {
        setTimeout(resolve, timeout);
    });
};

describe('FormIOForm', function () {
    beforeEach(() => {
        // DOM.
        this.form = document.createElement('form');
        this.form.classList.add('formio-form');
        this.form.classList.add('form');
        this.form.dataset.formSlug = 'foo';
        document.body.appendChild(this.form);

        this.formBody = document.createElement('div');
        this.formBody.classList.add('formio-form__body');
        this.form.appendChild(this.formBody);

        this.placeholder = document.createElement('p');
        this.placeholder.classList.add('body');
        document.body.appendChild(this.placeholder);

        // XHR.
        this.server = sinon.createFakeServer();
        this.server.respondWith('GET', FIXTURES.FORM.URL, FIXTURES.FORM.GET);
        this.server.respondWith('POST', FIXTURES.SUBMISSIONS.URL, FIXTURES.SUBMISSIONS.POST);

    });

    afterEach(() => {
        // DOM.
        this.form.removeChild(this.formBody);
        document.body.removeChild(this.form);

        // XHR.
        this.server.restore();

    });

    it('should construct', () => {
        assert.ok(new FormIOForm(this.form));
    });

    it('should get the Form instance.', (done) => {
        new FormIOForm(this.form);

        delay()
            .then(() => assert.equal(this.server.requests[0].method, 'GET'))
            .then(() => assert.equal(this.server.requests[0].url, FIXTURES.FORM.URL))
            .then(done, done);
    });

    it('should get/create the Submission instance.', (done) => {
        new FormIOForm(this.form);

        delay()
            .then(() => this.server.respond())
            .then(delay)
            .then(() => assert.equal(this.server.requests[1].method, 'POST'))
            .then(() => assert.equal(this.server.requests[1].url, '/api/v1/submissions/'))
            .then(done, done);
    });

    it('should get the FormStep instance.', (done) => {
        new FormIOForm(this.form);
        delay()
            .then(() => this.server.respond())
            .then(delay)
            .then(() => this.server.respond())
            .then(delay)
            .then(() => assert.equal(this.server.requests[2].method, 'GET'))
            .then(() => assert.equal(this.server.requests[2].url, FIXTURES.FORM_STEP.URL))
            .then(done, done);
    });
});
