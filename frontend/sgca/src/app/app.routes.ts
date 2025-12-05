import { Routes } from '@angular/router';
import { Home } from './home/home'; // ⚠️ Verifique se o caminho do arquivo está correto aqui!

export const routes: Routes = [
  {
    path: '',       // Caminho vazio = Raiz do site (http://localhost:4200/)
    component: Home // Carrega o seu componente Home
  },
  // Aqui você pode adicionar outras rotas depois, ex:
  // { path: 'financeiro', component: FinanceiroComponent },
];