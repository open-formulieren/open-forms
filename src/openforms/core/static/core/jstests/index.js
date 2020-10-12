/** Include tests */
let testsContext = require.context('./', true, /\.spec\.js$/);
testsContext.keys().forEach(testsContext);

/** Include sources */
let sourceContext = require.context('../js/', true, /\.js$/);
sourceContext.keys().forEach(sourceContext);
