import {Editor} from '@tinymce/tinymce-react';
import React, {useContext, useRef} from 'react';
import {useIntl} from 'react-intl';
import {useGlobalState} from 'state-pool';
import getTinyMCEAppearance from 'tinymce_appearance';

import {currentTheme} from 'utils/theme';

import tinyMceConfig from '../../../../conf/tinymce_config.json';
import {TinyMceContext} from './Context';

const TinyMCEEditor = ({content, onEditorChange}) => {
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
