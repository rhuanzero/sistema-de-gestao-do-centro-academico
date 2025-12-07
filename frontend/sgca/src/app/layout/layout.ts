import { Component, OnInit } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router'; // Imports de rota
import { ApiService } from '../services/apiservice';

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive], // <--- Verifique se RouterOutlet está aqui
  templateUrl: './layout.html',
  styleUrl: './layout.css'
})
export class Layout implements OnInit {
  
  nomeUsuario: string = 'Carregando...';

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.apiService.getMe().subscribe({
      next: (user) => {
        this.nomeUsuario = user.nome;
      },
      error: (e) => {
        console.error('Erro ao pegar usuário:', e);
        this.nomeUsuario = 'Visitante';
      }
    });
  }
}