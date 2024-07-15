import isEmpty from 'lodash/isEmpty';
import PropTypes from 'prop-types';
import React, {useContext, useState} from 'react';
import useAsync from 'react-use/esm/useAsync';

import {APIContext} from 'components/admin/form_design/Context';
import {LOGIC_DESCRIPTION_ENDPOINT} from 'components/admin/form_design/constants';
import {TextInput} from 'components/admin/forms/Inputs';
import {post} from 'utils/fetch';

const generateDescription = async (csrftoken, expression) => {
  let response;
  try {
    response = await post(LOGIC_DESCRIPTION_ENDPOINT, csrftoken, {expression});
  } catch (error) {
    // we deliberately ignore backend errors here - validation errors for bad logic
    // expressions should already show up in that field itself.
    console.debug(error);
    return null;
  }
  return response.data.description;
};

const LogicDescriptionInput = ({
  generationAllowed,
  generationRequest,
  onChange: _onChange,
  onDescriptionGenerated,
  logicExpression = null,
  ...textInputProps
}) => {
  const {csrftoken} = useContext(APIContext);
  const [modifiedByHuman, setModifiedByHuman] = useState(false);
  const [hasFocus, setHasFocus] = useState(false);

  const onChange = event => {
    const {
      target: {value},
    } = event;
    _onChange(event);
    setModifiedByHuman(value !== '');
  };

  const mustBail = isEmpty(logicExpression) || !generationAllowed || modifiedByHuman || hasFocus;

  useAsync(async () => {
    if (mustBail) {
      return;
    }
    const description = await generateDescription(csrftoken, logicExpression);
    description && onDescriptionGenerated(description);
    // generationRequest is incremented by the parent to force the hook to execute.
    // Running the hook without dependencies causes it to render indefinitely and fire
    // network requests in an infinite loop.
    //
    // Running this without the generationRequest causes multiple clicks to reset the
    // description to empty string without it actually being re-populated from the backend.
  }, [mustBail, generationRequest, logicExpression]);

  return (
    <TextInput
      onChange={onChange}
      onFocus={() => setHasFocus(true)}
      onBlur={() => setHasFocus(false)}
      {...textInputProps}
      maxLength="100"
    />
  );
};

LogicDescriptionInput.propTypes = {
  generationAllowed: PropTypes.bool.isRequired,
  generationRequest: PropTypes.number.isRequired,
  onChange: PropTypes.func.isRequired,
  onDescriptionGenerated: PropTypes.func.isRequired,
  logicExpression: PropTypes.oneOfType([
    PropTypes.object,
    PropTypes.array,
    PropTypes.string,
    PropTypes.bool,
    PropTypes.number,
  ]),
};

export default LogicDescriptionInput;
