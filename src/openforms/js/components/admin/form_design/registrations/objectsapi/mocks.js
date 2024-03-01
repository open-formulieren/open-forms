import {rest} from 'msw';

export const BASE_URL = process.env.SB_BASE_URL || '';

export const mockObjecttypesGet = objecttypes =>
  rest.get(`${BASE_URL}/api/v2/registration/plugins/objects-api/object-types`, (req, res, ctx) => {
    return res(ctx.json(objecttypes));
  });

export const mockObjecttypeVersionsGet = versions =>
  rest.get(
    `${BASE_URL}/api/v2/registration/plugins/objects-api/object-types/:uuid/versions`,
    (req, res, ctx) => {
      return res(ctx.json(versions));
    }
  );

export const mockObjecttypesError = () =>
  rest.all('*', (req, res, ctx) => {
    return res(ctx.status(500));
  });

export const mockTargetPathsPost = paths =>
  rest.post(`${BASE_URL}/api/v2/registration/plugins/objects-api/target-paths`, (req, res, ctx) => {
    return res(ctx.json(paths));
  });
