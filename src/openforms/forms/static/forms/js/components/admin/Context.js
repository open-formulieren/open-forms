import React from 'react';


const FormDefinitionsContext = React.createContext([]);
FormDefinitionsContext.displayName = 'FormDefinitionsContext';

const AuthenticationPluginsContext = React.createContext([]);
AuthenticationPluginsContext.displayName = 'AuthenticationPluginsContext';

export { FormDefinitionsContext, AuthenticationPluginsContext };
