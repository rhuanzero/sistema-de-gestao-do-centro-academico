import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

export const authGuard: CanActivateFn = (route, state) => {
  const router = inject(Router);
  const platformId = inject(PLATFORM_ID);

  // Verifica se estamos no navegador (para evitar erro de SSR)
  if (isPlatformBrowser(platformId)) {
    const token = localStorage.getItem('token');
    
    if (token) {
      return true; // Tem token? Pode passar!
    }
  }

  // Não tem token? Manda pro login!
  router.navigate(['/login']);
  return false;
};