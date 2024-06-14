import {
  clearObsoleteLiterals,
  handleComponentValueLiterals,
  isTranslatableProperty,
  persistComponentTranslations,
} from './translation';

describe('Checking if properties are translatable', () => {
  it('works with plain strings', () => {
    expect(isTranslatableProperty('textfield', 'label')).toBe(true);
    expect(isTranslatableProperty('date', 'label')).toBe(true);
    expect(isTranslatableProperty('textfield', 'key')).toBe(false);
    expect(isTranslatableProperty('textfield', 'top')).toBe(false);
    expect(isTranslatableProperty('content', 'html')).toBe(true);
    expect(isTranslatableProperty('textfield', 'validate.required')).toBe(false);
  });

  it('takes component type into account', () => {
    expect(isTranslatableProperty('fieldset', 'legend')).toBe(true);
    expect(isTranslatableProperty('date', 'defaultValue')).toBe(false);
  });

  it('works with nested paths', () => {
    expect(isTranslatableProperty('textfield', 'data.values[3].label')).toBe(false);
    expect(isTranslatableProperty('select', 'data.values[2].value')).toBe(false);
    expect(isTranslatableProperty('select', 'data.values[1].label')).toBe(true);
    expect(isTranslatableProperty('radio', 'values[420].label')).toBe(true);
    expect(isTranslatableProperty('selectboxes', 'values[420].label')).toBe(true);
  });

  it('treats WYSIWYG in a special way', () => {
    expect(isTranslatableProperty('content', 'label')).toBe(false);
    expect(isTranslatableProperty('content', 'html')).toBe(true);
  });
});

describe('Persisting component translations in the store', () => {
  const component = {type: 'textfield', key: 'simpleComponent'};

  it('does not crash when namespace not present', () => {
    const container = {};
    persistComponentTranslations(container, component);

    expect(container).toEqual({});
    expect(component.type).toBe('textfield');
    expect(component.openForms).toBe(undefined);
  });

  it('merges with existing translations', () => {
    const container = {nl: {Foo: 'Bar'}, en: {Foo: 'Baz'}};
    const translations = {
      nl: [{literal: 'a_literal', translation: 'Vertaling'}],
      en: [{literal: 'a_literal', translation: 'Translation'}],
    };
    const _component = {...component, openForms: {translations: translations}};

    persistComponentTranslations(container, _component);

    expect(container).toEqual({
      nl: {Foo: 'Bar', a_literal: 'Vertaling'},
      en: {Foo: 'Baz', a_literal: 'Translation'},
    });
    expect(_component.openForms.translations).toBe(undefined);
    expect(_component.openForms).not.toBe(undefined);
  });
});

describe('Clearing obsolete literals', () => {
  const configuration = {
    display: 'form',
    components: [
      {
        type: 'textfield',
        key: 'text1',
        label: 'text1Label',
        defaultValue: 'text1Default',
      },
      {
        type: 'date',
        key: 'date1',
        label: 'date1Label',
        defaultValue: '2023-01-26',
      },
      {
        type: 'editgrid',
        key: 'editgrid1',
        label: 'editgrid1Label',
        groupLabel: 'editgrid1GroupLabel',
        components: [
          {
            type: 'number',
            key: 'number1',
            label: 'number1Label',
            defaultValue: 123,
            description: 'number1Description',
          },
        ],
      },
    ],
  };

  const componentTranslations = {
    nl: {
      text1Label: 'Tekstlabel',
      text1: 'Tekst1',
      date1Label: '',
      editgrid1GroupLabel: 'Veldengroep',
    },
    en: {
      editgrid1Label: 'Edit grid label',
      number1Label: 'First number',
      123: 'Nope',
    },
  };

  it('removes unused literals', () => {
    const cleaned = clearObsoleteLiterals(componentTranslations, configuration);

    expect(cleaned.nl).toEqual(expect.not.objectContaining({text1: 'Tekst1', date1Label: ''}));
    expect(cleaned.nl).toEqual({
      text1Label: 'Tekstlabel',
      editgrid1GroupLabel: 'Veldengroep',
    });
    expect(cleaned.en).toEqual(expect.not.objectContaining({text1: ''}));
    expect(cleaned.en).toEqual(expect.not.objectContaining({text1: undefined}));
    expect(cleaned.en).toEqual(expect.not.objectContaining({text1: null}));
    expect(cleaned.en).toEqual({
      editgrid1Label: 'Edit grid label',
      number1Label: 'First number',
    });
  });

  it.each(['', undefined, null, 0])('removes empty translations (%p)', emptyValue => {
    const component = {type: 'textfield', key: 'foo', label: 'label'};
    const translations = {nl: {label: emptyValue}};

    const cleaned = clearObsoleteLiterals(translations, {components: [component]});

    expect(cleaned.nl).toEqual(expect.not.objectContaining({label: emptyValue}));
  });
});

describe('Component value label literals', () => {
  const componentTranslations = {
    nl: {
      'Option 1': 'Optie 1',
      'Option 2': 'Optie 2',
    },
  };
  const values = [
    {value: 'option1', label: 'Option 1'},
    {value: 'option2', label: 'Option 2'},
  ];
  const selectComponent = {
    type: 'select',
    key: 'select',
    data: {values},
    openForms: {translations: {nl: [], en: []}},
  };
  const radioComponent = {
    type: 'radio',
    key: 'radio',
    values,
    openForms: {translations: {nl: [], en: []}},
  };
  const selectBoxesComponent = {
    type: 'selectboxes',
    key: 'selectboxes',
    values,
    openForms: {translations: {nl: [], en: []}},
  };

  it.each([
    [selectComponent, 'data.values'],
    [radioComponent, 'values'],
    [selectBoxesComponent, 'values'],
  ])('are exposed in the translations structure (%#)', (component, path) => {
    const translations = handleComponentValueLiterals(
      {...component},
      componentTranslations,
      path,
      values,
      {}
    );

    expect(translations.nl).toEqual([
      {literal: 'Option 1', translation: 'Optie 1'},
      {literal: 'Option 2', translation: 'Optie 2'},
    ]);
    expect(translations.en).toEqual([
      {literal: 'Option 1', translation: ''},
      {literal: 'Option 2', translation: ''},
    ]);
  });
});
