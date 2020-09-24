import {CrudConsumer, CrudConsumerObject} from 'consumerjs';


/**
 * A submission of a form.
 * @class
 */
class Submission extends CrudConsumerObject {
}


/**
 * Consumer used for CRUD operations on Submission objects.
 * @class
 */
export class SubmissionConsumer extends CrudConsumer {
    constructor() {
        super('/api/v1/submissions/', Submission);
    }
}
