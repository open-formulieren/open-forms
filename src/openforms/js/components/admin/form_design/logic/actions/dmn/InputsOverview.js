import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

const InputsOverview = ({inputClauses}) => (
  <section className="logic-dmn__info">
    <h2 className="react-modal__section-title">
      <FormattedMessage
        description="DMN input expressions title"
        defaultMessage="Expected input expressions"
      />
    </h2>
    <p>
      <FormattedMessage
        description="DMN input expressions warning about extraction accuracy"
        defaultMessage={`The expressions here are extracted from the selected decision definition.
          It's possible certain inputs are displayed here that are already provided
          by a dependency of the selected decision, due to the complexity of the
          input expression.
        `}
      />
    </p>

    <table className="mapping-table mapping-table--stretch">
      <thead>
        <tr>
          <th>
            <FormattedMessage description="DMN Input clause label header" defaultMessage="Label" />
          </th>
          <th>
            <FormattedMessage
              description="DMN Input clause expression header"
              defaultMessage="Expression"
            />
          </th>
          <th>
            <FormattedMessage
              description="DMN Input clause data type header"
              defaultMessage="Data type"
            />
          </th>
        </tr>
      </thead>
      <tbody>
        {inputClauses.map((inputClause, index) => (
          <tr key={index}>
            <td>{inputClause.label || '-'}</td>
            <td>
              <code>{inputClause.expression}</code>
            </td>
            <td>
              <code>{inputClause.typeRef || '-'}</code>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </section>
);

InputsOverview.propTypes = {
  inputClauses: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.string,
      expression: PropTypes.string.isRequired,
      typeRef: PropTypes.string,
    })
  ),
};

export default InputsOverview;
