import { Routes } from '@angular/router';
import { Home } from './pages/home/home'; // Verifique se o nome da classe é Home ou HomeComponent
import { Membros } from './pages/membros/membros';
import { Financeiro } from './pages/financeiro/financeiro';
import { Eventos } from './pages/eventos/eventos';
// Importe os outros se já tiver criado
// import { ComunicacaoComponent } from './pages/comunicacao/comunicacao.component';
// import { PatrimonioComponent } from './pages/patrimonio/patrimonio.component';

export const routes: Routes = [
  // Rota padrão: redireciona para o dashboard ao abrir o site
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  
  { path: 'dashboard', component: Home },
  { path: 'membros', component: Membros },
  { path: 'financeiro', component: Financeiro },
  { path: 'eventos', component: Eventos },
  
  // Exemplo para futuras rotas (descomente quando criar os componentes)
  // { path: 'comunicacao', component: ComunicacaoComponent },
  // { path: 'patrimonio', component: PatrimonioComponent },
];