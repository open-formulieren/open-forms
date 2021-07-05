import React from 'react';


const FormDefinitionsContext = React.createContext([]);
FormDefinitionsContext.displayName = 'FormDefinitionsContext';

const PluginsContext = React.createContext({availablePlugins: {}, selectedPlugins: []});
PluginsContext.displayName = 'PluginsContext';

export { FormDefinitionsContext, PluginsContext };
