import { getRequestURL } from 'h3'

const isTraceEnabled = process.env.NITRO_AUTH_TRACE !== 'false'
const tracedPaths = new Set(['/', '/callback', '/auth/callback'])

export default defineNitroPlugin((nitroApp) => {
  if (!isTraceEnabled) {
    return
  }

  nitroApp.hooks.hook('request', (event) => {
    const url = getRequestURL(event)
    if (!tracedPaths.has(url.pathname)) {
      return
    }

    const hasInternalJwtCookie = (event.node.req.headers.cookie || '').includes('internal_jwt=')
    const returnTo = url.searchParams.get('return_to') || '-'

    console.info(
      `[auth-flow][request] ${event.node.req.method} ${url.pathname} return_to=${returnTo} internal_jwt_cookie=${hasInternalJwtCookie}`
    )
  })

  nitroApp.hooks.hook('afterResponse', (event) => {
    const url = getRequestURL(event)
    if (!tracedPaths.has(url.pathname)) {
      return
    }

    console.info(
      `[auth-flow][response] ${event.node.req.method} ${url.pathname} status=${event.node.res.statusCode}`
    )
  })
})
