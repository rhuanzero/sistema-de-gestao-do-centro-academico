import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withFetch } from '@angular/common/http'; 

import { routes } from './app.routes';

// Mudei de 'class' para 'const'
export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideHttpClient(withFetch()) // O fetch ajuda muito na performance e SSR
  ]
};