/*
https://github.com/open-formulieren/open-forms/issues/223

pdf xls vlsx (xlsx?) csv doc dockx (docx?) jpg png, zip, rar, tar en alle open office formaten
 */


export const KNOWN_TYPES = {
    "All": "*",
    ".png": "image/png",
    ".jpg": "image/jpeg",

    ".pdf": "application/pdf",

    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".csv": "text/csv",

    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",

    "Open Office": ["application/vnd.oasis.opendocument.*",
        "application/vnd.stardivision.*",
        "application/vnd.sun.xml.*"].join(","),

    ".zip": "application/zip",
    ".rar": "application/vnd.rar",
    ".tar": "application/x-tar",
    // if we want .tar you'd expect .gz
    // ".gz": "application/gzip",
}


export function as_choices(obj) {
    return Object.keys(obj).map(key => {
        return {"label": key, "value": obj[key]};
    })
}
