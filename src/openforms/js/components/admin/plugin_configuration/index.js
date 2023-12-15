import React from 'react';
import {createRoot} from 'react-dom/client';

import AppWrapper, {getWrapperProps} from 'components/admin/AppWrapper';
import {onLoaded} from 'utils/dom';
import jsonScriptToVar from 'utils/json-script';

import PluginConfiguration from './PluginConfiguration';

const CLASSNAME = '.plugin-config-react';

const init = async () => {
  const nodes = document.querySelectorAll(CLASSNAME);
  if (!nodes.length) return;

  const wrapperProps = await getWrapperProps();

  for (const node of nodes) {
    const {name, value} = node.dataset;

    const modulesAndPlugins = jsonScriptToVar(`${name}-modules-and-plugins`);

    const mountNode = node.querySelector(`${CLASSNAME}__widget`);
    const hiddenInput = node.querySelector(`${CLASSNAME}__input`);
    const root = createRoot(mountNode);

    const onChange = newConfiguration => {
      hiddenInput.value = JSON.stringify(newConfiguration);
    };

    root.render(
      <AppWrapper {...wrapperProps}>
        <PluginConfiguration
          name={name}
          modulesAndPlugins={modulesAndPlugins}
          value={JSON.parse(value) || {}}
          onChange={onChange}
        />
      </AppWrapper>
    );
  }
};

onLoaded(init);
