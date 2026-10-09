import type {IntlShape, MessageDescriptor} from 'react-intl';

type ChoiceValue = string;

type ChoiceTuple = [ChoiceValue, MessageDescriptor];
type ChoicesObject = {[v: ChoiceValue]: MessageDescriptor};
type TranslatedChoice = [ChoiceValue, string];

/**
 * Given a list of choices with defined messages, ensure the list of translated choices
 * is returned.
 */
const getTranslatedChoices = (
  intl: IntlShape,
  choices: ChoiceTuple[] | ChoicesObject
): TranslatedChoice[] => {
  const choicesArray: ChoiceTuple[] = Array.isArray(choices) ? choices : Object.entries(choices);
  return choicesArray.map(([value, labelMessage]) => [value, intl.formatMessage(labelMessage)]);
};

export {getTranslatedChoices};
