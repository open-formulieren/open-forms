import cssHasPseudo from 'css-has-pseudo/browser';
import {Formio} from 'react-formio';

import './components';
import OpenForms from './formio_module';
import './initTinymce';

// use custom component overrides
Formio.use(OpenForms);

const DebugPlugin = {
  priority: 0,
  preRequest: requestArgs => {
    console.log(requestArgs);
  },
};

// Formio.registerPlugin(DebugPlugin, 'debug');

// set up :has polyfill;
cssHasPseudo(document);
