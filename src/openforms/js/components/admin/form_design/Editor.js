import {Editor} from '@tinymce/tinymce-react';
import React, {useContext, useRef} from 'react';
import {useIntl} from 'react-intl';
import {useGlobalState} from 'state-pool';
import getTinyMCEAppearance from 'tinymce_appearance';

import {currentTheme} from 'utils/theme';

import {default as defaultTinyMceConfig} from '../../../../conf/tinymce_config.json';
import {TinyMceContext} from './Context';

export const DEFAULT_CONFIG = defaultTinyMceConfig;

const TinyMCEEditor = ({content, onEditorChange, tinyMceConfig = defaultTinyMceConfig}) => {
  const editorRef = useRef(null);
  const tinyMceUrl = useContext(TinyMceContext);
  const intl = useIntl();
  const [theme] = useGlobalState(currentTheme);

  const appearance = getTinyMCEAppearance(theme);
  // when appearance changes, the key changes, which re-initializes the editor. tinymce
  // does not have a built-in way to change the skin/content_css on the fly.
  const key = `${appearance.skin}/${appearance.content_css}`;
  return (
    <>
      <Editor
        key={key}
        tinymceScriptSrc={tinyMceUrl}
        onInit={(evt, editor) => (editorRef.current = editor)}
        value={content}
        init={{
          ...tinyMceConfig,
          language: intl.locale,
          ...appearance,
        }}
        onEditorChange={onEditorChange}
      />
    </>
  );
};

export default TinyMCEEditor;
