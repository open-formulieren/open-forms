import React, {useContext, useRef} from "react";
import {Editor} from "@tinymce/tinymce-react";
import {TinyMceContext} from "./Context";



const TinyMCEEditor = ({content, onEditorChange}) => {
    const editorRef = useRef(null);
    const tinyMceUrl = useContext(TinyMceContext);

    return (
        <>
            <Editor
                tinymceScriptSrc={tinyMceUrl}
                onInit={(evt, editor) => editorRef.current = editor}
                value={content}
                init={{
                    /*
                    NOTE: manually synchronise changes with Django's copy in settings.TINYMCE_DEFAULT_CONFIG
                     */
                    height: 250,
                    menubar: false,
                    plugins: [
                        'advlist autolink lists link image charmap print preview anchor',
                        'searchreplace visualblocks code fullscreen',
                        'insertdatetime media table paste code help wordcount'
                    ],
                    toolbar: 'undo redo | formatselect | ' +
                    'bold italic backcolor | alignleft aligncenter ' +
                    'alignright alignjustify | bullist numlist outdent indent | ' +
                    'link unlink removeformat | help',
                    content_style: 'body { font-family:Helvetica,Arial,sans-serif; font-size:14px }',
                    default_link_target: '_blank',
                    link_default_protocol: 'https',
                    link_assume_external_targets: 'https',

                    // Django would set this in its own widget
                    language: 'nl'
                }}
                onEditorChange={onEditorChange}
            />
        </>
    );
};

export default TinyMCEEditor;
