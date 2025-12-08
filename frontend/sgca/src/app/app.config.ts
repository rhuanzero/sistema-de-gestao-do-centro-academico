import { ApplicationConfig, LOCALE_ID } from '@angular/core'; // Importe LOCALE_ID
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors, withFetch } from '@angular/common/http';
import { registerLocaleData } from '@angular/common'; // Importe isso
import localePt from '@angular/common/locales/pt';    // Importe o locale PT

import { routes } from './app.routes';
import { authInterceptor } from './core/auth.interceptor';
import { isPlatformBrowser } from '@angular/common'; // Se precisar para SSR

registerLocaleData(localePt);

// Mudei de 'class' para 'const'
export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideHttpClient(withFetch()), // O fetch ajuda muito na performance e SSR
    provideHttpClient(withInterceptors([authInterceptor])),
    provideHttpClient()
  ]
};