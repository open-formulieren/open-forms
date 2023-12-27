// via @open-formulieren/formio-builder
import ClassicEditor from '@open-formulieren/ckeditor5-build-classic';
import cssHasPseudo from 'css-has-pseudo/browser';
import {Formio} from 'react-formio';

import './components';
import OpenForms from './formio_module';
import './initTinymce';

// assign to global, so that Formio.requireLibrary doesn't load a different
// (incompatible) version from its own CDN. Formio looks for the global name `ClassicEditor`
// to determine whether the library was already loaded or not.
window.ClassicEditor = ClassicEditor;

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
