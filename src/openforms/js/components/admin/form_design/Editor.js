import React, {useContext, useRef} from "react";
import {useIntl} from 'react-intl';
import {Editor} from "@tinymce/tinymce-react";
import {TinyMceContext} from "./Context";
import tinyMceConfig from "../../../../conf/tinymce_config.json";



const TinyMCEEditor = ({content, onEditorChange}) => {
    const editorRef = useRef(null);
    const tinyMceUrl = useContext(TinyMceContext);
    const intl = useIntl()

    return (
        <>
            <Editor
                tinymceScriptSrc={tinyMceUrl}
                onInit={(evt, editor) => editorRef.current = editor}
                value={content}
                init={{...tinyMceConfig,
                    language: intl.locale,
                }}
                onEditorChange={onEditorChange}
            />
        </>
    );
};

export default TinyMCEEditor;
