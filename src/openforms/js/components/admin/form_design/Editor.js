import React, {useRef} from "react";
import {Editor} from "@tinymce/tinymce-react";

import {TINYMCE_URL} from "./constants";


const TinyMCEEditor = ({content, onEditorChange}) => {
    const editorRef = useRef(null);

    return (
        <>
            <Editor
                tinymceScriptSrc={TINYMCE_URL}
                onInit={(evt, editor) => editorRef.current = editor}
                value={content}
                init={{
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
                    'removeformat | help',
                    content_style: 'body { font-family:Helvetica,Arial,sans-serif; font-size:14px }'
                }}
                onEditorChange={onEditorChange}
            />
        </>
    );
};

export default TinyMCEEditor;
