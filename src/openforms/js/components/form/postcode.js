import TextField from './textfield';

// NB: this component will become deprecated due to preset autocomplete components
// see issue: https://github.com/open-formulieren/open-forms/issues/2268

class PostcodeField extends TextField {
  static schema(...extend) {
    return TextField.schema(
      {
        type: 'postcode',
        label: 'Postcode',
        autocomplete: 'postal-code',
        key: 'postcode',
        inputMask: '9999 AA',
        validateOn: 'blur',
        validate: {
          customMessage: 'Invalid Postcode',
          // Dutch postcode has 4 numbers and 2 letters (case insensitive). Letter combinations SS, SD and SA
          // are not used due to the Nazi-association.
          // See https://stackoverflow.com/a/17898538/7146757 and https://nl.wikipedia.org/wiki/Postcodes_in_Nederland
          pattern: '^[1-9][0-9]{3} ?(?!sa|sd|ss|SA|SD|SS)[a-zA-Z]{2}$',
        },
      },
      ...extend
    );
  }

  static get builderInfo() {
    return {
      title: 'Postcode Field',
      icon: 'home',
      group: 'deprecated',
      weight: 10,
      schema: PostcodeField.schema(),
    };
  }

  get defaultSchema() {
    return PostcodeField.schema();
  }
}

export default PostcodeField;
