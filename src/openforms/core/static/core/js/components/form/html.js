import {defineCommonEditFormTabs, defineInputInfo} from './abstract';
import {Formio} from 'formiojs';

// defineInputInfo(Formio.Components.components.htmlelement, 'wysiwyg');
// defineCommonEditFormTabs(Formio.Components.components.htmlelement);

export const html = `
<{{ctx.tag}} ref="html" class="html">
    {{ctx.t(ctx.content)}}
</{{ctx.tag}}>
`;
