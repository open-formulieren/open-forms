#!groovy

// Use "node {...}" to use any Jenkins server, or "node('master') {...}" to
// only run on the master node.
node {
    // You can hardcode the settings here, or have it dynamically figured out
    // in the build step.
    def djangoSettings = null
    def curDir = pwd()
    def envDir = "${curDir}/env"

    stage ("Build") {
        // Use the clean option that fits best in the project.
        // Clean build when changing target
        if (env.CHANGE_TARGET) {
            // Clean workspace
            // cleanWs()

            // Clean virtual environment
            dir("env") {
                deleteDir()
            }
        }
        // Clean build when the previous build failed.
        // cleanWs cleanWhenNotBuilt: false, cleanWhenSuccess: false, notFailBuild: true

        def installed = fileExists "${envDir}/bin/activate"

        checkout scm

        // Hard way of determining the Django settings path.
        if (!djangoSettings) {
            djangoSettings = sh(
                script: 'projectFolder=`cd src; ls -d */`; echo "${projectFolder%?}.conf.jenkins"',
                returnStdout: true
            )
        }

        if (!installed) {
            sh "virtualenv ${envDir} --no-site-packages -p python3"
        }
    }

    stage ("Install backend requirements") {
        sh """
            . ${envDir}/bin/activate
            pip install pip --upgrade
            pip install -r requirements/ci.txt
            deactivate
          """
    }

    stage ("Install frontend requirements") {
        sh """
            npm ci
            ./node_modules/gulp/bin/gulp.js build
           """

        withEnv(["SECRET_KEY=test_key"]) {
            sh """
                . ${envDir}/bin/activate
                python src/manage.py collectstatic \
                    --link \
                    --noinput \
                    --settings=${djangoSettings}
                deactivate
           """
        }
    }

    stage ("Test backend") {
        def testsError = null
        def keepDbOption = ""

        if (!env.CHANGE_TARGET) {
            keepDbOption = "--keepdb"
        }

        withEnv(["SECRET_KEY=test_key","ELASTIC_APM_DISABLE_SEND=true"]) {
            try {
                sh """
                    . ${envDir}/bin/activate
                    python src/manage.py jenkins \
                        --project-apps-tests \
                        --verbosity 2 \
                        --noinput \
                        --pep8-rcfile=.pep8 \
                        --coverage-rcfile=.coveragerc \
                        ${keepDbOption} \
                        --enable-coverage \
                        --settings=${djangoSettings}
                    deactivate
                """
            }
            catch(err) {
                testsError = err
                currentBuild.result = "FAILURE"
            }
            finally {
                dir("media") {
                    deleteDir()
                }
                junit "reports/junit.xml"

                if (testsError) {
                    throw testsError
                }
            }
        }

        withEnv(["SECRET_KEY=test_key"]) {
            try {
                sh "${envDir}/bin/isort --recursive --check-only --diff --quiet src > reports/isort.report"
            }
            catch(err) {
                // Nothing...
            }
        }
    }

    stage ("Test frontend") {
        def testsError = null

        try {
            sh "xvfb-run -a --server-args='-screen 0, 1920x1200x16' ./node_modules/gulp/bin/gulp.js test"
        }
        catch(err) {
            testsError = err
            currentBuild.result = "FAILURE"
        }
        finally {
            sh "./node_modules/gulp/bin/gulp.js lint"
            junit "reports/jstests/junit.xml"

            if (testsError) {
                throw testsError
            }
        }
    }

    stage ("Quality") {
        step(
            [
                $class: "CoberturaPublisher",
                coberturaReportFile: "reports/coverage.xml"
            ]
        )
        step(
            [
                $class: "WarningsPublisher",
                parserConfigurations: [
                    [
                        parserName: "PyLint",
                        pattern: "reports/pylint.report",
                        unstableTotalAll: "10",
                        usePreviousBuildAsReference: true,
                    ],
                    [
                        parserName: "Pep8",
                        pattern: "reports/pep8.report",
                        unstableTotalAll: "50",
                        usePreviousBuildAsReference: true,
                    ],
                    [
                        parserName: "Dynamic",
                        pattern: "reports/isort.report",
                        unstableTotalAll: "10",
                        usePreviousBuildAsReference: true,
                    ],
                ]
            ]
        )
    }

// Enable for SonarQube
//  stage("Analysis") {
//    def scannerHome = tool "SonarQube Scanner 2.8";
//    withSonarQubeEnv("Jenkins Scanner") {
//      sh "${scannerHome}/bin/sonar-scanner"
//    }
//  }
}
