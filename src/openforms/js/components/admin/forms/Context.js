import React from 'react';

const PrefixContext = React.createContext('');
const ComponentsContext = React.createContext([]);

PrefixContext.displayName = 'PrefixContext';
ComponentsContext.displayName = 'ComponentsContext';

export { PrefixContext, ComponentsContext };
