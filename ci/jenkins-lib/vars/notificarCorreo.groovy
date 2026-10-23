/**
 * Envía un correo HTML con el resultado del build usando la plantilla
 * resources/stockflow/correo.html de esta librería.
 *
 *   notificarCorreo(resultado: 'SUCCESS', tests: resumenTests, rama: 'develop')
 */
def call(Map args = [:]) {
    String destino = args.para ?: env.NOTIFY_EMAIL
    if (!destino) {
        echo 'notificarCorreo: NOTIFY_EMAIL no definido; se omite'
        return
    }
    String resultado = args.resultado ?: currentBuild.currentResult
    boolean ok = resultado == 'SUCCESS'
    String icono = ok ? '✅' : (resultado == 'UNSTABLE' ? '⚠️' : '❌')
    String color = ok ? '#2e7d32' : (resultado == 'UNSTABLE' ? '#ef6c00' : '#c62828')

    String commit = sh(returnStdout: true,
                       script: 'git log -1 --pretty=format:"%h - %an: %s" 2>/dev/null || echo "-"').trim()

    Map valores = [
        ICONO    : icono,
        COLOR    : color,
        RESULTADO: resultado,
        JOB      : env.JOB_NAME,
        BUILD    : env.BUILD_NUMBER,
        RAMA     : args.rama ?: env.BRANCH_NAME ?: '-',
        TIPO     : args.tipo ?: '-',
        COMMIT   : commit,
        TESTS    : args.tests ?: 'sin resultados de tests',
        ETAPAS   : args.etapas ?: '-',
        DURACION : currentBuild.durationString.replace(' and counting', ''),
        URL      : env.BUILD_URL ?: '',
    ]
    String html = libraryResource('stockflow/correo.html')
    valores.each { k, v -> html = html.replace("{{${k}}}", v.toString()) }

    mail(to: destino,
         subject: "${icono} StockFlow [${valores.RAMA}] #${env.BUILD_NUMBER} - ${resultado}",
         mimeType: 'text/html',
         charset: 'UTF-8',
         body: html)
    echo "Correo enviado a ${destino} (${resultado})"
}
