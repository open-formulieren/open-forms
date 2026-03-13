import {checkVersionsCompatible} from './FormVersionsTable';

// showing a warning depends on the combination of the app and the current release
// test same versions and patch, minor and  major versions
test.each([
  ['3.3.4', '3.3.4', true],
  ['3.3.4', '3.3.7', true],
  ['3.3.4', '3.4.1', false],
  ['3.3.4', '4.1.0', false],
])('version compatibility', (appRelease, currentRelease, expected) => {
  const result = checkVersionsCompatible(appRelease, currentRelease);

  expect(result).toBe(expected);
});
