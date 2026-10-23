/**
 * Publica los informes JUnit indicados y devuelve un texto resumen.
 *
 *   String r = resumenTests('reports/junit-*.xml')
 */
def call(String patron = 'reports/junit-*.xml') {
    def t = junit(allowEmptyResults: true, testResults: patron)
    if (t == null || t.totalCount == 0) {
        return 'sin resultados de tests'
    }
    return "${t.passCount} pasaron, ${t.failCount} fallaron, ${t.skipCount} omitidos (total ${t.totalCount})"
}
