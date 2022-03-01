import React from 'react';
import ReactDOM from 'react-dom';
import {IntlProvider} from 'react-intl';

import jsonScriptToVar from '../../../utils/json-script'
import {getIntlProviderProps} from '../i18n';
import PluginConfiguration from './PluginConfiguration';

const CLASSNAME = '.plugin-config-react';

document.addEventListener('DOMContentLoaded', async () => {
    const nodes = document.querySelectorAll(CLASSNAME);
    if (!nodes.length) return;

    const intlProviderProps = await getIntlProviderProps();

    for (const node of nodes) {
        const {name, value} = node.dataset;

        const attrs = jsonScriptToVar(`${name}-attrs-react`);
        const modulesAndPlugins = jsonScriptToVar(`${name}-modules-and-plugins`);

        const mountNode = node.querySelector(`${CLASSNAME}__widget`);
        const hiddenInput = node.querySelector(`${CLASSNAME}__input`);

        const onChange = (newConfiguration) => {
            hiddenInput.value = JSON.stringify(newConfiguration);
        };

        ReactDOM.render(
            <React.StrictMode>
                <IntlProvider {...intlProviderProps}>
                    <PluginConfiguration
                        name={name}
                        modulesAndPlugins={modulesAndPlugins}
                        value={JSON.parse(value) || {}}
                        onChange={onChange} />
                </IntlProvider>
            </React.StrictMode>,
            mountNode
        );
    }
});

