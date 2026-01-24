const { defineConfig } = require('cypress')
const fs = require('fs')
const path = require('path')

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:5001',
    supportFile: 'cypress/support/e2e.js',
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
    viewportWidth: 1280,
    viewportHeight: 720,
    video: false,
    screenshotOnRunFailure: true,
    screenshotsFolder: 'cypress/screenshots',
    defaultCommandTimeout: 10000,
    requestTimeout: 10000,
    responseTimeout: 30000,
    setupNodeEvents(on, config) {
      on('before:browser:launch', (browser, launchOptions) => {
        if (browser.family === 'chromium') {
          launchOptions.args.push('--no-sandbox')
          launchOptions.args.push('--disable-setuid-sandbox')
          launchOptions.args.push('--disable-dev-shm-usage')
          launchOptions.args.push('--disable-gpu')
        }
        return launchOptions
      })

      // Custom task to copy SOP screenshots to static folder
      on('task', {
        copySopScreenshot({ source, destination }) {
          const destDir = path.dirname(destination)
          if (!fs.existsSync(destDir)) {
            fs.mkdirSync(destDir, { recursive: true })
          }
          if (fs.existsSync(source)) {
            fs.copyFileSync(source, destination)
            return destination
          }
          return null
        }
      })

      // After screenshot, copy SOP screenshots to static folder
      on('after:screenshot', (details) => {
        if (details.path.includes('static/images/sop')) {
          const filename = path.basename(details.path)
          const destPath = path.join('static', 'images', 'sop', filename)
          const destDir = path.dirname(destPath)

          if (!fs.existsSync(destDir)) {
            fs.mkdirSync(destDir, { recursive: true })
          }

          fs.copyFileSync(details.path, destPath)
          console.log(`Copied screenshot to: ${destPath}`)
        }
        return details
      })

      return config
    },
  },
})
