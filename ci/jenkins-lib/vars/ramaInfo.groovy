/**
 * Estrategia de branching (GitFlow simplificado) y qué ejecuta cada rama.
 *
 *   main       -> producción: todo + análisis Sonar + empaquetado de la release
 *   develop    -> integración: todo + análisis Sonar (sin empaquetar)
 *   release/*  -> igual que main (estabilización antes de publicar)
 *   hotfix/*   -> igual que main
 *   feature/*  -> ciclo rápido: build, linters y tests unitarios/API
 *
 * Uso: ramaInfo().tipo, ramaInfo().ejecutarSonar, ...
 */
def call(String rama = env.BRANCH_NAME ?: 'main') {
    String tipo
    if (rama == 'main' || rama == 'master') {
        tipo = 'produccion'
    } else if (rama == 'develop') {
        tipo = 'integracion'
    } else if (rama.startsWith('release/') || rama.startsWith('hotfix/')) {
        tipo = 'release'
    } else {
        tipo = 'feature'
    }

    boolean completa = tipo != 'feature'
    return [
        rama          : rama,
        tipo          : tipo,
        ejecutarE2E   : completa,
        ejecutarSonar : completa,
        empaquetar    : tipo == 'produccion' || tipo == 'release',
    ]
}
