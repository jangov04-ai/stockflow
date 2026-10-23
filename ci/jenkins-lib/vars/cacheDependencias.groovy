/**
 * Cache de dependencias entre builds y ramas.
 *
 * La clave de cada cache es el hash SHA-256 del fichero de dependencias:
 *   - Python: requirements*.txt  -> entorno virtual en $CI_CACHE/venv-<hash>
 *   - Node:   package-lock.json  -> node_modules en $CI_CACHE/node-<hash>
 *
 * Si la clave ya existe (nadie cambió las dependencias) se reutiliza con un
 * enlace simbólico y la instalación tarda ~0 s. Si cambia, se crea una entrada
 * nueva de forma atómica (directorio temporal + mv) para que dos builds en
 * paralelo no se pisen.
 *
 *   cacheDependencias.python('requirements-dev.txt')
 *   cacheDependencias.node()
 */

String raiz() {
    return env.CI_CACHE ?: '/var/jenkins_home/ci-cache'
}

def python(String requisitos = 'requirements-dev.txt') {
    String clave = sh(returnStdout: true,
                      script: "cat requirements*.txt | sha256sum | cut -c1-16").trim()
    String destino = "${raiz()}/venv-${clave}"
    sh """
        set -e
        mkdir -p '${raiz()}/pip'
        if [ -x '${destino}/bin/python' ]; then
            echo "CACHE HIT  python venv-${clave}"
        else
            echo "CACHE MISS python venv-${clave}: instalando dependencias"
            tmp=\$(mktemp -d '${raiz()}/tmp-venv-XXXX')
            python3 -m venv "\$tmp"
            "\$tmp/bin/pip" install --quiet --cache-dir '${raiz()}/pip' -r '${requisitos}'
            # Renombrado atómico: si otro build lo creó a la vez, nos quedamos con el suyo
            mv -T "\$tmp" '${destino}' 2>/dev/null || rm -rf "\$tmp"
        fi
        rm -rf .venv && ln -s '${destino}' .venv
    """
    return clave
}

def node() {
    String clave = sh(returnStdout: true,
                      script: "sha256sum package-lock.json | cut -c1-16").trim()
    String destino = "${raiz()}/node-${clave}"
    sh """
        set -e
        if [ -d '${destino}/node_modules' ]; then
            echo "CACHE HIT  node node-${clave}"
        else
            echo "CACHE MISS node node-${clave}: npm ci"
            rm -rf node_modules
            npm ci --no-audit --no-fund --cache '${raiz()}/npm'
            tmp=\$(mktemp -d '${raiz()}/tmp-node-XXXX')
            mv node_modules "\$tmp/"
            mv -T "\$tmp" '${destino}' 2>/dev/null || rm -rf "\$tmp"
        fi
        rm -rf node_modules && ln -s '${destino}/node_modules' node_modules
    """
    return clave
}

/** Borra entradas de cache sin usar en más de N días (mantenimiento). */
def limpiar(int dias = 7) {
    sh "find '${raiz()}' -maxdepth 1 \\( -name 'venv-*' -o -name 'node-*' \\) -mtime +${dias} -exec rm -rf {} + || true"
}
