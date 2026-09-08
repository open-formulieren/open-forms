import {Suspense, lazy} from 'react';

const LazyJSONEditor = lazy(async () => {
  const monacoJsonEditor = await import('@open-formulieren/monaco-json-editor');
  return {default: monacoJsonEditor.JSONEditor};
});

const JSONEditor = props => (
  <Suspense fallback="Loading editor...">
    <LazyJSONEditor {...props} />
  </Suspense>
);

export default JSONEditor;
