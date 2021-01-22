import React from 'react';

import Container from '@material-ui/core/Container';
import Typography from '@material-ui/core/Typography';
import Box from '@material-ui/core/Box';
import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import IconButton from '@material-ui/core/IconButton';
import MenuIcon from '@material-ui/icons/Menu';
import Link from '@material-ui/core/Link';
import { makeStyles } from '@material-ui/core/styles';

import {
  BrowserRouter as Router,
  Switch,
  Route,
  Link as RouterLink
} from 'react-router-dom';

import FormList from './FormList';
import FormDetail from './FormDetail';
import FormStep from './FormStep';
import FormCompletion from './FormCompletion';

const basename = process.env.REACT_APP_BASENAME || '/';

const useStyles = makeStyles((theme) => ({
  navLink: {
    marginRight: theme.spacing(1),
  }
}));


const App = () => {
  const classes = useStyles();
  return (
    <Router basename={basename}>
      <Container maxWidth="xl">

        <AppBar position="static">
          <Toolbar>
            <IconButton edge="start" color="inherit" aria-label="menu">
              <MenuIcon />
            </IconButton>

            <Link
              to="/"
              color="inherit"
              variant="h5"
              className={classes.navLink}
              component={RouterLink}>Forms</Link>

            <Link
              to="/submissions"
              color="inherit"
              variant="h5"
              className={classes.navLink}
              component={RouterLink}>My submissions</Link>

          </Toolbar>
        </AppBar>

        <Box my={4}>
          <Typography variant="h4" component="h1" gutterBottom>
            Open Forms demo
          </Typography>
        </Box>

        <Switch>
          <Route exact path="/" component={FormList} />
          <Route path="/forms/:id/start" component={FormDetail} />
          <Route path="/submissions/:submissionId/steps/:stepId" component={FormStep} />
          <Route path="/submissions/:submissionId/complete" component={FormCompletion} />
        </Switch>

      </Container>
    </Router>
  );
};

export default App;
