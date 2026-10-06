import mswWorker from '@/api-mocks/msw-worker';
import {afterEach, beforeAll} from 'vitest';

beforeAll(async () => {
  // set up HTTP mocks
  await mswWorker.start({
    onUnhandledRequest: 'error',
    quiet: true,
  });
});

afterEach(() => mswWorker.resetHandlers());
