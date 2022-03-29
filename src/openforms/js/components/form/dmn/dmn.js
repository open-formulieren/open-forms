import {Formio} from 'react-formio';
// import DmnJS from 'dmn-js';  // https://www.npmjs.com/package/dmn-js

// import {get} from '../../../utils/fetch';
import editForm from './editForm';

const Field = Formio.Components.components.field;


export default class DMNEvaluation extends Field {
    static schema(...extend) {
        return Field.schema({
            type: 'dmn',
            label: 'DMN Evaluation',
            key: 'dmn',
            input: false,
            dmn: {
                engine: '',
                decisionDefinition: '',
                decisionDefinitionVersion: '',
                resultDisplayTemplate: '{% for key, value in result.items %}{{ key }}: {{ value }}{% endfor %}',
                resultDisplay: '',  // evaluated resultDisplayTemplate after the DMN table was evaluated
            },
        }, ...extend);
    }

    static get builderInfo() {
        return {
            title: 'DMN/Business rules evaluation',
            icon: 'th-list',
            weight: 1000,
            schema: DMNEvaluation.schema(),
        };
    }

    get defaultSchema() {
        return DMNEvaluation.schema();
    }

    static editForm() {
        return {components: editForm};
    }

    constructor(component, options, data) {
        super(component, options, data);

        this.viewer = null;
    }

    render() {
        return super.render(this.renderTemplate('dmn'));
    }

    attach(element) {
        this.loadRefs(element, {
            dmnPreview: 'single',
            dmnViewer: 'single',
        });

        // // get the XML DMN definition (if available) and render it in the viewer
        // get(
        //     `/api/v1/dmn/decision-definitions/${this.component.dmn.decisionDefinition.id}/xml`,
        //     {
        //         engine: this.component.dmn.engine.id,
        //         version: this.component.dmn.decisionDefinitionVersion.id,
        //     }
        // ).then(response => {
        //     if (!response.ok) return;
        //     if (!this.refs.dmnViewer) return;

        //     const xml = response.data.xml;
        //     if (!xml) return;

        //     if (!this.viewer) this.viewer = new DmnJS();
        //     return this.viewer.importXML(xml);
        // }).then(() => {
        //     if (!this.viewer) return;

        //     this.viewer.attachTo(this.refs.dmnViewer);
        //     const view = this.viewer.getViews().find(view => view.type === 'decisionTable');
        //     this.viewer.open(view);
        // });

        return super.attach(element);
    }

    detach() {
        this.viewer && this.viewer.detach();
        return super.detach();
    }
}
