import { Routes } from '@angular/router';
import { Home } from './pages/home/home'; // Verifique se o nome da classe é Home ou HomeComponent
import { Membros } from './pages/membros/membros';
import { Financeiro } from './pages/financeiro/financeiro';
import { Eventos } from './pages/eventos/eventos';
// Importe os outros se já tiver criado
import { Comunicacao } from './pages/comunicacao/comunicacao';
import { Patrimonio } from './pages/patrimonio/patrimonio';
import { Login } from './pages/login/login';
import { Layout } from './layout/layout';


export const routes: Routes = [
  // Rota padrão: redireciona para o dashboard ao abrir o site
  { path: '', redirectTo: 'login', pathMatch: 'full' },

  { path: 'login', component: Login },
  
  {
    path: '',
    component: Layout, // O Pai é o Layout
    children: [
      { path: 'dashboard', component: Home },
      { path: 'membros', component: Membros },
      { path: 'financeiro', component: Financeiro },
      { path: 'eventos', component: Eventos },
  
  // Exemplo para futuras rotas (descomente quando criar os componentes)
      { path: 'comunicacao', component: Comunicacao },
      { path: 'patrimonio', component: Patrimonio },
    ],
  },

];