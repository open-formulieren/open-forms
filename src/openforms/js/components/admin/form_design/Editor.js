import React, {useContext, useRef} from "react";
import {Editor} from "@tinymce/tinymce-react";
import {TinyMceContext} from "./Context";
import tinyMceConfig from "../../../../conf/tinymce_config.json";



const TinyMCEEditor = ({content, onEditorChange}) => {
    const editorRef = useRef(null);
    const tinyMceUrl = useContext(TinyMceContext);

    return (
        <>
            <Editor
                tinymceScriptSrc={tinyMceUrl}
                onInit={(evt, editor) => editorRef.current = editor}
                value={content}
                init={{...tinyMceConfig,
                    // Django would set this in its own widget
                    language: 'nl'
                }}
                onEditorChange={onEditorChange}
            />
        </>
    );
};

export default TinyMCEEditor;
