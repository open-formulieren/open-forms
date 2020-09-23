//jshint ignore:start
import {TOGGLES} from './constants';

if (TOGGLES.length) {
    import(/* webpackChunkName: 'toggle' */ './toggle');
}
