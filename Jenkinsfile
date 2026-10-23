// =============================================================================
// StockFlow · Pipeline CI (Jenkins Multibranch)
//
// Estrategia de branching: GitFlow simplificado (ver ci/jenkins-lib/vars/ramaInfo.groovy)
//   feature/*          -> Build + Calidad + Tests unitarios/API            (rápido)
//   develop            -> + Tests E2E (Selenium) + SonarQube
//   main / release/*   -> + Empaquetado de la versión
//
// Optimizaciones aplicadas:
//   1. Ejecución paralela   -> Build, Calidad y Tests tienen sub-etapas en paralelo
//   2. Cache                -> venv y node_modules reutilizados por hash de dependencias
//   3. Ejecución selectiva  -> etapas según rama, cambios en ficheros y parámetros
//   4. Modular/reutilizable -> lógica en la Shared Library 'stockflow-ci-lib'
// =============================================================================

@Library('stockflow-ci-lib') _

def rama = null                        // resultado de ramaInfo()
def tests = 'sin resultados de tests'  // resumen para las notificaciones

pipeline {
    agent any

    options {
        timeout(time: 25, unit: 'MINUTES')
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '15'))
        disableConcurrentBuilds(abortPrevious: true)   // un push nuevo cancela el build viejo de la rama
        durabilityHint('PERFORMANCE_OPTIMIZED')         // menos escrituras a disco en cada paso
        skipStagesAfterUnstable()
    }

    parameters {
        booleanParam(name: 'FORZAR_E2E', defaultValue: false,
                     description: 'Ejecutar las pruebas Selenium aunque la rama no lo requiera')
        booleanParam(name: 'FORZAR_SONAR', defaultValue: false,
                     description: 'Ejecutar el análisis SonarQube aunque la rama no lo requiera')
    }

    environment {
        CI_CACHE      = '/var/jenkins_home/ci-cache'
        CHROME_BIN    = '/usr/bin/chromium'
        CHROMEDRIVER  = '/usr/bin/chromedriver'
        PIP_DISABLE_PIP_VERSION_CHECK = '1'
    }

    stages {
        stage('Preparación') {
            steps {
                script {
                    rama = ramaInfo()
                    echo """Rama: ${rama.rama} (tipo: ${rama.tipo})
                           |  E2E Selenium : ${rama.ejecutarE2E || params.FORZAR_E2E}
                           |  SonarQube    : ${rama.ejecutarSonar || params.FORZAR_SONAR}
                           |  Empaquetado  : ${rama.empaquetar}""".stripMargin()
                    githubStatus(estado: 'pending', descripcion: "Build #${env.BUILD_NUMBER} en curso")
                }
                sh 'rm -rf reports && mkdir -p reports'
            }
        }

        stage('Build') {
            parallel {
                stage('Backend (Python)') {
                    steps {
                        script { cacheDependencias.python('requirements-dev.txt') }
                        sh '''
                            .venv/bin/python -m compileall -q app
                            .venv/bin/python -c "from app import create_app; create_app('testing'); print('App Flask construida correctamente')"
                        '''
                    }
                }
                stage('Frontend (JS)') {
                    steps {
                        script { cacheDependencias.node() }
                        sh 'for f in app/static/js/*.js; do node --check "$f"; done && echo "JavaScript compila sin errores"'
                    }
                }
            }
        }

        stage('Calidad de código') {
            failFast true
            parallel {
                stage('flake8 (PEP 8)') {
                    steps {
                        sh '.venv/bin/flake8 app tests --tee --output-file=reports/flake8.txt'
                    }
                }
                stage('black (formato)') {
                    steps {
                        sh '.venv/bin/black --check --diff app tests'
                    }
                }
                stage('ESLint (JS)') {
                    steps {
                        sh '''
                            npx eslint app/static/js -f json -o reports/eslint.json || true
                            npx eslint app/static/js
                        '''
                    }
                }
                stage('bandit (seguridad)') {
                    steps {
                        sh '''
                            .venv/bin/bandit -q -c pyproject.toml -r app -f json -o reports/bandit.json || true
                            .venv/bin/bandit -q -c pyproject.toml -r app --severity-level medium
                        '''
                    }
                }
            }
        }

        stage('Tests') {
            parallel {
                stage('Unitarios + API') {
                    steps {
                        sh '''
                            .venv/bin/python -m pytest -m "not e2e" \
                              --junitxml=reports/junit-unit.xml \
                              --cov --cov-report=term --cov-report=xml:reports/coverage.xml
                        '''
                    }
                }
                stage('E2E (Selenium)') {
                    when {
                        anyOf {
                            expression { rama.ejecutarE2E }
                            expression { params.FORZAR_E2E }
                            changeset 'app/templates/**'
                            changeset 'app/static/**'
                        }
                    }
                    steps {
                        sh '.venv/bin/python -m pytest -m e2e -v --junitxml=reports/junit-e2e.xml'
                    }
                }
            }
        }

        stage('SonarQube') {
            when {
                anyOf {
                    expression { rama.ejecutarSonar }
                    expression { params.FORZAR_SONAR }
                }
            }
            steps {
                // SonarQube Community no analiza ramas: un proyecto por rama
                // (stockflow-main, stockflow-develop...) para que no se mezclen.
                withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
                    sh '''
                        RAMA_SONAR=$(echo "$BRANCH_NAME" | tr '/' '_')
                        .venv/bin/pysonar \
                          --sonar-host-url="$SONAR_HOST_URL" \
                          --sonar-token="$SONAR_TOKEN" \
                          --sonar-project-version="$BUILD_NUMBER" \
                          -Dsonar.projectKey="stockflow-$RAMA_SONAR" \
                          -Dsonar.projectName="StockFlow ($BRANCH_NAME)" \
                          -Dsonar.qualitygate.wait=true \
                          -Dsonar.qualitygate.timeout=300
                    '''
                }
            }
        }

        stage('Empaquetado') {
            when { expression { rama.empaquetar } }
            steps {
                sh '''
                    mkdir -p dist
                    VERSION="1.0.${BUILD_NUMBER}"
                    tar czf "dist/stockflow-${VERSION}.tar.gz" app run.py seed.py requirements.txt
                    echo "Paquete generado: dist/stockflow-${VERSION}.tar.gz"
                '''
                archiveArtifacts artifacts: 'dist/*.tar.gz', fingerprint: true
            }
        }
    }

    post {
        always {
            script { tests = resumenTests('reports/junit-*.xml') }
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
        }
        success {
            script {
                githubStatus(estado: 'success', descripcion: "Correcto · ${tests}")
                notificarCorreo(resultado: 'SUCCESS', tests: tests, tipo: rama?.tipo, etapas: etapasEjecutadas(rama))
            }
        }
        unstable {
            script {
                githubStatus(estado: 'failure', descripcion: "Inestable · ${tests}")
                notificarCorreo(resultado: 'UNSTABLE', tests: tests, tipo: rama?.tipo, etapas: etapasEjecutadas(rama))
            }
        }
        failure {
            script {
                githubStatus(estado: 'failure', descripcion: "Falló · ${tests}")
                notificarCorreo(resultado: 'FAILURE', tests: tests, tipo: rama?.tipo, etapas: etapasEjecutadas(rama))
            }
        }
        aborted {
            script { githubStatus(estado: 'error', descripcion: 'Build cancelado') }
        }
        cleanup {
            // Solo quita los enlaces a la cache; la cache se conserva para el siguiente build
            sh 'rm -f .venv node_modules'
        }
    }
}

String etapasEjecutadas(Map rama) {
    if (rama == null) {
        return 'el build falló antes de decidir las etapas'
    }
    List<String> etapas = ['Build', 'Calidad', 'Tests unitarios/API']
    if (rama.ejecutarE2E || params.FORZAR_E2E) { etapas << 'E2E Selenium' }
    if (rama.ejecutarSonar || params.FORZAR_SONAR) { etapas << 'SonarQube' }
    if (rama.empaquetar) { etapas << 'Empaquetado' }
    return etapas.join(' → ')
}
