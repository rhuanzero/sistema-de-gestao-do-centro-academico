import { Component, OnInit, signal } from '@angular/core'; // 👈 1. Importe signal
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ApiService } from '../../services/apiservice';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './home.html',
  styleUrls: ['./home.css']
})
export class Home implements OnInit {
  
  // 👇 2. Define a variável como um Signal
  usuarioNome = signal('Carregando...');

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.carregarDadosUsuario();
  }

  carregarDadosUsuario() {
    console.log('🚀 Iniciando busca de usuário...');
    
    this.apiService.getUser().subscribe({
      next: (user: any) => {
        console.log('✅ Usuário chegou:', user);
        
        if (user && user.nome) {
          // 👇 3. Atualiza o valor do Signal (Instantâneo)
          this.usuarioNome.set(user.nome);
        }
      },
      error: (e) => {
        console.error('❌ Erro ao buscar usuário:', e);
        this.usuarioNome.set('Visitante');
      }
    });
  }
}