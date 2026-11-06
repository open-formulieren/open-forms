import React from 'react';
import {MessageDescriptor} from 'react-intl';

type ValidationError = string | MessageDescriptor;
type ValidationErrorTuple = [key: string, message: ValidationError];

const ValidationErrorContext = React.createContext<ValidationErrorTuple[]>([]);
ValidationErrorContext.displayName = 'ValidationErrorContext';

interface ValidationErrorProviderProps {
  children?: React.ReactNode;
  errors?: ValidationErrorTuple[];
}

const ValidationErrorsProvider = ({children, errors = []}: ValidationErrorProviderProps) => {
  return (
    <ValidationErrorContext.Provider value={errors}>{children}</ValidationErrorContext.Provider>
  );
};

const filterErrors = (name: string, errors: ValidationErrorTuple[]): ValidationErrorTuple[] => {
  return errors
    .filter(([key]) => key.startsWith(`${name}.`))
    .map(([key, msg]) => [key.slice(name.length + 1), msg]);
};

export {
  ValidationErrorsProvider,
  ValidationErrorContext,
  filterErrors,
  ValidationError,
  ValidationErrorTuple,
};
export default ValidationErrorsProvider;
