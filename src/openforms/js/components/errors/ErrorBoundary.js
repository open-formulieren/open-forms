import React from 'react';
import {FormattedMessage} from 'react-intl';

import ErrorMessage from './ErrorMessage';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {hasError: false, errorMessage: props.errorMessage};
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI.
    return {hasError: true, error: error};
  }

  // componentDidCatch(error, info) {
  //  TODO Log to sentry?
  // }

  render() {
    if (this.state.hasError) {
      const errorMessage = this.state.errorMessage || (
        <FormattedMessage
          description="Unexpected error message"
          defaultMessage="Oh no! Something went wrong."
        />
      );
      return <ErrorMessage>{errorMessage}</ErrorMessage>;
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
