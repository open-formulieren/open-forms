import {assert} from 'chai';
import {FormIOForm} from '../../../js/components/formio_form/formio_form';
import sinon from 'sinon';

const FIXTURES = {
    FORM: {
        URL: '/api/v1/forms/1111111-2222-3333-4444-555555555555',
        GET: `{ 
            "url": "/api/v1/forms/1111111-2222-3333-4444-555555555555",
            "uuid": "1111111-2222-3333-4444-555555555555",
            "steps": [
                {
                    "index": 1,
                    "uuid": "2222222-3333-4444-5555-666666666666",
                    "configuration": {}
                },
                {
                    "index": 2,
                    "uuid": "3333333-4444-5555-6666-777777777777",
                    "configuration": {}
                }
            ],
            "user_current_step": {
                "uuid": "2222222-3333-4444-5555-666666666666"
            }
        }`,
    },
    FORM_STEP_1: {
        URL: '/api/v1/forms/1111111-2222-3333-4444-555555555555/steps/2222222-3333-4444-5555-666666666666',
        GET: `{
            "index": 1,
            "uuid": "2222222-3333-4444-5555-666666666666",
            "configuration": {
                "components": [
                    {
                        "label": "Voornaam",
                        "key": "first-name",
                        "type": "textfield",
                        "id": "first-name"
                    }
                ]
            }
        }`,
    },
    FORM_STEP_2: {
        URL: '/api/v1/forms/1111111-2222-3333-4444-555555555555/steps/3333333-4444-5555-6666-777777777777',
        GET: `{
            "index": 2,
            "uuid": "3333333-4444-5555-6666-777777777777",
            "configuration": {}
        }`,
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
        this.form.dataset.formId = '1111111-2222-3333-4444-555555555555';
        document.body.appendChild(this.form);

        this.formBody = document.createElement('div');
        this.formBody.classList.add('formio-form__body');
        this.form.appendChild(this.formBody);

        this.placeholder = document.createElement('p');
        this.placeholder.classList.add('body');
        document.body.appendChild(this.placeholder);

        // XHR.
        this.server = sinon.createFakeServer();
        Object.values(FIXTURES).forEach(fixture => {
            Object.keys(fixture)
                .filter(key => ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT'].indexOf(key) > -1)
                .forEach(method => this.server.respondWith(method, fixture.URL, fixture[method]))
            ;
        });
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

    it('should get the FormStep instance based on current step.', (done) => {
        new FormIOForm(this.form);
        delay()
            .then(() => this.server.respond())
            .then(delay)
            .then(() => this.server.respond())
            .then(delay)
            .then(() => assert.equal(this.server.requests[2].method, 'GET'))
            .then(() => assert.equal(this.server.requests[2].url, FIXTURES.FORM_STEP_1.URL))
            .then(done, done);
    });

    it('should get the FormStep instance based on step URL.', (done) => {
        history.pushState({}, '', '/1111111-2222-3333-4444-555555555555/2');
        const form = new FormIOForm(this.form);

        delay()
            .then(() => this.server.respond())
            .then(delay)
            .then(() => this.server.respond())
            .then(delay)
            .then(() => assert.equal(this.server.requests[2].method, 'GET'))
            .then(() => assert.equal(this.server.requests[2].url, FIXTURES.FORM_STEP_2.URL))
            .then(done, done);
    });

    it('should update the history url based on received step.', (done) => {
        history.pushState({}, '', '/1111111-2222-3333-4444-555555555555/2');
        const form = new FormIOForm(this.form);
        const spy = sinon.spy(history, 'pushState');

        delay()
            .then(() => this.server.respond())
            .then(delay)
            .then(() => this.server.respond())
            .then(delay)
            .then(() => this.server.respond())
            .then(delay)
            .then(() => assert.ok(spy.calledOnce))
            .then(() => assert.equal(spy.firstCall.args[2], '/1111111-2222-3333-4444-555555555555/2'))
            .then(() => spy.restore())
            .then(done, done);
    });

    it('should mount an empty form.', (done) => {
        history.pushState({}, '', '/1111111-2222-3333-4444-555555555555/1');
        new FormIOForm(this.form);

        delay()
            .then(() => this.server.respond())
            .then(delay)
            .then(() => this.server.respond())
            .then(delay)
            .then(() => this.server.respond())
            .then(delay)
            .then(() => assert.ok(this.form.querySelector('.formio-form')))
            .then(done, done);
    });

    it('should render the component(s) returned by the API.', (done) => {
        history.pushState({}, '', '/1111111-2222-3333-4444-555555555555/1');
        const form = new FormIOForm(this.form);

        delay()
            .then(() => this.server.respond())
            .then(delay)
            .then(() => this.server.respond())
            .then(delay)
            .then(() => this.server.respond())
            .then(delay)
            .then(delay)
            .then(() => assert.equal(this.form.querySelector('.label').textContent.trim(), 'Voornaam'))
            .then(() => assert.ok(this.form.querySelector('.input')))
            .then(done, done);
    });

    it('should render the component(s) returned by the window.popstate event.', (done) => {
        history.pushState({}, '', '/1111111-2222-3333-4444-555555555555/1');
        const form = new FormIOForm(this.form);
        const spy = sinon.stub(form, 'render');
        const event = document.createEvent('CustomEvent');
        event.initEvent('popstate');
        event.state = {
            formStep: JSON.parse(FIXTURES.FORM_STEP_1.GET)
        };

        delay()
            .then(() => form.mount(event.state))
            .then(delay)
            .then(() => window.dispatchEvent(event))
            .then(() => assert.equal(spy.firstCall.args[0], event.state))
            .then(() => spy.restore())
            .then(done, done);
    });
});
