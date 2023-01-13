import {generateComponentTranslations, removeEmptyTranslations} from './translation';

describe('generating component translations', () => {
  const configuration = {
    display: 'form',
    components: [
      {
        key: 'onderschrift',
        type: 'textfield',
        label: 'Onderschrift',
        labelPosition: 'top',
        tooltip: '',
        description: 'De tekst onder het plaatje',
        placeholder: 'Placeholder is een Engels leenwoord',
        defaultValue: '',
      },
      {
        key: 'content',
        type: 'content',
        html: '<p>Kent u deze nog?</p><figure class="image"><img src="data:image/gif;base64,R0lGODdhAQABAIEAAAAAAAAAAAAAAAAAACwAAAAAAQABAAAIBAABBAQAOw=="><figcaption>{{ onderschrift }}</figcaption></figure>',
        label: '',
        tooltip: '',
        description: '',
        placeholder: '',
        defaultValue: null,
      },
    ],
  };
  const componentTranslations = {
    nl: {},
    en: {
      Onderschrift: 'Caption',
      'Placeholder is een Engels leenwoord': 'Placeholder',
      '<p>Vorige versie zonder plaatje.</p>': '<p>Translation of previous literal.</p>',
      '<p>Kent u deze nog?</p><figure class="image"><img src="data:image/gif;base64,R0lGODdhAQABAIEAAAAAAAAAAAAAAAAAACwAAAAAAQABAAAIBAABBAQAOw=="><figcaption>{{ onderschrift }}</figcaption></figure>':
        '<p>Remember these?</p><figure class="image"><img src="data:image/gif;base64,R0lGODdhAQABAIEAAAAAAAAAAAAAAAAAACwAAAAAAQABAAAIBAABBAQAOw=="><figcaption>{{ onderschrift }}</figcaption></figure>',
    },
  };

  const translations = generateComponentTranslations(configuration, componentTranslations);

  it('adds missing translations', () => {
    expect(translations['en']['De tekst onder het plaatje']).toBe('');
  });

  it('does not pickup untranslatable properties', () => {
    expect(translations['en']['top']).toBe(undefined);
    expect(translations['en']['textfield']).toBe(undefined);
    expect(translations['en']['content']).toBe(undefined);
  });

  it('removes unused literals', () => {
    // keeps used literal
    expect(
      translations['en'][
        '<p>Kent u deze nog?</p><figure class="image"><img src="data:image/gif;base64,R0lGODdhAQABAIEAAAAAAAAAAAAAAAAAACwAAAAAAQABAAAIBAABBAQAOw=="><figcaption>{{ onderschrift }}</figcaption></figure>'
      ]
    ).toBe(
      '<p>Remember these?</p><figure class="image"><img src="data:image/gif;base64,R0lGODdhAQABAIEAAAAAAAAAAAAAAAAAACwAAAAAAQABAAAIBAABBAQAOw=="><figcaption>{{ onderschrift }}</figcaption></figure>'
    );
    // doesn't contain unused literal
    expect(translations['en']).not.toBe(
      expect.objectContaining({
        '<p>Vorige versie zonder plaatje.</p>': '<p>Translation of previous literal.</p>',
      })
    );
  });
});

describe('removing empty component translations', () => {
  const componentTranslations = {
    nl: {
      Onderschrift: '',
      'Placeholder is een Engels leenwoord': '',
      '<p>Vorige versie zonder plaatje.</p>': '',
    },
    en: {
      Onderschrift: '',
      'Placeholder is een Engels leenwoord': 'Placeholder',
      '<p>Vorige versie zonder plaatje.</p>': '<p>Translation of previous literal.</p>',
    },
  };

  it('does not return literal with empty string translations', () => {
    const translations = removeEmptyTranslations(componentTranslations);

    expect(translations['nl']).toStrictEqual({});
    expect(translations['nl']['Onderschrift']).toBe(undefined);
  });
});
