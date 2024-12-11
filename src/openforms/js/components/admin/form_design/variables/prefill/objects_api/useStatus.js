import {useFormikContext} from 'formik';

/**
 * Convenience hook that wraps around Formik's status.
 *
 * This centralizes the shape of the status tracked in the Formik state. We use status
 * to track some configuration/state that affects the configuration modal without it
 * directly being a form field or requiring to be managed at a higher level.
 */
const useStatus = () => {
  const {status = {}, setStatus} = useFormikContext();
  const {showCopyButton = false} = status;
  const toggleShowCopyButton = () => {
    setStatus({...status, showCopyButton: !showCopyButton});
  };
  return {
    showCopyButton,
    toggleShowCopyButton,
  };
};

export default useStatus;
