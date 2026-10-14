const createListFromSchema = <T = unknown, U = unknown>(
  enums: T[],
  enumNames: string[],
  callback: (value: T, label: string) => U
): U[] => {
  // enum and enumNames are expected to have the same size!
  if (enums.length !== enumNames.length)
    throw new Error('enums and enumNames must have the same size');
  return enums.map((val: T, index: number) => {
    const name = enumNames[index];
    return callback(val, name);
  });
};

export const getChoicesFromSchema = <T = unknown>(
  enums: T[],
  enumNames: string[],
  blankChoiceTitle: string = ''
): [T, string][] => {
  return createListFromSchema<T, [T, string]>(enums, enumNames, (value, label) => [
    value,
    label || blankChoiceTitle,
  ]);
};

interface ReactSelectOption<T> {
  value: T;
  label: string;
}

export const getReactSelectOptionsFromSchema = <T = unknown>(
  enums: T[],
  enumNames: string[],
  blankChoiceTitle: string = ''
): ReactSelectOption<T>[] => {
  return createListFromSchema<T, ReactSelectOption<T>>(enums, enumNames, (value, label) => ({
    value,
    label: label || blankChoiceTitle,
  }));
};
