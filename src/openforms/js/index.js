import ClassicEditor from '@open-formulieren/formio-builder/components/CKEditor';
import cssHasPseudo from 'css-has-pseudo/browser';

import './components';
import './initTinymce';

// assign to global, so that Formio.requireLibrary doesn't load a different
// (incompatible) version from its own CDN. Formio looks for the global name `ClassicEditor`
// to determine whether the library was already loaded or not.
window.ClassicEditor = ClassicEditor;

// set up :has polyfill;
cssHasPseudo(document);
