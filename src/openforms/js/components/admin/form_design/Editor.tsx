import {Editor} from '@tinymce/tinymce-react';
import {useContext, useRef} from 'react';
import {useIntl} from 'react-intl';
import {useGlobalState} from 'state-pool';
import type {Editor as RawEditor} from 'tinymce';

import getTinyMCEAppearance from '@/tinymce_appearance';
import {currentTheme} from '@/utils/theme';
import type {OFTheme} from '@/utils/theme';

import {default as defaultTinyMceConfig} from '../../../../conf/tinymce_config.json';
import {TinyMceContext} from './Context';

export const DEFAULT_CONFIG = defaultTinyMceConfig;

export interface TinyMCEEditorProps {
  content: string;
  onEditorChange: React.ComponentProps<typeof Editor>['onEditorChange'];
  tinyMceConfig: Partial<React.ComponentProps<typeof Editor>['init']>;
}

const TinyMCEEditor: React.FC<TinyMCEEditorProps> = ({
  content,
  onEditorChange,
  tinyMceConfig = defaultTinyMceConfig,
}) => {
  const editorRef = useRef<RawEditor | null>(null);
  const tinyMceUrl = useContext(TinyMceContext);
  const intl = useIntl();
  const [theme] = useGlobalState<OFTheme>(currentTheme);

  const appearance = getTinyMCEAppearance(theme);
  // when appearance changes, the key changes, which re-initializes the editor. tinymce
  // does not have a built-in way to change the skin/content_css on the fly.
  const key = `${appearance.skin}/${appearance.content_css}`;
  return (
    <>
      <Editor
        key={key}
        tinymceScriptSrc={tinyMceUrl}
        onInit={(_, editor) => (editorRef.current = editor)}
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
