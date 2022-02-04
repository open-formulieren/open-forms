const usedKeys = {};


const getUniqueRandomString = (length=7, scope='') => {
  if (!usedKeys[scope]) usedKeys[scope] = [];
  let randomString;
  do {
    randomString = getRandomString(length);
  } while (usedKeys[scope].includes(randomString));
  return randomString;
};


// Inspired on FormioUtils.getRandomComponentId and react-key-string
const getRandomString = (length=7) => {
  return `e${Math.random().toString(36).substring(length)}`;
};


export {getRandomString, getUniqueRandomString};
