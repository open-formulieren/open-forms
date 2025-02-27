import {Formio} from 'formiojs';

import {localiseSchema} from './i18n';

const Time = Formio.Components.components.time;

/**
 * Time 24h format is functional by not using the HTML5 widget, but rather the mask
 * input & specify the moment format to use. This still runs the validation and allows
 * us to enter times in 24h notation.
 */
class TimeField extends Time {
  constructor(...args) {
    super(...args);
  }

  static schema(...extend) {
    const schema = Time.schema(
      {
        inputType: 'text',
        format: 'HH:mm',
        validateOn: 'blur',
        validate: {
          minTime: null,
          maxTime: null,
        },
        defaultValue: '',
      },
      ...extend
    );
    return localiseSchema(schema);
  }

  static get builderInfo() {
    return {
      title: 'Time',
      icon: 'clock-o',
      group: 'basic',
      weight: 10,
      schema: TimeField.schema(),
    };
  }

  get defaultSchema() {
    return TimeField.schema();
  }
}

export default TimeField;
