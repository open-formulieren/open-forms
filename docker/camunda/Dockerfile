ARG BASE_VERSION
FROM camunda/camunda-bpm-platform:${BASE_VERSION}

# This webapp includes a default admin:admin sample user
# RUN rm -rf /camunda/webapps/camunda-invoice

# Enable Auth on the REST API
COPY web.xml /camunda/webapps/engine-rest/WEB-INF/web.xml
