import {assert} from 'chai';
import {BLOCK_TOGGLE} from '../../../js/components/toggle/constants';
import {Toggle} from '../../../js/components/toggle/toggle';
import simulant from 'simulant';
import {delay} from '../../utils';


describe('Toggle', function () {
    beforeEach(() => {
        this.button = document.createElement('button');
        this.button.classList.add(BLOCK_TOGGLE);
        document.body.appendChild(this.button);

        this.target = document.createElement('div');
        this.target.classList.add('target');
        document.body.appendChild(this.target);

        this.clearTarget = document.createElement('div');
        this.clearTarget.classList.add('clear-target');
        document.body.appendChild(this.clearTarget);

        this.focusTarget = document.createElement('input');
        this.focusTarget.classList.add('focus-target');
        document.body.appendChild(this.focusTarget);

        this.link = document.createElement('a');
        this.link.classList.add(BLOCK_TOGGLE);
        this.link.classList.add('link');
        document.body.appendChild(this.link);
    });

    afterEach(() => {
        document.body.removeChild(this.button);
        document.body.removeChild(this.target);
        document.body.removeChild(this.clearTarget)
        document.body.removeChild(this.focusTarget);
        document.body.removeChild(this.link);
    });

    it('should construct', () => {
        assert.ok(new Toggle(this.button));
    });

    it('should have BLOCK_TOGGLE present in classList for detection' +
        'and should have data-toggle-target set to query selector for target ' +
        'and should have data-toggle-modifier set to modifier to toggle.', (done) => {
        this.button.dataset.toggleTarget = '.target';
        this.button.dataset.toggleModifier = 'on';
        new Toggle(this.button);

        delay()
        // Initial state.
            .then(() => assert.ok(this.target.classList.contains('target')))
            .then(() => assert.notOk(this.target.classList.contains('target--on')))

            // Click button.
            .then(() => simulant.fire(this.button, 'click'))
            .then(() => delay(100))

            // "On" state.
            .then(() => assert.ok(this.target.classList.contains('target')))
            .then(() => assert.ok(this.target.classList.contains('target--on')))

            // Click button.
            .then(() => simulant.fire(this.button, 'click'))
            .then(() => delay(100))

            // "Off" state.
            .then(() => assert.ok(this.target.classList.contains('target')))
            .then(() => assert.notOk(this.target.classList.contains('target--on')))

            // Done.
            .then(done, done)
        ;
    });

    it('could have data-toggle-clear-target set to query selector for node which click removes modifier.', (done) => {
        this.button.dataset.toggleTarget = '.target';
        this.button.dataset.toggleClearTarget = '.clear-target';
        this.button.dataset.toggleModifier = 'on';
        new Toggle(this.button);

        delay()
        // Initial state.
            .then(() => assert.ok(this.target.classList.contains('target')))
            .then(() => assert.notOk(this.target.classList.contains('target--on')))

            // Click clearTarget.
            .then(() => simulant.fire(this.clearTarget, 'click'))
            .then(() => delay(100))

            // "Off" state.
            .then(() => assert.ok(this.target.classList.contains('target')))
            .then(() => assert.notOk(this.target.classList.contains('target--on')))

            // Click button.
            .then(() => simulant.fire(this.button, 'click'))
            .then(() => delay(100))

            // "On" state.
            .then(() => assert.ok(this.target.classList.contains('target')))
            .then(() => assert.ok(this.target.classList.contains('target--on')))

            // Click clearTarget.
            .then(() => simulant.fire(this.clearTarget, 'click'))
            .then(() => delay(100))

            // "Off" state.
            .then(() => assert.ok(this.target.classList.contains('target')))
            .then(() => assert.notOk(this.target.classList.contains('target--on')))

            // Done.
            .then(done, done)
        ;
    });

    it('could have data-toggle-clear-target set to query selector for node which click removes modifier.', (done) => {
        this.button.dataset.toggleTarget = '.target';
        this.button.dataset.toggleClearTarget = '.clear-target';
        this.button.dataset.toggleModifier = 'on';
        new Toggle(this.button);

        delay()
        // Initial state.
            .then(() => assert.ok(this.target.classList.contains('target')))
            .then(() => assert.notOk(this.target.classList.contains('target--on')))

            // Click clearTarget.
            .then(() => simulant.fire(this.clearTarget, 'click'))
            .then(() => delay(100))

            // "Off" state.
            .then(() => assert.ok(this.target.classList.contains('target')))
            .then(() => assert.notOk(this.target.classList.contains('target--on')))

            // Click button.
            .then(() => simulant.fire(this.button, 'click'))
            .then(() => delay(100))

            // "On" state.
            .then(() => assert.ok(this.target.classList.contains('target')))
            .then(() => assert.ok(this.target.classList.contains('target--on')))

            // Click clearTarget.
            .then(() => simulant.fire(this.clearTarget, 'click'))
            .then(() => delay(100))

            // "Off" state.
            .then(() => assert.ok(this.target.classList.contains('target')))
            .then(() => assert.notOk(this.target.classList.contains('target--on')))

            // Done.
            .then(done, done)
        ;
    });

    it('could have data-toggle-focus-target set to query selector for node to focus on click.', (done) => {
        this.button.dataset.toggleTarget = '.focus-target';
        this.button.dataset.toggleFocusTarget = '.focus-target';
        this.button.dataset.toggleModifier = 'on';
        new Toggle(this.button);

        delay()
        // Initial state.
            .then(() => assert.notEqual(document.activeElement, this.focusTarget))

            // Click button.
            .then(() => simulant.fire(this.button, 'click'))
            .then(() => delay(100))

            // // "Focus" state.
            .then(() => assert.ok(document.activeElement.classList.contains('focus-target')))
            .then(() => assert.ok(document.activeElement.classList.contains('focus-target--on')))

            // Done.
            .then(done, done)
        ;
    });

    // This test fails since switching to jest
    it.skip('could have data-toggle-link-mode set to either "normal", "positive", "negative", "prevent" or "noprevent".', (done) => {
        this.link.dataset.toggleTarget = '.target';
        this.link.dataset.toggleModifier = 'on';
        const toggle = new Toggle(this.link);
        // const spy = sinon.spy(toggle, 'onClick');

        delay()
        // Initial state.
        // Normal and no href.
            .then(() => window.location.hash = '')
            .then(() => delete this.link.href)
            .then(() => this.link.dataset.toggleLinkMode = 'normal')
            .then(() => simulant.fire(this.link, 'click'))
            .then(() => assert.equal(window.location.hash, ''))

            // Normal and "#" href.
            .then(() => window.location.hash = '')
            .then(() => this.link.href = '#')
            .then(() => this.link.dataset.toggleLinkMode = 'normal')
            .then(() => simulant.fire(this.link, 'click'))
            .then(() => assert.equal(window.location.hash, ''))

            // Normal and "#foo" href.
            .then(() => window.location.hash = '')
            .then(() => this.link.href = '#foo1')
            .then(() => this.link.dataset.toggleLinkMode = 'normal')
            .then(() => simulant.fire(this.link, 'click'))
            .then(() => assert.equal(window.location.hash, '#foo1'))

            // Negative and off.
            .then(() => window.location.hash = '')
            .then(() => this.link.href = '#bar1')
            .then(() => this.link.dataset.toggleLinkMode = 'negative')
            .then(() => this.target.classList.remove('.target--on'))
            .then(() => simulant.fire(this.link, 'click'))
            .then(() => assert.equal(window.location.hash, '#bar1'))

            // Negative and on.
            .then(() => window.location.hash = '')
            .then(() => this.link.href = '#bar2')
            .then(() => this.link.dataset.toggleLinkMode = 'negative')
            .then(() => this.target.classList.add('.target--on'))
            .then(() => simulant.fire(this.link, 'click'))
            .then(() => assert.equal(window.location.hash, ''))


            // Positive and off.
            .then(() => window.location.hash = '')
            .then(() => this.link.href = '#bar2')
            .then(() => this.link.dataset.toggleLinkMode = 'positive')
            .then(() => this.target.classList.remove('.target--on'))
            .then(() => simulant.fire(this.link, 'click'))
            .then(() => assert.equal(window.location.hash, ''))

            // Positive and on.
            .then(() => window.location.hash = '')
            .then(() => this.link.href = '#bar3')
            .then(() => this.link.dataset.toggleLinkMode = 'positive')
            .then(() => this.target.classList.add('.target--on'))
            .then(() => simulant.fire(this.link, 'click'))
            .then(() => assert.equal(window.location.hash, '#bar3'))

            // Prevent.
            .then(() => window.location.hash = '#foo')
            .then(() => this.link.href = '#baz1')
            .then(() => this.link.dataset.toggleLinkMode = 'prevent')
            .then(() => simulant.fire(this.link, 'click'))
            .then(() => assert.equal(window.location.hash, '#foo'))

            // Noprevent.
            .then(() => window.location.hash = '#baz2')
            .then(() => this.link.href = '#')
            .then(() => this.link.dataset.toggleLinkMode = 'noprevent')
            .then(() => simulant.fire(this.link, 'click'))
            .then(() => assert.equal(window.location.hash, ''))

            // Done.
            .then(done, done)
        ;
    });

    it('could have data-toggle-operation set to either "add" or "remove", see this.toggle().', (done) => {
        this.button.dataset.toggleTarget = '.target';
        this.button.dataset.toggleModifier = 'on';
        new Toggle(this.button);

        delay()
        // Remove.
            .then(() => this.target.classList.add('target--on'))
            .then(() => this.button.dataset.toggleOperation = 'remove')
            .then(() => simulant.fire(this.button, 'click'))
            .then(() => delay(100))
            .then(() => assert.notOk(this.target.classList.contains('target--on')))
            .then(() => simulant.fire(this.button, 'click'))
            .then(() => delay(100))
            .then(() => assert.notOk(this.target.classList.contains('target--on')))

            // Add.
            .then(() => this.target.classList.remove('target--on'))
            .then(() => this.button.dataset.toggleOperation = 'add')
            .then(() => simulant.fire(this.button, 'click'))
            .then(() => delay(100))
            .then(() => assert.ok(this.target.classList.contains('target--on')))
            .then(() => simulant.fire(this.button, 'click'))
            .then(() => delay(100))
            .then(() => assert.ok(this.target.classList.contains('target--on')))


            // Done.
            .then(done, done)
        ;
    });
});
