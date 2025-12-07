import { HttpInterceptorFn } from '@angular/common/http';
import { inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  // 1. Injeta o identificador da plataforma (Navegador ou Servidor)
  const platformId = inject(PLATFORM_ID);
  
  // 2. Verifica: "Estou no navegador?"
  if (isPlatformBrowser(platformId)) {
    
    // Se estiver no navegador, pode usar localStorage sem medo
    const token = localStorage.getItem('token');

    if (token) {
      const cloned = req.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`
        }
      });
      return next(cloned);
    }
  }

  // 3. Se estiver no servidor (SSR) ou não tiver token, manda a requisição original
  return next(req);
};