import BEM from 'bem.js';
import {TOGGLES} from './constants';


/**
 * Class for generic toggles.
 *
 * Toggle should have BLOCK_TOGGLE present in classList for detection.
 * Toggle should have data-toggle-target set to query selector for target.
 * Toggle should have data-toggle-modifier set to modifier to toggle.
 * Toggle could have data-toggle-clear-target set to query selector for node which click removes modifier.
 * Toggle could have data-toggle-focus-target set to query selector for node to focus on click.
 * Toggle could have data-toggle-link-mode set to either "normal", "positive", "negative", "prevent" or "noprevent", see this.onClick().
 * Toggle could have data-toggle-operation set to either "add" or "remove", see this.toggle().
 * @class
 */
export class Toggle {
    /**
     * Constructor method.
     * @param {HTMLElement} node
     */
    constructor(node) {
        /** @type {HTMLElement} */
        this.node = node;

        /** @type {HTMLElement[]} */
        this.clearTarget = this.getClearTargets();

        /** @type {string} */
        this.toggleModifier = this.node.dataset.toggleModifier;

        /** @type {(boolean|undefined)} */
        this.toggleMobileState = this.node.dataset.toggleMobileState ? this.node.dataset.toggleMobileState.toUpperCase() === 'TRUE' : undefined;

        this.restoreState();
        this.bindEvents();
    }

    /**
     * Binds events to callbacks.
     */
    bindEvents() {
        this.node.addEventListener('click', this.onClick.bind(this));

        this.clearTarget.forEach(ct =>
            ct.addEventListener('click', this.onClearClick.bind(this))
        );
    }

    /**
     * Callback for this.node click.
     *
     * Prevents default action (e.preventDefault()) based on target and this.node.dataset.toggleLinkMode value:
     * - "normal" (default): Prevent default on regular elements and links towards "#", pass all other links.
     * - "positive": Prevent default on regular elements, dont prevent links if this.getState() returns true.
     * - "negative": Prevent default on regular elements, dont prevent links if this.getState() returns false.
     * - "prevent": Always prevent default.
     * - "noprevent": Never prevent default.
     *
     * @param {MouseEvent} e
     */
    onClick(e) {
        let toggleLinkMode = this.node.dataset.toggleLinkMode || 'normal';

        if (toggleLinkMode === 'normal') {
            if (!e.target.getAttribute('href') || e.target.getAttribute('href') === '#') {
                e.preventDefault();
                e.stopPropagation();
            }
        } else if (toggleLinkMode === 'positive') {
            if (!e.target.href || !this.getState()) {
                e.preventDefault();
                e.stopPropagation();
            }
        } else if (toggleLinkMode === 'negative') {
            if (!e.target.href || this.getState()) {
                e.preventDefault();
                e.stopPropagation();
            }
        } else if (toggleLinkMode === 'prevent') {
            e.preventDefault();
            e.stopPropagation();
        } else if (toggleLinkMode === 'noprevent') {
            if (e.target.href || e.target.parentNode.href) {
                return;
            }
        }

        setTimeout(() => {
            this.toggle();
            this.saveState();
            this.focus();
        }, 100);
    }

    /**
     * Callback for this.clearTarget click.
     */
    onClearClick(e) {
        let clearTarget = e.target;
        const toggleTargets = this.getTargets();

        // Don't clear if clicked node is child of a target.
        while(clearTarget.parentNode) {
            clearTarget = clearTarget.parentNode;

            if (toggleTargets.indexOf(clearTarget) > -1) {
                return;
            }
        }

        this.toggle(false);
    }

    /**
     * Focuses this.node.dataset.toggleFocusTarget.
     */
    focus() {
        let querySelector = this.node.dataset.toggleFocusTarget;
        if (querySelector && this.getState()) {
            let target = document.querySelector(querySelector);
            target.focus();
        }
    }

