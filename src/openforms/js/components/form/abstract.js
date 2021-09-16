import {BuilderUtils, Utils} from 'formiojs';

import DEFAULT_TABS, {BASIC, ADVANCED, VALIDATION, REGISTRATION} from './edit/tabs';

export const defineEditFormTabs = (ComponentClass, tabs) => {
    ComponentClass.editForm = function () {
        return {
            components: tabs
        };
    };
};

export const defineCommonEditFormTabs = (ComponentClass, extra = []) => {
    console.debug(`
        defineCommonEditFormTabs is deprecated, please use the 'formio_module' system
        instead to register your component overrides. See 'components/form/time.js'
        for an example.
    `);

    // insert the extras here
    const BASIC_TAB = {
        ...BASIC,
        components: [
            ...BASIC.components,
            ...extra,
        ]
    };
    const TABS = {
        ...DEFAULT_TABS,
        components: [
            BASIC_TAB,
            ADVANCED,
            VALIDATION,
            REGISTRATION,
        ]
    };
    defineEditFormTabs(ComponentClass, [TABS]);
};
