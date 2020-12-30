import FormList from './FormList';
import FormDetail from './FormDetail';

import {
  BrowserRouter as Router,
  Switch,
  Route,
  Link
} from "react-router-dom";


const App = () => {
  return (
    <Router>
      <div>
        <ul>
          <li>
            <Link to="/">Forms</Link>
          </li>
        </ul>

        <hr />

        <Switch>
          <Route exact path="/"> <FormList /> </Route>
          <Route path="/forms/:id">
            <FormDetail />
          </Route>
        </Switch>

      </div>
    </Router>
  );
};

export default App;
