import {Suspense, lazy} from 'react';

const LazyJSONEditor = lazy(() => import('./LazyJSONEditor'));

const JSONEditor = props => (
  <Suspense fallback="Loading editor...">
    <LazyJSONEditor {...props} />
  </Suspense>
);

export default JSONEditor;
