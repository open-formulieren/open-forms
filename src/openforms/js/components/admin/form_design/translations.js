/**
 * Defines the default translations structure + values for new/missing records.
 */
import set from 'lodash/set';

export const initialFormTranslations = {
  name: '',
  changeText: '',
  confirmText: '',
  previousText: '',
  beginText: '',
  submissionConfirmationTemplate: '',
  introductionPageContent: '',
  explanationTemplate: '',
};

export const initialConfirmationEmailTranslations = {
  subject: '',
  content: '',
};

export const initialStepTranslations = {
  name: '',
  previousText: '',
  saveText: '',
  nextText: '',
};

export const assignInitialTranslations = (target, code, initial) => {
  for (const [key, value] of Object.entries(initial)) {
    if (target?.[code]?.[key] != null) continue;
    set(target, [code, key], value);
  }
};
