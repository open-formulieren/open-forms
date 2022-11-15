import {get} from 'utils/fetch';
import {LANGUAGE_INFO_ENDPOINT} from '../constants';

const loadLanguages = async () => {
  try {
    const response = await get(LANGUAGE_INFO_ENDPOINT);
    if (!response.ok) {
      throw new Error('Error loading languages');
    }
    return response.data.languages;
  } catch (e) {
    console.error(e);
  }
};

export {loadLanguages};
