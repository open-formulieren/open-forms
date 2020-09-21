import {CrudConsumer, CrudConsumerObject} from 'consumerjs';


/**
 * Resulting object of fetching data using FormDefinitionConsumer.
 * @class
 */
class FormDefinition extends CrudConsumerObject {
}


/**
 * Consumer for fetching FormDefinitions.
 * @class
 */
export class FormDefinitionConsumer extends CrudConsumer {
    constructor() {
        super('/api/v1/form-definitions', FormDefinition);

        this.csrfProtection = false;
    }

    /**
     * Extends build in read() with ability to load absolute urls.
     * @param {string} path Can either be a slug/pk or an (absolute) url.
     * @return {Promise}
     */
    read(path = '') {
        const endpoint = this.endpoint;

        if (path.startsWith('/') || path.toLowerCase().match('^https?:\/\/')) {
            this.endpoint = path;
        }

        const promise = super.read('');
        this.endpoint = endpoint;
        return promise;

    }
}
