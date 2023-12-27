import _ from 'lodash';
import NativePromise from 'native-promise-only';
import {Formio} from 'react-formio';

import {ADVANCED, TEXT_BASIC, TEXT_VALIDATION, TRANSLATIONS} from './edit/tabs';
import {localiseSchema} from './i18n';

const textareaBasicTab = {
  key: 'basic',
  label: 'Basic',
  components: [
    ...TEXT_BASIC.components,
    {
      type: 'checkbox',
      input: true,
      key: 'autoExpand',
      label: 'Auto Expand',
      tooltip:
        "This will make the TextArea auto expand it's height as the user is typing into the area.",
      weight: 415,
      conditional: {
        json: {
          '==': [{var: 'data.editor'}, ''],
        },
      },
    },
    {
      type: 'number',
      input: true,
      weight: 80,
      key: 'rows',
      label: 'Number of rows',
      tooltip: 'The number of rows for this text area.',
    },
  ],
};

const textareaTabs = {
  type: 'tabs',
  key: 'tabs',
  components: [textareaBasicTab, ADVANCED, TEXT_VALIDATION, TRANSLATIONS],
};

const FormioTextarea = Formio.Components.components.textarea;

class TextArea extends FormioTextarea {
  static schema(...extend) {
    return localiseSchema(FormioTextarea.schema({validate: {maxLength: 10000}}, ...extend));
  }

  static get builderInfo() {
    return {
      ...FormioTextarea.builderInfo,
      schema: TextArea.schema(),
    };
  }

  get defaultSchema() {
    return TextArea.schema();
  }

  static editForm() {
    return {components: [textareaTabs]};
  }

  attachElement(element, index) {
    // override to deal with the newer CKEditor5 version, v40.2 vs. formio's v19.
    // Code taken and adapted from Formio.js v13.x, `src/components/textarea/TextArea.js`.
    if (this.autoExpand && (this.isPlain || this.options.readOnly || this.options.htmlView)) {
      if (element.nodeName === 'TEXTAREA') {
        this.addAutoExpanding(element, index);
      }
    }

    if (this.options.readOnly) {
      return element;
    }

    if (this.component.wysiwyg && !this.component.editor) {
      this.component.editor = 'ckeditor';
    }

    let settings = _.isEmpty(this.component.wysiwyg)
      ? this.wysiwygDefault[this.component.editor] || this.wysiwygDefault.default
      : this.component.wysiwyg;

    // Keep track of when this editor is ready.
    this.editorsReady[index] = new NativePromise(editorReady => {
      // Attempt to add a wysiwyg editor. In order to add one, it must be included on the global scope.
      switch (this.component.editor) {
        case 'ace':
        case 'quill':
          throw new Error('Only CKEditor is supported.');
        case 'ckeditor':
          settings = settings || {};
          settings.rows = this.component.rows;
          this.addCKE(element, settings, newValue => this.updateEditorValue(index, newValue)).then(
            editor => {
              this.editors[index] = editor;
              let dataValue = this.dataValue;
              dataValue =
                this.component.multiple && Array.isArray(dataValue) ? dataValue[index] : dataValue;
              const value = this.setConvertedValue(dataValue, index);
              const isReadOnly = this.options.readOnly || this.disabled;

              // XXX: removed check for IE, it is not supported.

              const numRows = parseInt(this.component.rows, 10);
              if (_.isFinite(numRows)) {
                // Default height is 21px with 10px margin + a 14px top margin.
                const editorHeight = numRows * 31 + 14;
                // editor.ui.view.editable.editableElement.style.height = `${editorHeight}px`;
                editor.editing.view.change(writer => {
                  writer.setStyle(
                    'height',
                    `${editorHeight}px`,
                    editor.editing.view.document.getRoot()
                  );
                });
              }
              if (isReadOnly) {
                editor.enableReadOnlyMode('formio readonly');
              }
              editor.data.set(value);

              editorReady(editor);
              return editor;
            }
          );
          break;
        default:
          super.attachElement(element, index);
          break;
      }
    });

    return element;
  }
}

export default TextArea;
