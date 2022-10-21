import React, {useContext, useRef} from 'react';
import {useIntl} from 'react-intl';
import {Editor} from '@tinymce/tinymce-react';

import tinyMceConfig from '../../../../conf/tinymce_config.json';
import {TinyMceContext} from './Context';

const TinyMCEEditor = ({content, onEditorChange}) => {
  const editorRef = useRef(null);
  const tinyMceUrl = useContext(TinyMceContext);
  const intl = useIntl();
  // TODO Django 4.2: use explicit theme names rather than the media query approach:
  // https://github.com/django/django/blob/main/django/contrib/admin/static/admin/css/dark_mode.css#L36
  const useDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;

  return (
    <>
      <Editor
        tinymceScriptSrc={tinyMceUrl}
        onInit={(evt, editor) => (editorRef.current = editor)}
        value={content}
        init={{
          ...tinyMceConfig,
          language: intl.locale,
          skin: useDarkMode ? 'oxide-dark' : 'oxide',
          content_css: useDarkMode ? 'dark' : 'default',
        }}
        onEditorChange={onEditorChange}
      />
    </>
  );
};

export default TinyMCEEditor;