    /**
     * Performs toggle.
     *
     * Toggle behaviour can optionally controlled by this.node.dataset.toggleOperation value.
     * - undefined (default): Toggles add/remove based on exp or presence of this.toggleModifier
     * - "add": Always add this.toggleModifier to targets.
     * - "remove": Always removes this.toggleModifier from targets.
     *
     * @param {boolean} [exp] If passed, add/removes this.toggleModifier based on exp.
     */
    toggle(exp = undefined) {
        if (this.node.dataset.toggleOperation === 'add') {
            exp = true;
        } else if (this.node.dataset.toggleOperation === 'remove') {
            exp = false;
        }

        let targets = this.getTargets();
        targets.forEach(target => {
            BEM.toggleModifier(target, this.toggleModifier, exp);
            this.dispatchEvent(target);
        });

        this.getExclusive()
            .filter(exclusive => targets.indexOf(exclusive) === -1)
            .forEach(exclusive => BEM.removeModifier(exclusive, this.toggleModifier));
    }

    /**
     * Dispatches "rh-toggle" event on target.
     * @param {HTMLElement} target
     */
    dispatchEvent(target) {
        const event = document.createEvent('Event');
        event.initEvent('rh-toggle', true, true);
        target.dispatchEvent(event);
    }

    /**
     * Returns the toggle state (whether this.node.toggleModifier is applied).
     * State is retrieved from first target.
     * @returns {(boolean|null)} Boolean is target is found and state is retrieved, null if no target has been found.
     */
    getState() {
        let referenceTarget = this.getTargets()[0];
        if (!referenceTarget) {
            return null;
        }

        return Boolean(BEM.hasModifier(referenceTarget, this.toggleModifier));
    }

    /**
     * Returns all the targets for this.node.
     * @returns {HTMLElement[]}
     */
    getTargets() {
        let selector = this.node.dataset.toggleTarget;
        return this.getRelated(selector);
    }

    /**
     * Retursn all the clear targets for this.node.
     * @return {HTMLElement[]}
     */
    getClearTargets() {
        const selector = this.node.dataset.toggleClearTarget;
        if (selector) {
            return this.getRelated(selector);
        }
        return [];
    }

    /**
     * Returns all the grouped "exclusive" toggles of this.node.
     * @returns {HTMLElement[]}
     */
    getExclusive() {
        let selector = this.node.dataset.toggleExclusive || '';
        return this.getRelated(selector);
    }

    /**
     * Splits selector by "," and query selects each part.
     * @param {string} selector Selector(s) (optionally divided by ",").
     * @return {HTMLElement[]} An array of all matched nodes.
     */
    getRelated(selector) {
        let targets = [];
        selector.split(',')
            .filter(selector => selector.length)
            .map(selector => String(selector).trim())
            .forEach(selector => {
                let parent = document;

                // Support "& " to represent this.node as parent for selector instead of document.
                if (selector.startsWith('&')) {
                    selector = selector.replace('&', '');

                    if (!selector.trim()) {
                        targets = [...targets, this.node];
                        return;

                    }
                    targets = [...targets, ...this.node.querySelectorAll(selector)];
                    return;
                }

                targets = [...targets, ...parent.querySelectorAll(selector)];
                return;
            });

        return targets;
    }

    /**
     * Saves state to localstorage.
     */
    saveState() {
        let id = this.node.id;
        let value = this.getState();

        if (typeof value !== 'boolean') {
            return;
        }

        if (id) {
            let key = `ToggleButton#${id}.modifierApplied`;
            try {
                localStorage.setItem(key, value);
            } catch (e) {
                console.warn(this, 'Unable to save state to localstorage');
            }
        }
    }

    /**
     * Restores state from localstorage.
     */
    restoreState() {
        if (this.toggleMobileState !== undefined && matchMedia('(max-width: 767px)').matches) {
            this.toggle(this.toggleMobileState);
            return;
        }

        let id = this.node.id;

        if (id) {
            let key = `ToggleButton#${id}.modifierApplied`;
            try {
                let value = localStorage.getItem(key) || false;
                this.toggle(value.toUpperCase() === 'TRUE');
            } catch (e) {
            }
        }
    }
}

// Start!
[...TOGGLES].forEach(node => new Toggle(node));
