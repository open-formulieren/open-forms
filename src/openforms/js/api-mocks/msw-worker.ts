import {setupWorker} from 'msw/browser';

// set up API mock worker
const mswWorker = setupWorker();

export default mswWorker;
