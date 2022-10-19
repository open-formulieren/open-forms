import {Formio} from 'react-formio';
import './initTinymce';
import './components';
import OpenForms from './formio_module';

// use custom component overrides
Formio.use(OpenForms);

const DebugPlugin = {
  priority: 0,
  preRequest: requestArgs => {
    console.log(requestArgs);
  },
};

// Formio.registerPlugin(DebugPlugin, 'debug');
