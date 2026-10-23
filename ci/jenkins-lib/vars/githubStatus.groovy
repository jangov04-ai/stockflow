/**
 * Publica el estado del build en el commit de GitHub (el ✅/❌/🟡 junto al commit).
 *
 *   githubStatus(estado: 'pending' | 'success' | 'failure' | 'error',
 *                descripcion: 'texto corto', contexto: 'jenkins/stockflow')
 *
 * Requiere la credencial 'github-token' (usuario/token) con permiso
 * "Commit statuses: Read and write" sobre el repositorio.
 */
def call(Map args = [:]) {
    String estado = args.estado ?: 'pending'
    String contexto = args.contexto ?: 'jenkins/stockflow'
    String descripcion = (args.descripcion ?: "Build #${env.BUILD_NUMBER}: ${estado}").take(140)
    String sha = env.GIT_COMMIT
    String repo = repoDesdeUrl(env.GIT_URL)

    if (!sha || !repo) {
        echo "githubStatus: sin commit o repo (GIT_COMMIT=${sha}, GIT_URL=${env.GIT_URL}); se omite"
        return
    }

    String cuerpo = groovy.json.JsonOutput.toJson([
        state      : estado,
        context    : contexto,
        description: descripcion,
        target_url : env.BUILD_URL ?: '',
    ])
    writeFile file: '.github-status.json', text: cuerpo

    withCredentials([usernamePassword(credentialsId: 'github-token',
                                      usernameVariable: 'GH_USER',
                                      passwordVariable: 'GH_TOKEN')]) {
        String codigo = sh(
            returnStdout: true,
            script: """
                curl -s -o .github-status.out -w '%{http_code}' -X POST \\
                  -H "Authorization: Bearer \$GH_TOKEN" \\
                  -H 'Accept: application/vnd.github+json' \\
                  -H 'X-GitHub-Api-Version: 2022-11-28' \\
                  --data @.github-status.json \\
                  https://api.github.com/repos/${repo}/statuses/${sha}
            """
        ).trim()
        if (codigo == '201') {
            echo "GitHub: estado '${estado}' publicado en ${repo}@${sha.take(7)}"
        } else {
            // No rompemos el build por un fallo de notificación, pero lo dejamos visible.
            echo "GitHub: no se pudo publicar el estado (HTTP ${codigo}): " + readFile('.github-status.out')
        }
    }
    sh 'rm -f .github-status.json .github-status.out'
}

/** https://github.com/owner/repo.git  ->  owner/repo */
@NonCPS
static String repoDesdeUrl(String url) {
    def m = (url ?: '') =~ /github\.com[:\/]([^\/]+)\/(.+?)(\.git)?$/
    return m.find() ? "${m.group(1)}/${m.group(2)}" : null
}
