import { Routes } from '@angular/router';
import { Home } from './pages/home/home'; // Verifique se o nome da classe é Home ou HomeComponent
import { Membros } from './pages/membros/membros';
import { Financeiro } from './pages/financeiro/financeiro';
import { Eventos } from './pages/eventos/eventos';
// Importe os outros se já tiver criado
import { Comunicacao } from './pages/comunicacao/comunicacao';
import { PatrimonioComponent } from './pages/patrimonio/patrimonio';
import { Login } from './pages/login/login';
import { Layout } from './layout/layout';

import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    component: Login
  },
  
  {
    path: '',
    component: Layout,
    canActivate: [authGuard], // O Pai é o Layout
    children: [

      { path: '', redirectTo: 'home', pathMatch: 'full' },

     { 
        path: 'home', 
        loadComponent: () => import('./pages/home/home').then(m => m.Home)
      },
      { path: 'membros', component: Membros },
      { path: 'financeiro', component: Financeiro },
      { path: 'eventos', component: Eventos },
  
  // Exemplo para futuras rotas (descomente quando criar os componentes)
      { path: 'comunicacao', component: Comunicacao },
      { path: 'patrimonio', component: PatrimonioComponent },
    ],
  },

];