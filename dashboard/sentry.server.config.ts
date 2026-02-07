// This file configures the initialization of Sentry on the server.
// The config you add here will be used whenever the server handles a request.
// https://docs.sentry.io/platforms/javascript/guides/nextjs/

import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: "https://91f46bfc53dfd998841ac58e990a3875@o4510760542470144.ingest.us.sentry.io/4510760587755520",

  // Sample 10% of traces in production to reduce costs and improve performance
  tracesSampleRate: 0.1,

  // Disable logs in production to reduce noise
  enableLogs: false,

  // Disable sending user PII (Personally Identifiable Information) for HIPAA compliance
  // https://docs.sentry.io/platforms/javascript/guides/nextjs/configuration/options/#sendDefaultPii
  sendDefaultPii: false,
});
