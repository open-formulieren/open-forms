import React from 'react';


const FormDefinitionsContext = React.createContext([]);
FormDefinitionsContext.displayName = 'FormDefinitionsContext';

const PluginsContext = React.createContext({availablePlugins: {}, selectedPlugins: []});
PluginsContext.displayName = 'PluginsContext';

const TinyMceContext = React.createContext('');
TinyMceContext.displayName = 'TinyMceContext';

export { FormDefinitionsContext, PluginsContext, TinyMceContext };
